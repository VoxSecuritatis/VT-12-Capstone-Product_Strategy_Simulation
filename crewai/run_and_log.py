# ================================================================
# CrewAI Run + Run-Log Emission
# ================================================================
# Objective:
#       Run this project's crew against a real brief and, unlike n8n,
#       capture real per-agent token/latency/status data directly
#       in-process (CrewAI exposes it on the live Agent/Task objects
#       after kickoff -- no post-hoc REST call needed), then append one
#       shared-schema row per agent to comparison/run_logs/run_logs.jsonl.
# Inputs:
#       - brief: optional CLI arg; defaults to the fixed test brief
#         already used throughout Phase 2/3 for an apples-to-apples
#         comparison with n8n
# Outputs:
#       - one run-log row per agent, appended via
#         log_server.run_log.append_run_log_row
# Notes:
#   - Also replaces run_crew_plain.py (a throwaway diagnostic script)
#     as the standard way to run this crew: `crewai run`'s own Textual
#     TUI dashboard can't be captured from a non-interactive process,
#     so this drives the Crew object directly via CrewAI's own Python
#     API instead, which prints plain, readable verbose output.
#   - gpt-5 pricing ($0.63/M input, $5.00/M output) matches
#     comparison/log_server/src/log_server/ingest_execution.py's
#     constants -- reused here, not re-derived, for consistency.
#   - Assumes each agent owns exactly one task (true for this project's
#     current four-agent, four-task design) -- would need revisiting if
#     an agent is ever assigned more than one task.
# ================================================================

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

CREWAI_ROOT = Path(__file__).resolve().parent
FIXED_TEST_BRIEF = (
    "A new budget noise-cancelling headphone for commuters. Who's the target "
    "customer and who are the main competitors?"
)

GPT5_INPUT_COST_PER_MILLION = 0.63
GPT5_OUTPUT_COST_PER_MILLION = 5.00


def build_run_log_rows(crew: Any) -> list[dict[str, Any]]:
    """Turn one completed crew's real per-agent data into shared-schema run-log rows."""
    run_id = str(crew.id)
    tasks_by_agent_role = {task.agent.role: task for task in crew.tasks if task.agent}

    rows: list[dict[str, Any]] = []
    for agent in crew.agents:
        task = tasks_by_agent_role.get(agent.role)
        if task is None or task.output is None:
            continue

        usage = agent.llm.get_token_usage_summary()
        tokens_in = usage.prompt_tokens
        tokens_out = usage.completion_tokens
        cost_usd = (
            tokens_in / 1_000_000 * GPT5_INPUT_COST_PER_MILLION
            + tokens_out / 1_000_000 * GPT5_OUTPUT_COST_PER_MILLION
        )

        latency_ms = 0.0
        if task.start_time and task.end_time:
            latency_ms = (task.end_time - task.start_time).total_seconds() * 1000

        # Task.start_time/end_time are naive local-clock datetimes (crewai's own
        # task.py calls bare datetime.datetime.now()) -- convert to UTC-aware so
        # this matches n8n's rows for cross-implementation comparison.
        if task.end_time:
            end_time = task.end_time.astimezone(timezone.utc)
        else:
            end_time = datetime.now(timezone.utc)
        timestamp = end_time.isoformat()
        run_status = "success" if task.output.raw.strip() else "error"

        rows.append(
            {
                "run_id": run_id,
                "implementation": "crewai",
                "agent": agent.role,
                "timestamp": timestamp,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": round(cost_usd, 6),
                "latency_ms": round(latency_ms, 3),
                "run_status": run_status,
            }
        )

    return rows


def main() -> None:
    """Run the crew against the fixed test brief and log one row per agent."""
    load_dotenv(CREWAI_ROOT / ".env")

    from crewai.project.crew_loader import load_crew
    from log_server.run_log import append_run_log_row, validate_run_log_row

    brief = sys.argv[1] if len(sys.argv) > 1 else FIXED_TEST_BRIEF
    crew, _ = load_crew(CREWAI_ROOT / "crew.jsonc")
    result = crew.kickoff(inputs={"brief": brief})

    print("\n===== FINAL RESULT =====")
    print(result.raw)

    rows = build_run_log_rows(crew)
    for row in rows:
        append_run_log_row(validate_run_log_row(row))

    print(f"\n[INFO] logged crew run {crew.id}: {len(rows)} rows appended")
    for row in rows:
        print(
            f"[INFO]   {row['agent']}: tokens_in={row['tokens_in']} "
            f"tokens_out={row['tokens_out']} cost_usd={row['cost_usd']} "
            f"latency_ms={row['latency_ms']} run_status={row['run_status']}"
        )


if __name__ == "__main__":
    main()
