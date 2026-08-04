import json

import pytest

from log_server import ingest_execution as ingest

# Minimal but structurally faithful fixtures, modeled directly on a real captured
# execution (see ROADMAP.md's log_server entry) -- one agent with a chat model
# feeding it, plus one non-agent (Docs Writer-style) node with no chat model.
FAKE_WORKFLOW = {
    "nodes": [
        {"name": "Head Planner", "type": "@n8n/n8n-nodes-langchain.agent"},
        {"name": "OpenAI Chat Model - Head Planner", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi"},
        {"name": "Docs Writer - Create a document", "type": "n8n-nodes-base.googleDocs"},
        {"name": "When clicking 'Execute workflow'", "type": "n8n-nodes-base.manualTrigger"},
    ],
    "connections": {
        "OpenAI Chat Model - Head Planner": {
            "ai_languageModel": [[{"node": "Head Planner", "type": "ai_languageModel", "index": 0}]]
        }
    },
}


def _chat_model_run(prompt_tokens: int, completion_tokens: int, start_time: int, exec_time: int):
    return {
        "startTime": start_time,
        "executionTime": exec_time,
        "executionStatus": "success",
        "data": {
            "ai_languageModel": [
                [{"json": {"tokenUsageEstimate": {
                    "promptTokens": prompt_tokens, "completionTokens": completion_tokens,
                }}}]
            ]
        },
    }


def _agent_run(start_time: int, exec_time: int, status: str = "success"):
    return {
        "startTime": start_time,
        "executionTime": exec_time,
        "executionStatus": status,
        "data": {"main": [[{"json": {}}]]},
    }


def make_execution(finished: bool = True, head_planner_status: str = "success") -> dict:
    return {
        "id": "99",
        "finished": finished,
        "data": {
            "resultData": {
                "runData": {
                    "Head Planner": [_agent_run(1785781331546, 26750, head_planner_status)],
                    "OpenAI Chat Model - Head Planner": [
                        _chat_model_run(82, 61, 1785781331550, 26745)
                    ],
                    "Docs Writer - Create a document": [_agent_run(1785781400000, 1742)],
                }
            }
        },
    }


@pytest.fixture
def workflow_path(tmp_path):
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(FAKE_WORKFLOW))
    return path


def test_load_chat_model_map(workflow_path):
    mapping = ingest.load_chat_model_map(workflow_path)
    assert mapping == {"OpenAI Chat Model - Head Planner": "Head Planner"}


def test_load_chat_model_map_missing_file(tmp_path):
    with pytest.raises(ingest.ExecutionIngestionError, match="not found"):
        ingest.load_chat_model_map(tmp_path / "missing.json")


def test_load_loggable_node_names(workflow_path):
    names = ingest.load_loggable_node_names(workflow_path)
    assert names == ["Head Planner", "Docs Writer - Create a document"]


def test_sum_token_usage_sums_across_multiple_runs():
    runs = [
        _chat_model_run(100, 20, 1, 10),
        _chat_model_run(200, 30, 2, 10),
    ]
    prompt_tokens, completion_tokens = ingest.sum_token_usage(runs)
    assert prompt_tokens == 300
    assert completion_tokens == 50


def test_sum_token_usage_handles_no_usage_data():
    runs = [_agent_run(1, 10)]
    assert ingest.sum_token_usage(runs) == (0, 0)


def test_build_run_log_rows_produces_expected_rows(workflow_path):
    rows = ingest.build_run_log_rows(make_execution(), workflow_path)

    assert len(rows) == 2
    head_planner_row = next(r for r in rows if r["agent"] == "Head Planner")
    assert head_planner_row["run_id"] == "99"
    assert head_planner_row["implementation"] == "n8n"
    assert head_planner_row["tokens_in"] == 82
    assert head_planner_row["tokens_out"] == 61
    assert head_planner_row["latency_ms"] == 26750
    assert head_planner_row["run_status"] == "success"
    assert head_planner_row["cost_usd"] > 0

    docs_writer_row = next(r for r in rows if r["agent"] == "Docs Writer - Create a document")
    assert docs_writer_row["tokens_in"] == 0
    assert docs_writer_row["tokens_out"] == 0
    assert docs_writer_row["cost_usd"] == 0


def test_build_run_log_rows_marks_error_status(workflow_path):
    rows = ingest.build_run_log_rows(make_execution(head_planner_status="error"), workflow_path)
    head_planner_row = next(r for r in rows if r["agent"] == "Head Planner")
    assert head_planner_row["run_status"] == "error"


def test_build_run_log_rows_rejects_unfinished_execution(workflow_path):
    with pytest.raises(ingest.ExecutionIngestionError, match="not finished"):
        ingest.build_run_log_rows(make_execution(finished=False), workflow_path)


def test_build_run_log_rows_skips_nodes_with_no_run_data(workflow_path):
    execution = make_execution()
    del execution["data"]["resultData"]["runData"]["Docs Writer - Create a document"]
    rows = ingest.build_run_log_rows(execution, workflow_path)
    assert len(rows) == 1
    assert rows[0]["agent"] == "Head Planner"


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


def test_fetch_execution_calls_correct_url_and_headers(monkeypatch):
    captured = {}

    def fake_get(url, headers, params, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        return FakeResponse(200, {"id": "42", "finished": True})

    monkeypatch.setattr(ingest.requests, "get", fake_get)
    result = ingest.fetch_execution("42", "http://localhost:5678", "fake-key")

    assert result == {"id": "42", "finished": True}
    assert captured["url"] == "http://localhost:5678/api/v1/executions/42"
    assert captured["headers"] == {"X-N8N-API-KEY": "fake-key"}
    assert captured["params"] == {"includeData": "true"}


def test_fetch_latest_execution_id_returns_most_recent(monkeypatch):
    def fake_get(url, headers, params, timeout):
        return FakeResponse(200, {"data": [{"id": "7"}]})

    monkeypatch.setattr(ingest.requests, "get", fake_get)
    assert ingest.fetch_latest_execution_id("http://localhost:5678", "fake-key") == "7"


def test_fetch_latest_execution_id_raises_when_no_executions(monkeypatch):
    def fake_get(url, headers, params, timeout):
        return FakeResponse(200, {"data": []})

    monkeypatch.setattr(ingest.requests, "get", fake_get)
    with pytest.raises(ingest.ExecutionIngestionError, match="no executions"):
        ingest.fetch_latest_execution_id("http://localhost:5678", "fake-key")
