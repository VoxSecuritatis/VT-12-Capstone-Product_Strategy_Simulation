# ================================================================
# Run-Log Row Validation and Append
# ================================================================
# Objective:
#       Validate one run-log row against the shared schema and append it
#       as a single JSON line to comparison/run_logs/run_logs.jsonl, so
#       n8n (and later CrewAI) can both write to the same file without
#       either implementation needing to know about the other's writes.
# Inputs:
#       - row: a dict decoded from one POST body, expected to already
#         carry all nine shared-schema fields
# Outputs:
#       - one line appended to run_logs.jsonl per valid call
# Notes:
#   - This file I/O lives here, not in n8n: n8n's Code node sandboxes fs
#     and cannot safely write local files itself (same rationale as
#     mcp-server/tools/cache.py -- see CVE-2026-1470 / CVE-2026-0863,
#     the sandbox-escape surface routing around it would touch).
#   - RUN_LOG_PATH resolves four parents up from this module, out of the
#     log_server uv project entirely, because run_logs.jsonl is shared
#     with the future CrewAI implementation and must live at
#     comparison/run_logs/, a sibling of log_server/, not inside it.
# ================================================================

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

RUN_LOG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "run_logs" / "run_logs.jsonl"

# Guards concurrent appends to the shared JSONL file. POSTs normally arrive
# one at a time (n8n runs its agent chain sequentially), but this keeps
# concurrent writers from interleaving partial lines if that ever changes.
WRITE_LOCK = threading.Lock()

REQUIRED_STRING_FIELDS = ("run_id", "implementation", "agent", "timestamp", "run_status")
REQUIRED_NUMERIC_FIELDS: dict[str, type] = {
    "tokens_in": int,
    "tokens_out": int,
    "cost_usd": float,
    "latency_ms": float,
}


class InvalidRunLogRow(ValueError):
    """Raised when a POSTed run-log row fails schema validation."""


def validate_run_log_row(data: Any) -> dict[str, Any]:
    """Validate data against the shared run-log schema and return a normalized row."""
    if not isinstance(data, dict):
        raise InvalidRunLogRow("request body must be a JSON object")

    errors: list[str] = []
    row: dict[str, Any] = {}

    for field in REQUIRED_STRING_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required and must be a non-empty string")
        else:
            row[field] = value

    for field, caster in REQUIRED_NUMERIC_FIELDS.items():
        value = data.get(field)
        try:
            row[field] = caster(value)
        except (TypeError, ValueError):
            errors.append(f"{field} is required and must be numeric")
            continue
        if row[field] < 0:
            errors.append(f"{field} must be >= 0")

    if "timestamp" in row:
        try:
            datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("timestamp must be an ISO-8601 string")

    if errors:
        raise InvalidRunLogRow("; ".join(errors))

    return row


def append_run_log_row(row: dict[str, Any]) -> None:
    """Append one validated run-log row as a JSON line to run_logs.jsonl."""
    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row)
    with WRITE_LOCK, RUN_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
