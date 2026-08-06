# ================================================================
# n8n vs. CrewAI Comparison Report
# ================================================================
# Objective:
#       Read the shared run-log schema both implementations write to and
#       compute cost, latency, and reliability stats per Phase 5 of
#       ROADMAP.md, writing a plain markdown report -- no notebook, no
#       new dependencies (stdlib only, matching this project's existing
#       log_server/mcp-server convention of avoiding third-party web/data
#       frameworks wherever the standard library is sufficient).
# Inputs:
#       - comparison/run_logs/run_logs.jsonl (shared schema: run_id,
#         implementation, agent, timestamp, tokens_in, tokens_out,
#         cost_usd, latency_ms, run_status)
# Outputs:
#       - comparison/report.md
# Notes:
#   - "Latency per run" is the sum of each run's per-agent/node
#     latency_ms values. The schema has no separate run-level
#     start/end timestamp, and every workflow in this project executes
#     its agents/nodes sequentially, so the sum is a reasonable proxy
#     for total wall-clock time -- not a literal measured run duration.
#   - "Reliability" is reported at two granularities: run-level (did
#     every row in a run report run_status="success") and row-level
#     (what fraction of individual agent/node rows succeeded). As of
#     this run, real logged data shows 100% success at both
#     granularities for both implementations -- real tool-level
#     failures were observed and recovered from during testing (see
#     ROADMAP.md), but none were severe enough to mark an agent/node
#     row as run_status="error".
# ================================================================

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RUN_LOG_PATH = Path(__file__).resolve().parent / "run_logs" / "run_logs.jsonl"
REPORT_PATH = Path(__file__).resolve().parent / "report.md"


@dataclass
class Run:
    """One complete run (all agent/node rows sharing an implementation + run_id)."""

    implementation: str
    run_id: str
    rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_cost_usd(self) -> float:
        """Sum of every row's cost_usd for this run."""
        return sum(row["cost_usd"] for row in self.rows)

    @property
    def total_latency_ms(self) -> float:
        """Sum of every row's latency_ms for this run (see module Notes)."""
        return sum(row["latency_ms"] for row in self.rows)

    @property
    def all_succeeded(self) -> bool:
        """Whether every row in this run reported run_status == 'success'."""
        return all(row["run_status"] == "success" for row in self.rows)


@dataclass
class ImplementationStats:
    """Aggregate cost/latency/reliability stats for one implementation."""

    implementation: str
    runs: list[Run]

    @property
    def run_count(self) -> int:
        return len(self.runs)

    @property
    def row_count(self) -> int:
        return sum(len(run.rows) for run in self.runs)

    @property
    def costs(self) -> list[float]:
        return [run.total_cost_usd for run in self.runs]

    @property
    def latencies_ms(self) -> list[float]:
        return [run.total_latency_ms for run in self.runs]

    @property
    def run_success_rate(self) -> float:
        """Fraction of runs where every row succeeded."""
        if not self.runs:
            return 0.0
        return sum(1 for run in self.runs if run.all_succeeded) / len(self.runs)

    @property
    def row_success_rate(self) -> float:
        """Fraction of individual agent/node rows that succeeded."""
        rows = [row for run in self.runs for row in run.rows]
        if not rows:
            return 0.0
        return sum(1 for row in rows if row["run_status"] == "success") / len(rows)


# ------------------------------------------------
# Data loading
# ------------------------------------------------


def load_runs(path: Path) -> dict[str, list[Run]]:
    """Load run_logs.jsonl and group rows into Runs by implementation."""
    rows_by_key: dict[tuple[str, str], Run] = {}

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = (row["implementation"], row["run_id"])
            if key not in rows_by_key:
                rows_by_key[key] = Run(implementation=row["implementation"], run_id=row["run_id"])
            rows_by_key[key].rows.append(row)

    runs_by_implementation: dict[str, list[Run]] = {}
    for run in rows_by_key.values():
        runs_by_implementation.setdefault(run.implementation, []).append(run)

    return runs_by_implementation


# ------------------------------------------------
# Report generation
# ------------------------------------------------


def format_currency(value: float) -> str:
    """Format a dollar amount per this project's markdown standard: $ and commas."""
    return f"${value:,.4f}"


def format_latency(ms: float) -> str:
    """Format a latency in milliseconds as minutes:seconds, matching prior reporting style."""
    seconds = ms / 1000
    minutes, remaining_seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {remaining_seconds:04.1f}s ({ms:,.0f} ms)"


def format_percent(fraction: float) -> str:
    """Format a 0-1 fraction as a percentage with one decimal place."""
    return f"{fraction * 100:.1f}%"


