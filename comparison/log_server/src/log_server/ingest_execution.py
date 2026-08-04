# ================================================================
# Post-Hoc n8n Execution Ingestion
# ================================================================
# Objective:
#       n8n's AI Agent node does not propagate token usage to its own
#       output (n8n-io/n8n#26302), so real per-agent cost/latency data
#       can't be read from inside the workflow via an expression. This
#       module fetches a completed execution's full detail from n8n's own
#       REST API (which does contain real per-node token usage and
#       timing) and turns it into shared-schema run-log rows.
# Inputs:
#       - an n8n execution ID (CLI arg; defaults to the most recent
#         execution if omitted)
#       - N8N_API_KEY (.env, required)
#       - the exported workflow JSON (n8n/VT Capstone GTM Planner.json),
#         used to map each Chat Model sub-node to the agent node it
#         belongs to, so token usage is attributed correctly
# Outputs:
#       - one run-log row appended per loggable node (the four AI Agent
#         nodes plus the two Docs Writer nodes) via run_log.append_run_log_row
# Notes:
#   - Deliberately post-hoc, not real-time: see ROADMAP.md's "Known
#     Platform Limitations & Blockers" section for the full rationale.
#   - gpt-5 pricing ($0.63/M input, $5.00/M output) confirmed in
#     ROADMAP.md's Open Questions section (2026-08-03) -- hardcoded here
#     as named constants rather than re-deriving per run.
# ================================================================

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from log_server.run_log import append_run_log_row, validate_run_log_row

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
WORKFLOW_JSON_PATH = PROJECT_ROOT / "n8n" / "VT Capstone GTM Planner.json"

LOGGABLE_NODE_TYPES = {"@n8n/n8n-nodes-langchain.agent", "n8n-nodes-base.googleDocs"}

GPT5_INPUT_COST_PER_MILLION = 0.63
GPT5_OUTPUT_COST_PER_MILLION = 5.00


class ExecutionIngestionError(RuntimeError):
    """Raised when a completed execution can't be fetched or parsed."""


def load_chat_model_map(workflow_path: Path) -> dict[str, str]:
    """Return a map of chat-model node name -> the agent node name it feeds."""
    if not workflow_path.exists():
        raise ExecutionIngestionError(f"exported workflow JSON not found: {workflow_path}")

    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    chat_model_to_agent: dict[str, str] = {}

    for source_node, outputs in workflow.get("connections", {}).items():
        for target in outputs.get("ai_languageModel", [[]])[0]:
            chat_model_to_agent[source_node] = target["node"]

    return chat_model_to_agent


def load_loggable_node_names(workflow_path: Path) -> list[str]:
    """Return the ordered list of node names this project logs rows for."""
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    return [node["name"] for node in workflow["nodes"] if node["type"] in LOGGABLE_NODE_TYPES]


def fetch_execution(execution_id: str, base_url: str, api_key: str) -> dict[str, Any]:
    """Fetch one completed execution's full detail from n8n's REST API."""
    response = requests.get(
        f"{base_url}/api/v1/executions/{execution_id}",
        headers={"X-N8N-API-KEY": api_key},
        params={"includeData": "true"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_latest_execution_id(base_url: str, api_key: str) -> str:
    """Return the most recent execution's ID."""
    response = requests.get(
        f"{base_url}/api/v1/executions",
        headers={"X-N8N-API-KEY": api_key},
        params={"limit": 1},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    if not data:
        raise ExecutionIngestionError("no executions found via the n8n API")
    return str(data[0]["id"])


def sum_token_usage(node_runs: list[dict[str, Any]]) -> tuple[int, int]:
    """Return (prompt_tokens, completion_tokens) summed across a chat model's runs."""
    prompt_tokens = 0
    completion_tokens = 0
    for run in node_runs:
        for output_list in run.get("data", {}).values():
            for batch in output_list:
                for item in batch:
                    usage = item.get("json", {}).get("tokenUsageEstimate")
                    if usage:
                        prompt_tokens += usage.get("promptTokens", 0)
                        completion_tokens += usage.get("completionTokens", 0)
    return prompt_tokens, completion_tokens


def build_run_log_rows(execution: dict[str, Any], workflow_path: Path) -> list[dict[str, Any]]:
    """Turn one execution's real per-node data into shared-schema run-log rows."""
    if not execution.get("finished"):
        raise ExecutionIngestionError(f"execution {execution.get('id')} has not finished yet")

    run_data = execution["data"]["resultData"]["runData"]
    chat_model_map = load_chat_model_map(workflow_path)
    agent_to_chat_model = {agent: model for model, agent in chat_model_map.items()}
    loggable_names = load_loggable_node_names(workflow_path)

    rows: list[dict[str, Any]] = []
    for node_name in loggable_names:
        node_runs = run_data.get(node_name)
        if not node_runs:
            continue

        chat_model_name = agent_to_chat_model.get(node_name)
        prompt_tokens, completion_tokens = (
            sum_token_usage(run_data[chat_model_name]) if chat_model_name in run_data else (0, 0)
        )

        latency_ms = sum(run.get("executionTime", 0) for run in node_runs)
        run_status = (
            "success"
            if all(run.get("executionStatus") == "success" for run in node_runs)
            else "error"
        )
        start_time_ms = node_runs[0]["startTime"]
        timestamp = datetime.fromtimestamp(start_time_ms / 1000, tz=timezone.utc).isoformat()
        cost_usd = (
            prompt_tokens / 1_000_000 * GPT5_INPUT_COST_PER_MILLION
            + completion_tokens / 1_000_000 * GPT5_OUTPUT_COST_PER_MILLION
        )

        rows.append(
            {
                "run_id": str(execution["id"]),
                "implementation": "n8n",
                "agent": node_name,
                "timestamp": timestamp,
                "tokens_in": prompt_tokens,
                "tokens_out": completion_tokens,
                "cost_usd": round(cost_usd, 6),
                "latency_ms": latency_ms,
                "run_status": run_status,
            }
        )

    return rows


def main() -> None:
    """Ingest one n8n execution's real per-node data into the shared run-log file."""
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("N8N_API_KEY")
    if not api_key:
        raise ExecutionIngestionError("N8N_API_KEY is not set in .env")

    base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
    execution_id = sys.argv[1] if len(sys.argv) > 1 else fetch_latest_execution_id(base_url, api_key)

    execution = fetch_execution(execution_id, base_url, api_key)
    rows = build_run_log_rows(execution, WORKFLOW_JSON_PATH)

    for row in rows:
        append_run_log_row(validate_run_log_row(row))

    print(f"[INFO] ingested execution {execution_id}: {len(rows)} rows appended")
    for row in rows:
        print(
            f"[INFO]   {row['agent']}: tokens_in={row['tokens_in']} "
            f"tokens_out={row['tokens_out']} cost_usd={row['cost_usd']} "
            f"latency_ms={row['latency_ms']} run_status={row['run_status']}"
        )


if __name__ == "__main__":
    main()
