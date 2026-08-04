import json

import pytest

from log_server import run_log as run_log_module
from log_server.run_log import InvalidRunLogRow, append_run_log_row, validate_run_log_row

VALID_ROW = {
    "run_id": "run-123",
    "implementation": "n8n",
    "agent": "Research Agent",
    "timestamp": "2026-08-03T14:00:00-04:00",
    "tokens_in": "1200",
    "tokens_out": 340,
    "cost_usd": 0.05,
    "latency_ms": "8210",
    "run_status": "success",
}


def test_validate_run_log_row_accepts_valid_row():
    row = validate_run_log_row(VALID_ROW)
    assert row["run_id"] == "run-123"
    assert row["tokens_in"] == 1200
    assert row["latency_ms"] == 8210.0


def test_validate_run_log_row_rejects_non_dict():
    with pytest.raises(InvalidRunLogRow, match="JSON object"):
        validate_run_log_row(["not", "a", "dict"])


@pytest.mark.parametrize(
    "missing_field",
    ["run_id", "implementation", "agent", "timestamp", "run_status", "tokens_in", "cost_usd"],
)
def test_validate_run_log_row_rejects_missing_field(missing_field):
    data = {k: v for k, v in VALID_ROW.items() if k != missing_field}
    with pytest.raises(InvalidRunLogRow, match=missing_field):
        validate_run_log_row(data)


def test_validate_run_log_row_rejects_non_numeric_tokens():
    data = {**VALID_ROW, "tokens_in": "not-a-number"}
    with pytest.raises(InvalidRunLogRow, match="tokens_in"):
        validate_run_log_row(data)


def test_validate_run_log_row_rejects_negative_cost():
    data = {**VALID_ROW, "cost_usd": -1.0}
    with pytest.raises(InvalidRunLogRow, match="cost_usd"):
        validate_run_log_row(data)


def test_validate_run_log_row_rejects_malformed_timestamp():
    data = {**VALID_ROW, "timestamp": "not-a-timestamp"}
    with pytest.raises(InvalidRunLogRow, match="timestamp"):
        validate_run_log_row(data)


def test_append_run_log_row_creates_parent_directory():
    assert not run_log_module.RUN_LOG_PATH.parent.exists()
    append_run_log_row(validate_run_log_row(VALID_ROW))
    assert run_log_module.RUN_LOG_PATH.parent.exists()


def test_append_run_log_row_writes_one_line_per_call_in_order():
    first = validate_run_log_row(VALID_ROW)
    second = validate_run_log_row({**VALID_ROW, "agent": "Analyst Agent"})

    append_run_log_row(first)
    append_run_log_row(second)

    lines = run_log_module.RUN_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["agent"] == "Research Agent"
    assert json.loads(lines[1])["agent"] == "Analyst Agent"
