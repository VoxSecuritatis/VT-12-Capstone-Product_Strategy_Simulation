# Roadmap

Build order for the capstone, phased to match the assignment's Actions section (`documentation/1762856365_capstoneprojectproblemstatement.md`). Every phase gate is a KPI or deliverable from that document — see [README.md](README.md#success-criteria--north-star-kpis).

Nothing below is started yet. Checkboxes track progress across future sessions.

## Phase 0 — Environment & Access Setup (blocking)

- [x] Dev environment confirmed: WSL2, Ubuntu 24.04.4 LTS
- [x] n8n confirmed installed locally: v2.27.4
- [ ] Install Python 3.11+ and `uv` in WSL (if not already present)
- [ ] Sign up for a SerpAPI key (free tier: 100 searches/month — should be sufficient for scenario testing)
- [ ] Set up a Google Cloud project, enable Docs API, generate OAuth client credentials for `brockfrarycerts@gmail.com` (user-consent flow — both implementations run locally, so no service account needed)
- [x] LLM provider chosen: OpenAI `gpt-4o-mini` for both implementations (default). Claude Haiku 4.5 optional later, for a quality/cost comparison once the baseline is working.
- [ ] Pick an MCP server to adapt (see task below) rather than building one from scratch
- [x] Git repo identified: [VoxSecuritatis/VT-12-Capstone-Product_Strategy_Simulation](https://github.com/VoxSecuritatis/VT-12-Capstone-Product_Strategy_Simulation) (already created on GitHub with a LICENSE + placeholder README — needs local `git init`, remote wired up, and a merge rather than a fresh init)
- [ ] Review prior projects for reusable MCP server / CrewAI patterns (paths TBD — see [Open Questions](#open-questions))

**Exit criteria:** every tool in the architecture diagram can authenticate; `curl` against the MCP server and a manual SerpAPI call both succeed.

## Phase 1 — MCP Server (shared by both implementations)

- [ ] Survey existing MCP servers (official reference servers, MCP marketplace, prior-project examples) for a web-search/fetch server that can be adapted rather than built from scratch
- [ ] Wire the chosen server to SerpAPI for search
- [ ] Add/confirm tool contracts: search, fetch/snapshot page, citation/evidence record
- [ ] Add response caching + timestamped snapshots (source-volatility mitigation)
- [ ] Smoke-test each tool with `curl`

**Exit criteria:** MCP tools independently return cited, timestamped evidence JSON.

## Phase 2 — n8n Implementation

**2.1 Environment**
- [ ] n8n running on the VM, MCP server reachable from it

**2.2 Workflow**
- [ ] Nodes: Trigger → Head Planner → Research Agent → Analyst Agent → Strategy Agent → Docs Writer
- [ ] Wire MCP tools into Research Agent node(s)
- [ ] Wire SerpAPI into Research Agent node(s)
- [ ] Logging, retries, cost/latency tracking on each node

**2.3 Test & export**
- [ ] Execute Node testing per node
- [ ] Debug and validate outputs against a fixed test brief
- [ ] Export workflow as JSON → `n8n/`

**Exit criteria:** one end-to-end run produces a drafted GTM doc in <15 minutes; JSON export saved.

## Phase 3 — CrewAI Implementation

**3.1 Environment**
- [ ] `uv`-structured CrewAI project scaffolded in `crewai/`
- [ ] MCP server reachable from CrewAI tools

**3.2 Agents & flow**
- [ ] Define Head Planner, Research, Analyst, Strategy agents with roles/tools
- [ ] Chain tasks via CrewAI Flows for hand-offs
- [ ] Persist interim outputs (tables, markdown) between stages
- [ ] Integrate MCP tools + SerpAPI

**3.3 Test & export**
- [ ] Run end-to-end against the same fixed test brief used for n8n
- [ ] Capture logs and debugging notes
- [ ] Capture CrewAI chatbot screenshots
- [ ] Save project files (uv structure) → `crewai/`

**Exit criteria:** same test brief as Phase 2 produces a comparable GTM doc; screenshots captured.

## Phase 4 — Testing

- [ ] Unit tests: mocked SerpAPI/MCP/Docs tool I/O
- [ ] Scenario tests: fixed briefs with golden expected outputs (shared across both implementations)
- [ ] Human rubric review: clarity, feasibility, differentiation (target ≥4/5)
- [ ] Reproducibility check: rerun same brief multiple times, measure fact consistency (target ≥80%)

## Phase 5 — Comparison (n8n vs. CrewAI)

- [ ] Cost per run (both implementations, same test brief)
- [ ] Latency per run
- [ ] Reliability/error rate across repeated runs
- [ ] Write up comparison → `comparison/`

## Phase 6 — Documentation & Submission Packaging

- [ ] README finalized with architecture, setup, and testing notes (this file evolves into that)
- [ ] Sample Google Doc output saved → `outputs/`
- [ ] All five deliverables from the assignment confirmed present (see README checklist)

---

## Open Questions

Resolved during initial planning:

- ~~Dev environment~~ → WSL2, Ubuntu 24.04.4 LTS, local (no VM)
- ~~LLM provider~~ → OpenAI `gpt-4o-mini` baseline; Claude Haiku 4.5 optional stretch comparison
- ~~Google Docs auth~~ → OAuth user-consent, `brockfrarycerts@gmail.com`, both implementations local
- ~~Chatbot screenshots~~ → CLI-based (e.g. `crewai chat`) for now
- ~~Timeline~~ → No hard deadline; course-end project for the VT Applied Agentic AI Post-Graduate Program, paced at your discretion

Still open:

1. **Reference projects** — you mentioned other projects with patterns worth modeling (MCP server setup, CrewAI structure). What are their paths, so they can inform Phase 1/3 instead of starting blind?
2. **MCP server choice** — no specific server picked yet. Once you can point to reference projects (Q1), Phase 1 will evaluate options against those.
3. **Budget cap number** — proposed **$1.00 per end-to-end run, per implementation**, based on `gpt-4o-mini` pricing (~$0.15/1M input, ~$0.60/1M output tokens) and SerpAPI's free tier (100 searches/month). A full 4-agent run should land well under $0.20 in practice, leaving headroom for repeated reproducibility-KPI runs. Open to a different number if you have one in mind — otherwise this becomes the working target.
4. **Git** — the GitHub repo already exists with an initial commit (`LICENSE` + placeholder `README.md`), so this needs a `git init` + remote add + merge (not a fresh init) to avoid losing that commit. Local git setup is queued next; **push to GitHub will wait for your explicit go-ahead** since it's a shared/visible action.
