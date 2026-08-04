# Multi-Agent Market Research & GTM Planning (n8n, MCP, CrewAI)

*Virginia Tech Applied Agentic AI Post-Graduate Program — Capstone Project (Product Strategy Simulation)*

> **Status:** 🚧 Phase 0 (Environment & Access Setup), Phase 1 (MCP Server), and Phase 2.1 (n8n <-> MCP wiring, confirmed end-to-end) complete. The full n8n agent chain — Head Planner, Research Agent, Analyst Agent, Strategy Agent, and Docs Writer — is built, chained, and confirmed working end-to-end in a single full-workflow run (~166,564 tokens, 3m 5s), producing a real, readable Google Doc GTM plan and meeting the <15-minute exit criterion, including recovery from a real fetch failure mid-run. Remaining Phase 2 work: per-node logging/retries tracking and emitting run-log rows, before moving to Phase 3 (CrewAI). This README is the north-star spec; see `ROADMAP.md` (local only — not published to GitHub) for the build sequence.
>
> **Repo:** [VoxSecuritatis/VT-12-Capstone-Product_Strategy_Simulation](https://github.com/VoxSecuritatis/VT-12-Capstone-Product_Strategy_Simulation)

## Overview

This capstone project designs and implements a **multi-agent workflow** that automates market research and go-to-market (GTM) planning. The same agent design is built **twice** — once in **n8n** and once in **CrewAI** — so the two implementations can be compared on cost, latency, and reliability.

Four agents, shared across both implementations:

| Agent | Role |
|---|---|
| **Head Planner** | Orchestrator and documenter |
| **Research Agent** | Finder — desk research, sourcing |
| **Analyst Agent** | Sense-maker — competitor analysis, synthesis |
| **Strategy Agent** | Planner — drafts the GTM plan |

The workflow orchestrates desk research → competitor analysis → GTM plan drafting → export to Google Docs.

## Why this project (Situation)

Product teams spend days manually collecting sources, analyzing competitors, and drafting GTM documents. That process is:

- **Slow** — delays responsiveness to market shifts
- **Error-prone** — manual effort misses insights
- **Inconsistent** — not reproducible across research cycles

## Success Criteria — North Star KPIs

Every design and implementation decision in this repo is measured against these. Source of truth: `documentation/1762856365_capstoneprojectproblemstatement.md`.

| KPI | Target |
|---|---|
| Coverage | ≥90% of research questions answered with linked sources |
| Source quality | ≥80% citations from top-tier/primary sources; 0% broken links |
| Latency | <15 minutes from project brief to drafted GTM document |
| Strategy quality | Human rubric score ≥4/5 (clarity, feasibility, differentiation) |
| Reproducibility | ≥80% consistent facts across multiple runs |
| Cost efficiency | Cloud/API spend per run within budget cap — **$0.50 per end-to-end run, per implementation** (tightened from an original $1.00 proposal once real data existed); **confirmed with real data**: a full n8n chain run cost **$0.1104** total (**22.1%** of the cap), a full CrewAI crew run cost **$0.3767** total (**75.3%** of the cap) — both pass, with a meaningfully different margin; see Open Questions in `ROADMAP.md` (local only). **Known n8n platform limitation affecting real-time measurement of this KPI:** n8n's AI Agent node does not expose per-agent token usage to downstream nodes ([n8n-io/n8n#26302](https://github.com/n8n-io/n8n/issues/26302)), solved instead with a post-hoc ingestion script — see `ROADMAP.md`'s "Known Platform Limitations & Blockers" section for the full explanation and references. |

## Architecture

Both implementations wire the same four agents to a shared tool layer:

```
Trigger → Head Planner → Research Agent → Analyst Agent → Strategy Agent → Docs Writer
                              │                │
                         MCP tools         SerpAPI (search)
```

- **MCP server** exposes research tools (search, fetch/snapshot, citation tracking) consumed by both n8n and CrewAI.
- **SerpAPI** supplies web search results to the Research Agent.
- **Docs Writer** exports the final GTM plan to Google Docs (PDF export optional).
- **Logging, retries, and cost/latency tracking** are cross-cutting concerns in both implementations -- `log_server` (below) is the shared persistence mechanism both write to.

### MCP server: why we built one, and what it does

The assignment requires starting an MCP server and connecting both implementations to it, but doesn't require writing one from scratch. Rather than build blind (first time working with MCP) or gamble on an unverified off-the-shelf bundle, we adapted the official reference `fetch` server from `modelcontextprotocol/servers` and extended it -- the lowest-cost path that still teaches real MCP mechanics through a working example.

**What it accomplishes:**
- **`search`** -- queries SerpAPI and returns cited results (title, link, snippet, citation ID) for the Research Agent.
- **`fetch`** -- fetches a URL, respects `robots.txt`, converts the page to markdown, and returns a cited, timestamped snapshot.
- **Citation/caching layer** -- every `search` and `fetch` result is written to a local, timestamped, citation-ID-keyed snapshot, so repeated lookups within a freshness window reuse the snapshot instead of re-fetching (the source-volatility mitigation from the Risks table below). This file I/O lives in the MCP server because n8n can't own it directly (its Code node sandboxes `fs`, and Write to File needs binary input, not text).
- **Real MCP protocol over SSE** -- not a generic REST wrapper. n8n's native MCP Client Tool node and CrewAI's `MCPServerAdapter` both connect to the same running server over SSE, exactly matching the shared-tool-layer architecture diagrammed above.

**Steps taken:**
1. Scaffolded `mcp-server/` as its own `uv` project (consistent with the CrewAI project's planned uv structure).
2. Added the reference `fetch` server's own dependencies (`mcp`, `markdownify`, `protego`, `readabilipy`, `pydantic`, `requests`) rather than reinventing HTML-to-markdown conversion or robots.txt parsing.
3. Wrote the custom `search` tool and the citation/caching layer alongside the adapted `fetch` tool, all served from one `MCPServer` instance over SSE (`mcp_server.run(transport="sse")`).
4. Added a `pytest` suite (mocked HTTP responses, no live network needed) covering the cache, search, and fetch logic.
5. Smoke-tested every tool for real: ran the server, then used `curl` to drive the full MCP protocol by hand (`initialize` handshake, `tools/list`, `tools/call` for both tools) and confirmed cited, timestamped results came back correctly, including a cache hit on a repeated `fetch`.

See `SETUP.md` for the exact commands (run, curl smoke-test sequence) and a note on a Node.js-related extraction-quality tradeoff inside the `fetch` tool.

### log_server: why we built one, and what it does

The rubric explicitly requires "logging, retries, and cost/latency tracking" plus a documented n8n-vs-CrewAI comparison -- both need real per-run data persisted somewhere Phase 5's `compare.py` can read. n8n can't write that data itself: its Code node sandboxes `fs`, and two 2026 CVEs (CVE-2026-1470, CVE-2026-0863) in n8n's sandbox-escape surface, specifically around Code-node file/code execution, make routing around that sandbox the wrong move rather than just an inconvenience. Same problem shape as the MCP server above, same solution: a small standalone Python process n8n talks to instead of trying to own the file I/O itself.

**What it accomplishes:**
- **`POST /log`** -- validates one JSON row against the shared run-log schema (`run_id, implementation, agent, timestamp, tokens_in, tokens_out, cost_usd, latency_ms, run_status`) and appends it as one line to `comparison/run_logs/run_logs.jsonl`.
- **Shared, not n8n-only** -- the same file and schema the future CrewAI implementation will also write to, so Phase 5's `compare.py` reads both without special-casing either.
- **Zero new dependencies** -- built on Python's standard library `http.server` only; no framework needed for one endpoint that validates and appends a line to a file.

**Steps taken:**
1. Scaffolded `comparison/log_server/` as its own `uv` project, matching `mcp-server/`'s structure exactly.
2. Wrote schema validation (`run_log.py`) and the HTTP handler (`server.py`) separately, so validation logic is testable without a real server.
3. Added a `pytest` suite (18 tests) -- schema-validation edge cases plus a real `ThreadingHTTPServer` instance driven over a real local socket in tests, no mocking needed for either.
4. Started the server for real and confirmed it live with an actual `POST` (`HTTP 201`), then deleted that one test row so the log file starts empty for real data -- see `ROADMAP.md`'s Lessons Learned for why the startup log line alone wasn't a reliable enough signal on its own.

**Real per-agent cost/latency data, not real-time from n8n:** n8n's AI Agent node doesn't expose token usage to downstream nodes ([n8n-io/n8n#26302](https://github.com/n8n-io/n8n/issues/26302)), so an in-workflow HTTP Request node can't log it directly. `ingest_execution.py` (a second entry point in the same project) solves this by calling n8n's own REST API after a run completes -- which does have the real data -- and cross-referencing it against the exported workflow JSON to attribute each Chat Model's token usage to the right agent. Confirmed against a real full-chain execution: **$0.1104 total cost**, with real `tokens_in`/`tokens_out`/`latency_ms` per agent. See `ROADMAP.md`'s "Known Platform Limitations & Blockers" for the full rationale and `SETUP.md` for run commands.

## Repository structure (planned)

```
.
├── documentation/          # Problem statement, source rubric docs (this is the north star)
├── mcp-server/             # Shared MCP server: research tools used by both n8n and CrewAI
├── n8n/                    # Exported n8n workflow: VT Capstone GTM Planner.json + setup notes (no Python here)
├── crewai/                 # CrewAI project: JSON-first scaffold (crewai create crew), built and proven
│   ├── agents/*.jsonc      # Head Planner, Research, Analyst, Strategy agent definitions
│   ├── crew.jsonc          # crew config + task definitions (sequential process)
│   └── tools/              # custom tools: serpapi_search.py, mcp_fetch.py
├── comparison/
│   ├── compare.py          # reads run_logs/, computes cost/latency/reliability stats (not yet built)
│   ├── report.md           # generated comparison writeup (output of compare.py, not yet built)
│   ├── log_server/         # uv project: POST /log HTTP endpoint, appends run-log rows (built, tested)
│   └── run_logs/           # run_logs.jsonl from both implementations, shared schema (git-ignored)
├── outputs/                # Sample Google Doc exports, evidence JSON, generated tables
├── screenshots/            # Build-walkthrough screenshots for the reflections doc, named <Phase>-<NN>-name.jpg
└── tests/                  # Unit tests (mocked tools), scenario tests (fixed briefs)
```

*(`screenshots/`, `mcp-server/`, `n8n/`, `crewai/`, and `comparison/log_server/` (with real `run_logs/` data from
both implementations) all exist already; `comparison/compare.py`/`report.md` and the top-level `tests/` are not yet
created — remaining work tracked in `ROADMAP.md`, local only.)*

**Python approach:** fully modular `.py` throughout. The CrewAI project follows CrewAI's own uv scaffold, the MCP server is a plain long-running Python process, and even the n8n-vs-CrewAI comparison (`comparison/compare.py`) is a script rather than a notebook, so every part of the system is pytest-testable and reproducible with a single command. Both implementations write run-log rows to a shared schema (`run_id, implementation, agent, timestamp, tokens_in, tokens_out, cost_usd, latency_ms, run_status`) in `comparison/run_logs/`, so `compare.py` can read both without special-casing either implementation.

## Prerequisites

- **Dev environment:** WSL2, Ubuntu 24.04.4 LTS (local, no separate VM)
- **n8n:** v2.27.4, run locally in WSL
- Python 3.11+ and `uv`
- An MCP server for research tools — adapting an existing/reference implementation rather than building one from scratch (first time working with MCP servers)
- SerpAPI key — obtained (free tier, 250 lookups/month), in `.env`
- Google account for Docs export: a personal Google account, OAuth user-consent flow (both n8n and CrewAI run locally, so no service account needed) — Google Cloud project created, Docs + Drive APIs enabled, OAuth consent screen and Client ID configured; Client ID/Secret in `.env`. Account details kept out of documentation.
- **LLM provider:** OpenAI `gpt-5` as the default model for both implementations. Anthropic Claude (e.g. Haiku 4.5) is an optional later comparison once the baseline works, not required for the MVP.

See `SETUP.md` for the full as-verified toolchain: exact versions, install locations, and the install/version/test command for each (Python, `uv`, `nvm`, Node.js, npm, n8n), plus the WSL networking fixes that were needed to get reliable internet access working.

See Open Questions in `ROADMAP.md` (local only) for full decision history — all resolved as of this writing.

## Deliverables

- [x] Exported n8n workflow JSON file
- [x] CrewAI project files (uv structure)
- [ ] Sample Google Doc output of a GTM plan
- [ ] CrewAI chatbot screenshots (CLI-based demo, e.g. `crewai chat`)
- [ ] Documentation (README) covering architecture, setup, testing notes, and n8n-vs-CrewAI comparison

## Testing strategy

- **Unit tests** — mock inputs/outputs for tools (SerpAPI, MCP, Docs)
- **Scenario tests** — fixed project briefs with golden expected outputs
- **Human review** — strategy quality scored against the rubric (clarity, feasibility, differentiation)
- **Comparison** — cost, latency, and reliability measured across both implementations

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Source volatility | Cache results, store page snapshots, include timestamps. **Encountered live** (robots.txt/403 blocks during fetch) and mitigated with a fetch-failure fallback, proven working twice in real runs — see `ROADMAP.md`'s "Known Platform Limitations & Blockers" section for the full incident history and residual risk. |
| API rate limits | Exponential backoff, batching, multiple keys (if permitted) |
| Hallucinations | Mandate evidence IDs per fact; flag uncited claims |
| Formatting drift | Stable Google Docs templates + post-write validation |
| Cost overruns | Token limits, early summarization, budget caps |

## Documentation

Full rubric and grading criteria: `documentation/1762856365_capstoneprojectproblemstatement.md` (local only — `documentation/` is git-ignored, not published to GitHub)
Assignment brief: `documentation/Multi- Agent Market Research and GTM Planning (n8n, MCP, and CrewAI).md` (local only)

