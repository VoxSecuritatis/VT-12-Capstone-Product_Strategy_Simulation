# Multi-Agent Market Research & GTM Planning (n8n, MCP, CrewAI)

*Virginia Tech Applied Agentic AI Post-Graduate Program — Capstone Project (Product Strategy Simulation)*

> **Status:** 🚧 Planning stage — environment not yet provisioned, no code written. This README is the north-star spec; see [ROADMAP.md](ROADMAP.md) for the build sequence.
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
| Cost efficiency | Cloud/API spend per run within budget cap — proposed **$1.00 per end-to-end run, per implementation** (gpt-4o-mini token costs + SerpAPI free tier); see [Open Questions](ROADMAP.md#open-questions) |

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

## Repository structure (planned)

```
.
├── documentation/          # Problem statement, source rubric docs (this is the north star)
├── mcp-server/             # Shared MCP server: research tools used by both n8n and CrewAI
├── n8n/                    # Exported n8n workflow JSON + setup notes
├── crewai/                 # CrewAI project (uv structure): agents, tasks, flows, tools
├── outputs/                # Sample Google Doc exports, evidence JSON, generated tables
├── tests/                  # Unit tests (mocked tools), scenario tests (fixed briefs)
└── comparison/             # n8n vs CrewAI cost/latency/reliability results
```

*(Not yet created — scaffolding happens per [ROADMAP.md](ROADMAP.md).)*

## Prerequisites

- **Dev environment:** WSL2, Ubuntu 24.04.4 LTS (local, no separate VM)
- **n8n:** v2.27.4, run locally in WSL
- Python 3.11+ and `uv`
- An MCP server for research tools — adapting an existing/reference implementation rather than building one from scratch (first time working with MCP servers)
- SerpAPI key — not yet created, needs signup (Phase 0)
- Google account for Docs export: `brockfrarycerts@gmail.com`, OAuth user-consent flow (both n8n and CrewAI run locally, so no service account needed)
- **LLM provider:** OpenAI `gpt-4o-mini` as the default model for both implementations — cheap and fast enough to give clean, comparable cost/latency numbers and to support repeated runs for the reproducibility KPI without burning budget. Anthropic Claude (e.g. Haiku 4.5) is an optional later comparison once the baseline works, not required for the MVP.

See [Open Questions](ROADMAP.md#open-questions) in the roadmap — a few remain unconfirmed (MCP server choice, budget cap number, reference projects to model).

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

## Patterns carried over from prior VT AGI course projects

`documentation/other_projects/` (git-ignored — local reference only, not part of this repo's history) holds two earlier course projects that inform this build:

- **Observability:** log every agent/node transition as structured JSONL, one line per transition, locally by default; mirror to a cloud dashboard only if configured, degrading gracefully if not. Satisfies this project's own logging/retry/cost-tracking requirement.
- **Testing:** run the full test suite against mocked LLM responses — no live API key or network access needed to run `pytest`/CI. Matches the assignment's "unit tests: mock inputs/outputs" requirement.
- **Secrets:** commit only `.env.example` with variable names, never actual values; `.env` stays git-ignored.
- **WSL2 networking gotcha:** in a prior project, n8n running in WSL2 could not reach a Windows-side service via `localhost` and needed the Windows host IP instead. Not expected to bite here since n8n, the MCP server, and CrewAI are all planned to run inside the same WSL2 Ubuntu instance — but worth a quick check in Phase 0 if anything ends up split across the WSL2/Windows boundary.
- **n8n launch method:** starting n8n from PowerShell via a non-interactive `wsl bash -c "..."` call let Windows PATH entries shadow the nvm-managed Node.js install, breaking the n8n binary. Start n8n from an **interactive WSL terminal** instead — it sources `.bashrc`, which sets nvm's PATH before any Windows entries get appended.
- **n8n expression scope after branch nodes:** downstream of any IF/Slack/HTTP branch node, bare `$json` resolves to *that branch node's* output, not the original pipeline data — a silent source of `undefined` fields. Use named-node expressions instead, e.g. `$('Compose Final').item.json.fieldName`, to reach the correct upstream node regardless of which branch was taken. Relevant anywhere this workflow's paths reconverge before the Docs Writer.
- **n8n can't write local files directly:** the Code node sandboxes `require('fs')`, and the Write to File node needs binary input, not text. A prior project's workaround was a dedicated backend endpoint that owns all file I/O, with the n8n node being a plain HTTP Request to it. Applies here too: any local evidence/citation caching should live in the MCP server (or another backend), not in an n8n Code/Write-to-File node.
- **HTTP Request body encoding for multi-line text:** a raw JSON-mode body broke with a "bad control character" error when a field (an LLM-drafted post) contained newlines. Use n8n's "Using Fields Below" mode instead of a raw JSON string — it handles escaping per-field. Relevant wherever this workflow passes multi-paragraph GTM draft text between nodes or into the Docs Writer's HTTP call.
- **Reusable doc tooling:** a matched pair of scripts (`generate_reflection.py` / `decompose_reflection.py`, python-docx based) assembles/disassembles a formatted `.docx` from markdown + images. Not needed for the core build, but worth reaching for when producing the final submission documentation/reflection.
