import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compare import ImplementationStats, Run, load_runs  # noqa: E402


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def make_row(run_id: str, implementation: str, cost: float, latency: float, status: str) -> dict:
    return {
        "run_id": run_id,
        "implementation": implementation,
        "agent": "Test Agent",
        "timestamp": "2026-08-06T00:00:00+00:00",
        "tokens_in": 100,
        "tokens_out": 50,
        "cost_usd": cost,
        "latency_ms": latency,
        "run_status": status,
    }


def test_run_totals_sum_across_rows():
    run = Run(implementation="n8n", run_id="1")
    run.rows = [
        make_row("1", "n8n", 0.10, 1000.0, "success"),
        make_row("1", "n8n", 0.20, 2000.0, "success"),
    ]
    assert run.total_cost_usd == pytest.approx(0.30)
    assert run.total_latency_ms == pytest.approx(3000.0)
    assert run.all_succeeded is True


def test_run_all_succeeded_false_on_any_error():
    run = Run(implementation="n8n", run_id="1")
    run.rows = [
        make_row("1", "n8n", 0.10, 1000.0, "success"),
        make_row("1", "n8n", 0.20, 2000.0, "error"),
    ]
    assert run.all_succeeded is False


def test_implementation_stats_success_rates():
    run_ok = Run(implementation="crewai", run_id="a")
    run_ok.rows = [make_row("a", "crewai", 0.10, 1000.0, "success")]

    run_fail = Run(implementation="crewai", run_id="b")
    run_fail.rows = [
        make_row("b", "crewai", 0.10, 1000.0, "success"),
        make_row("b", "crewai", 0.10, 1000.0, "error"),
    ]

    stats = ImplementationStats(implementation="crewai", runs=[run_ok, run_fail])
    assert stats.run_count == 2
    assert stats.row_count == 3
    assert stats.run_success_rate == 0.5
    assert stats.row_success_rate == 2 / 3


def test_load_runs_groups_by_implementation_and_run_id(tmp_path):
    path = tmp_path / "run_logs.jsonl"
    write_jsonl(
        path,
        [
            make_row("1", "n8n", 0.05, 500.0, "success"),
            make_row("1", "n8n", 0.05, 500.0, "success"),
            make_row("x", "crewai", 0.10, 1000.0, "success"),
        ],
    )

    grouped = load_runs(path)

    assert set(grouped.keys()) == {"n8n", "crewai"}
    assert len(grouped["n8n"]) == 1
    assert len(grouped["n8n"][0].rows) == 2
    assert len(grouped["crewai"]) == 1
    assert len(grouped["crewai"][0].rows) == 1


def test_load_runs_skips_blank_lines(tmp_path):
    path = tmp_path / "run_logs.jsonl"
    path.write_text(
        json.dumps(make_row("1", "n8n", 0.05, 500.0, "success")) + "\n\n\n",
        encoding="utf-8",
    )

    grouped = load_runs(path)

    assert len(grouped["n8n"]) == 1