def build_summary_table(stats_by_impl: dict[str, ImplementationStats]) -> str:
    """Build the top-level cost/latency/reliability summary table."""
    lines = [
        "| Implementation | Runs | Avg Cost | Min Cost | Max Cost | Avg Latency | Run Success Rate | Row Success Rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    best_avg_cost = min(statistics.mean(s.costs) for s in stats_by_impl.values())
    best_avg_latency = min(statistics.mean(s.latencies_ms) for s in stats_by_impl.values())
    for name, stats in stats_by_impl.items():
        avg_cost = statistics.mean(stats.costs)
        min_cost = min(stats.costs)
        max_cost = max(stats.costs)
        avg_latency = statistics.mean(stats.latencies_ms)

        avg_cost_cell = format_currency(avg_cost)
        if avg_cost == best_avg_cost:
            avg_cost_cell = f"**{avg_cost_cell}**"

        avg_latency_cell = format_latency(avg_latency)
        if avg_latency == best_avg_latency:
            avg_latency_cell = f"**{avg_latency_cell}**"

        lines.append(
            f"| {name} | {stats.run_count} | {avg_cost_cell} | {format_currency(min_cost)} | "
            f"{format_currency(max_cost)} | {avg_latency_cell} | "
            f"{format_percent(stats.run_success_rate)} | {format_percent(stats.row_success_rate)} |"
        )
    return "\n".join(lines)


def build_per_run_table(stats_by_impl: dict[str, ImplementationStats]) -> str:
    """Build a detailed per-run breakdown table, sorted by implementation then run_id."""
    lines = [
        "| Implementation | Run ID | Agent/Node Rows | Cost | Latency | All Succeeded |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name, stats in stats_by_impl.items():
        for run in sorted(stats.runs, key=lambda r: r.run_id):
            succeeded_cell = "Yes" if run.all_succeeded else "**No**"
            lines.append(
                f"| {name} | `{run.run_id}` | {len(run.rows)} | {format_currency(run.total_cost_usd)} | "
                f"{format_latency(run.total_latency_ms)} | {succeeded_cell} |"
            )
    return "\n".join(lines)


def build_report(stats_by_impl: dict[str, ImplementationStats]) -> str:
    """Assemble the full markdown report."""
    total_runs = sum(s.run_count for s in stats_by_impl.values())
    total_rows = sum(s.row_count for s in stats_by_impl.values())

    sections = [
        "# **n8n vs. CrewAI Comparison Report**",
        "",
        "Generated by `comparison/compare.py` from `comparison/run_logs/run_logs.jsonl` -- real cost, "
        "latency, and reliability data captured across both implementations' Phase 2/3 build-out runs "
        f"and Phase 4 testing (scenario briefs, reproducibility reruns). {total_runs} total runs, "
        f"{total_rows} total agent/node rows.",
        "",
        "## Summary",
        "",
        build_summary_table(stats_by_impl),
        "",
        "## Per-Run Detail",
        "",
        build_per_run_table(stats_by_impl),
        "",
        "## Notes",
        "",
        "- \"Avg Latency\" is the mean of each run's summed per-agent/node latency_ms -- a proxy for "
        "total wall-clock time (both workflows execute their agents/nodes sequentially), not a "
        "separately measured run duration; the schema has no run-level start/end timestamp.",
        "- \"Run Success Rate\" is the fraction of runs where every agent/node row reported "
        "run_status=\"success\". \"Row Success Rate\" is the same check at individual row "
        "granularity. Both are 100% for both implementations in the currently logged data -- real "
        "tool-level failures (a SerpAPI timeout, several `robots.txt` blocks) were observed and "
        "recovered from during testing, but none were severe enough to mark an agent/node row as "
        "failed. See `ROADMAP.md` Phase 2-4 for the qualitative resilience evidence this quantitative "
        "data doesn't capture on its own.",
        "- Costs and token counts are real, captured either in-process (CrewAI, via "
        "`agent.llm.get_token_usage_summary()`) or post-hoc via n8n's REST API "
        "(`log_server`'s `ingest_execution.py`) -- see `ROADMAP.md` for the full design rationale.",
    ]
    return "\n".join(sections) + "\n"


# ------------------------------------------------
# Entry point
# ------------------------------------------------


def main() -> None:
    """Load run_logs.jsonl, compute stats, and write comparison/report.md."""
    if not RUN_LOG_PATH.exists():
        raise FileNotFoundError(f"run log not found: {RUN_LOG_PATH}")

    runs_by_implementation = load_runs(RUN_LOG_PATH)
    if not runs_by_implementation:
        raise ValueError(f"no rows found in {RUN_LOG_PATH}")

    stats_by_impl = {
        name: ImplementationStats(implementation=name, runs=runs)
        for name, runs in sorted(runs_by_implementation.items())
    }

    report = build_report(stats_by_impl)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"[INFO] wrote {REPORT_PATH}")
    for name, stats in stats_by_impl.items():
        print(
            f"[INFO]   {name}: {stats.run_count} runs, avg cost "
            f"{format_currency(statistics.mean(stats.costs))}, "
            f"run success rate {format_percent(stats.run_success_rate)}"
        )


if __name__ == "__main__":
    main()
