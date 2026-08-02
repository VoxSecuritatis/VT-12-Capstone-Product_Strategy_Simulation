# Multi-Agent Market Research & GTM Planning (n8n, MCP, CrewAI)

*Virginia Tech Applied Agentic AI Post-Graduate Program — Capstone Project (Product Strategy Simulation)*

> **Status:** 🚧 Phase 0 (Environment & Access Setup) and Phase 1 (MCP Server) complete. Phase 2 (n8n workflow) is next. This README is the north-star spec; see `ROADMAP.md` (local only — not published to GitHub) for the build sequence.
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
| Cost efficiency | Cloud/API spend per run within budget cap — proposed **$1.00 per end-to-end run, per implementation** (gpt-5 token costs + SerpAPI free tier); see Open Questions in `ROADMAP.md` (local only) — cap needs re-checking against gpt-5 pricing (was set based on a cheaper mini-tier model) |

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
- Logging, retries, and cost/latency tracking are cross-cutting concerns in both implementations.

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

## Repository structure (planned)

```
.
├── documentation/          # Problem statement, source rubric docs (this is the north star)
├── mcp-server/             # Shared MCP server: research tools used by both n8n and CrewAI
├── n8n/                    # Exported n8n workflow JSON + setup notes (no Python here)
├── crewai/                 # CrewAI project (uv structure, `crewai create crew` scaffold)
│   ├── src/.../            # crew.py, agents.yaml, tasks.yaml, main.py, tools/
│   └── tests/              # pytest, mocked LLM responses
├── comparison/
│   ├── compare.py          # reads run_logs/, computes cost/latency/reliability stats
│   ├── report.md           # generated comparison writeup (output of compare.py)
│   └── run_logs/           # raw JSONL/CSV from both implementations, shared schema
├── outputs/                # Sample Google Doc exports, evidence JSON, generated tables
├── screenshots/            # Build-walkthrough screenshots for the reflections doc, named <Phase>-<NN>-name.jpg
└── tests/                  # Unit tests (mocked tools), scenario tests (fixed briefs)
```

*(`screenshots/` and `mcp-server/` exist already; the rest is not yet created — scaffolding happens per `ROADMAP.md`, local only.)*

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

See Open Questions in `ROADMAP.md` (local only) — two remain unconfirmed: MCP server choice, and the proposed budget cap number.

## Deliverables

- [ ] Exported n8n workflow JSON file
- [ ] CrewAI project files (uv structure)
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
| Source volatility | Cache results, store page snapshots, include timestamps |
| API rate limits | Exponential backoff, batching, multiple keys (if permitted) |
| Hallucinations | Mandate evidence IDs per fact; flag uncited claims |
| Formatting drift | Stable Google Docs templates + post-write validation |
| Cost overruns | Token limits, early summarization, budget caps |

## Documentation

Full rubric and grading criteria: `documentation/1762856365_capstoneprojectproblemstatement.md` (local only — `documentation/` is git-ignored, not published to GitHub)
Assignment brief: `documentation/Multi- Agent Market Research and GTM Planning (n8n, MCP, and CrewAI).md` (local only)

