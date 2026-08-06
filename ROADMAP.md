# Roadmap

Build order for the capstone, phased to match the assignment's Actions section (`documentation/1762856365_capstoneprojectproblemstatement.md`). Every phase gate is a KPI or deliverable from that document — see [README.md](README.md#success-criteria--north-star-kpis).

Checkboxes track progress across sessions. Current state: **Phase 0, Phase 1, and Phase 2 (2.1, 2.2,
2.3) all complete.** The full n8n agent chain (Trigger -> Head Planner -> Research Agent -> Analyst
Agent -> Strategy Agent -> Docs Writer) is built, named, and confirmed working end-to-end in a single
**Execute workflow** run (~166,564 tokens, 3m 5s), producing a real, readable Google Doc GTM plan and
recovering from a real fetch failure mid-run -- the Phase 2.3 exit criterion (<15 minutes) is met,
and the workflow JSON is exported to `n8n/`. Run-log rows (cost/latency/tokens) are captured via a
post-hoc ingestion script, confirmed against real execution data ($0.1104/run). Retry On Fail is
enabled on every node that supports it (the two Google Docs nodes); the two AI-tool nodes that don't
support it are a documented platform limitation, not a gap -- see the Known Platform Limitations
section below. **Phase 0 through Phase 3 are now all complete.** Phase 3 (CrewAI implementation) is
built and proven end-to-end against the same fixed test brief, with real tool use (SerpAPI + this
project's own MCP server) and real cost figures ($0.3767, $0.215656, and $0.211878 across three real
runs, the last two both well under the $0.50/run cap). Run-log rows are emitted via
`crewai/run_and_log.py` (4 rows per run confirmed appended and schema-valid, matching n8n's shared
schema including timezone-aware timestamps) and 8 real, live-captured screenshots document the full
CrewAI chain (see Phase 3.3, `SCREENSHOTS.md`). **Phase 4 (Testing) is now also complete:** unit
tests (5 new CrewAI tests + existing mcp-server/log_server suites), scenario tests against 2 new
fixed briefs with golden-fact checks on both implementations, a reproducibility check on the primary
brief (3 reruns each, real cost/fact data), and a human rubric review (both n8n and CrewAI avg
4.33/5, exceeding the 4/5 target). **Phase 5 (Comparison) is now also complete:** `comparison/compare.py`
(pure stdlib, tested) reads the shared run-log schema and writes `comparison/report.md` -- real
findings: n8n averages **$0.0642**/run and **1m 59.4s**/run vs. CrewAI's $0.1379/run and 6m 39.0s/run
(n8n roughly 2.1x cheaper and faster, both 100% reliable across all 15 logged runs). See Phase 4/5
below for full results. **A full rubric audit of Phases 0-5 is also done** (see "Rubric Audit" section
below) -- 4 real gaps and 3 judgment calls found, all documented, none fixed yet pending per-item
approval. Next: resolve the audit items, then Phase 6 (Documentation & Submission Packaging).

## Phase 0 — Environment & Access Setup (blocking)

- [x] Dev environment confirmed: WSL2, Ubuntu 24.04.4 LTS
- [x] n8n confirmed installed locally: v2.27.4
- [x] Python 3.11+ and `uv` confirmed in WSL: Python 3.12.3 already present, `uv 0.12.1` installed (installer wires it onto PATH automatically). Along the way, fixed WSL's DNS (was fully broken: `generateResolvConf = false` left it with no DNS servers at all) and a VPN-vs-WSL2-NAT connectivity issue (real HTTPS connections timing out after resolving) by disabling the VPN and switching WSL to mirrored networking (`C:\Users\<user>\.wslconfig`, `networkingMode=mirrored`) — needed since network calls are core to this project (SerpAPI, Google APIs, PyPI). An IPv6-disable via `/etc/sysctl.d/` was also applied and may no longer be necessary now that mirrored networking + VPN-off works, but is left in place as harmless.
- [x] `.env.example` created (tracked, placeholder values only: `SERPAPI_API_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-5`). `.env` (git-ignored) already exists locally with a real `OPENAI_API_KEY` filled in — Claude never reads/writes `.env` itself, per standing rule.
- [x] SerpAPI key obtained (free tier: 250 lookups/month) and added to `.env` by the user
- [x] Google Cloud project (`vt-capstone-gtm-planner`) created; Google Docs API and Google Drive API enabled; OAuth consent screen configured (External, Testing, scopes `.../auth/documents` + `.../auth/drive.file`, test user added); OAuth 2.0 Client ID created (Web application type, redirect URI `http://localhost:5678/rest/oauth2-credential/callback` for n8n). Client ID/Secret added to `.env` by the user. Screenshots in `screenshots/Phase0-01` through `Phase0-08`.
- [x] LLM provider chosen: OpenAI `gpt-5` for both implementations (default; updated from `gpt-4.1-mini`, set directly in `.env.example`). Claude Haiku 4.5 optional later, for a quality/cost comparison once the baseline is working.
- [x] Picked an MCP server to adapt: the official reference `fetch` server (`modelcontextprotocol/servers`), extended with a custom `search` tool (SerpAPI) and a citation/caching layer, over real MCP protocol (SSE transport) so both n8n's MCP Client Tool node and CrewAI's MCPServerAdapter connect natively. See Phase 1 below for details.
- [x] Confirmed n8n startup: `n8n start` inside WSL logs `Editor is now accessible via: http://localhost:5678`, and it responds `HTTP 200` from the Windows side too (mirrored networking didn't break port forwarding). Node v24.18.0/npm/n8n 2.27.4 are correctly nvm-managed inside WSL, exactly as originally recorded — but only visible from an **interactive** shell (`bash -ic`, sources `.bashrc` where nvm lives). A **non-interactive login shell** (`bash -lc`, sources `.profile` only) falls through to Windows-side PATH entries instead (e.g. `/mnt/f/nodejs/node.exe`), which aren't executable from Linux and fail with "Permission denied" — the practical form of the prior project's PATH-shadowing gotcha. Always launch n8n via an interactive WSL shell/terminal, not a scripted non-interactive one. Confirmed independently by user in a browser: dashboard loads with no issues.
- [x] Git repo identified: [VoxSecuritatis/VT-12-Capstone-Product_Strategy_Simulation](https://github.com/VoxSecuritatis/VT-12-Capstone-Product_Strategy_Simulation) (already created on GitHub with a LICENSE + placeholder README — needs local `git init`, remote wired up, and a merge rather than a fresh init)
- [x] Reviewed prior projects for reusable patterns — `documentation/other_projects/` (git-ignored, local only): a LangGraph 3-agent pitch-deck planner and an n8n+FastAPI LinkedIn automation PRD. Adopting: structured JSONL logging per agent/node transition (cloud mirror optional), pytest against mocked LLM responses only, `.env.example`-with-no-secrets convention. Neither used CrewAI or MCP directly, so no direct code to port for Phases 1/3 — just conventions.

**Exit criteria:** every tool in the architecture diagram can authenticate; `curl` against the MCP server and a manual SerpAPI call both succeed.

See `SETUP.md` for the full installed-toolchain inventory (versions, locations, obtain/verify commands) and the WSL networking fixes applied above.

## Phase 1 — MCP Server (shared by both implementations)

- [x] Surveyed the option space (interview + research, not a from-scratch build): confirmed both n8n (native MCP Client Tool node, SSE, shipped since v1.88.0) and CrewAI (`crewai-tools` MCPServerAdapter, SSE) can connect to a real MCP server natively. Chose to adapt the official reference `fetch` server rather than build blind or hunt for an unverified off-the-shelf search+fetch bundle.
- [x] Wired a custom `search` tool to SerpAPI (`mcp-server/src/mcp_server/tools/search.py`) — plain `requests` call to SerpAPI's REST endpoint, no extra SDK dependency.
- [x] Tool contracts confirmed: `search` (query -> cited results: title/link/snippet/citation_id) and `fetch` (url -> cited, timestamped markdown snapshot), both returning citation IDs backed by the cache layer.
- [x] Response caching + timestamped snapshots implemented (`mcp-server/src/mcp_server/tools/cache.py`): JSON files under `mcp-server/.cache/` (git-ignored), keyed by a hash of the URL, with a 6-hour freshness window. Confirmed via curl that a repeat `fetch` call on the same URL returns instantly from cache instead of re-fetching.
- [x] Smoke-tested each tool with `curl` against the running SSE server: full MCP handshake (`initialize`), `tools/list`, and `tools/call` for both `search` and `fetch` all verified end-to-end with real responses (see SETUP.md for the exact commands).
- [x] `pytest` suite (9 tests) covering cache, search, and fetch logic against mocked HTTP responses — no live network/API calls needed to run the suite.

**Node.js note:** `fetch` uses `readabilipy` for higher-quality content extraction when Node.js is available (checked via `shutil.which("node")`, avoiding a known upstream hang when Node is missing/misconfigured — see SETUP.md). First live call incurred a one-time ~15-20s delay while `npx` installed a helper package; subsequent calls are fast. Worth a quick mental note against the <15-minute latency KPI, though it's a one-time warm-up cost, not per-run.

**Exit criteria:** MCP tools independently return cited, timestamped evidence JSON. **Met.**

## Phase 2 — n8n Implementation

**2.1 Environment**
- [x] n8n running, MCP server reachable from it -- confirmed end-to-end, not just a reachability
  check: blank canvas built from scratch (Trigger manually -> AI Agent -> OpenAI Chat Model (`gpt-5`)
  + MCP Client Tool). MCP Client Tool node configured with Endpoint `http://127.0.0.1:8000/sse`,
  Server Transport `Server Sent Events (Deprecated)` (matches the server's `transport="sse"` --
  n8n's label calls it deprecated in favor of Streamable HTTP, but it's the correct choice for this
  server), Authentication `None`, Tools to Include `All`. Ran the full workflow: the Agent decided on
  its own to call `fetch` on a live test URL, the MCP server returned a real cited/timestamped
  snapshot, and the Agent summarized it back -- "Workflow executed successfully," ~2,086 tokens,
  ~42s. This proves the same citation/caching design from Phase 1 working end-to-end from n8n.
  - Known n8n rough edge hit along the way: the MCP Client Tool node's standalone "Test" popup
    throws `Cannot read properties of undefined (reading 'inputType')` for any MCP tool with more
    than one parameter (our `search` tool takes two: `query`, `num_results`) -- documented upstream
    as [n8n-io/n8n#21569](https://github.com/n8n-io/n8n/issues/21569). Not a bug in our server or
    setup -- it's a limitation of that manual test popup only. `fetch` (single parameter, `url`) was
    proven working end-to-end via the real Agent-driven run above; `search` (two parameters) still
    needs its own real Agent-driven test (a prompt that requires a web search) before it's confirmed
    -- next thing to try in Phase 2.2.

**2.2 Workflow**
- [x] Nodes: Trigger → Head Planner → Research Agent → Analyst Agent → Strategy Agent → Docs Writer
  (full chain built, named, chained, and confirmed working end-to-end: a real, well-formatted Google
  Doc GTM plan is produced from the fixed test brief -- see `Phase2-08` screenshot. Docs Writer is
  two nodes: `Docs Writer - Create a document` then `Docs Writer - Insert Content`, detailed below)
  - [x] Docs Writer node added (n8n's Google Docs node, renamed from its default "Create a document"
    label per the standing node-naming rule), chained after Strategy Agent. Resource: Document,
    Operation: Create. Confirmed working end-to-end twice (`Phase2-06`/`Phase2-07` screenshots) --
    creates a real Google Doc titled `GTM Plan - {{ $now }}` in the authenticated account's Drive.
  - [x] Second Docs Writer node, `Docs Writer - Insert Content` (Resource: Document, Operation:
    Update), chained after the Create node, actually writes Strategy Agent's GTM plan text into the
    document body. Fields: **Doc ID or URL** (Expression mode) =
    `{{ $('Docs Writer - Create a document').item.json.id }}`; one Action (`Object: Text`,
    `Action: Insert`, `Insert Segment: Body`, `Insert Location: At End of Specific Position` -- no
    extra numeric index field needed for an empty doc); **Text** (Expression mode) =
    `{{ $('Strategy Agent').item.json.output }}`. Confirmed working via **Execute step** alone,
    without re-running the upstream LLM agents -- n8n reused their already-cached output from the
    prior full run instead of re-invoking them, costing no new tokens. Opened the real resulting
    document (`Phase2-08` screenshot) and confirmed Strategy Agent's `\n`-embedded output string
    renders as genuine paragraph breaks via the Insert Text action, not literal backslash-n
    characters -- an open concern from Phase 0's design notes, now resolved.
    - **Credential:** Google Docs OAuth2 API, using the Client ID/Secret already in `.env` from Phase
      0 (same OAuth client, same redirect URI, no new Google Cloud Console changes needed). During
      the consent screen, deliberately declined the broad "See, edit, create, and delete all of your
      Google Drive files" scope, keeping only the two already configured in Phase 0 (`drive.file` +
      `documents`) -- sufficient for this node to create/write files itself.
    - **Node-config gotchas hit and fixed (same family as the Analyst Agent gotcha above -- worth
      checking on every resourceLocator-style field going forward):** the "Folder Name or ID" field
      is a resourceLocator with `Fixed`/`Expression` tabs and, within Fixed mode, `From list`/`By
      URL`/`By ID` sub-modes. `Drive Name or ID` and `Folder Name or ID` both fail to list real
      options ("Error fetching options from Google Docs") because the `drive.file` scope only grants
      visibility into files/folders the app itself creates or opens -- not arbitrary existing Drive
      contents, so it can't browse to populate the dropdown. This is expected, not a bug. Typing
      `root` (Google Drive API's documented alias for My Drive's top level) directly as a raw
      **Expression** value failed client-side validation ("The value 'root' is not supported!")
      because expression-override on a resourceLocator field is still checked against whatever mode
      is selected underneath. Fix: switch to the **Fixed** tab, then select the single available
      list entry (displayed as `/`) from the dropdown rather than typing anything manually -- this
      properly sets the field's underlying value. (One run also succeeded after typing the plain
      string `default` in Expression mode; exact reason unconfirmed, but the `/`-list-entry approach
      is the reliable, repeatable one to use going forward.)
    - **Fetch-failure fallback validated a second time, different error type:** during one of the
      test runs of this node, Research Agent's MCP Client hit `robots.txt disallows fetching` on a
      different URL (`rascasse.com`) -- distinct from the earlier `403 Forbidden` case -- and
      recovered correctly via the existing fallback instruction with no prompt changes needed,
      confirming the fix generalizes across fetch-failure types. See `Phase2-06` screenshot.
    - **Investigated and resolved:** a separate run showed the SerpApi tool sub-call with status
      "Unknown," 0s duration, and no output despite a real query -- initially suspected SerpAPI quota
      exhaustion, ruled out by checking the account dashboard directly (56/250 monthly searches
      used). A clean re-run showed normal tool activity again, suggesting a one-off n8n Logs-panel
      rendering glitch, not a reproducible functional failure. Noted for Phase 3/testing: an
      anomalously low total token count for a run (e.g. ~2,983 vs. the normal ~100K-150K range) is a
      useful smell test for "something didn't actually execute."
  - [x] Analyst Agent -> Strategy Agent hand-off built and run successfully end-to-end (full chain:
    Manual Trigger -> Head Planner -> Research Agent -> Analyst Agent -> Strategy Agent, "Workflow
    executed successfully," ~121,416 tokens for the full chain). Strategy Agent has no tools of its
    own (drafts the GTM plan from Analyst Agent's synthesis, per README's planner role); Prompt (User
    Message) set to `{{ $('Analyst Agent').item.json.output }}` (same dropdown -> "Define below" ->
    separate text field pattern as Analyst Agent, no repeat of the earlier gotcha this time). System
    Message kept minimal per the academic-scope rule (target customer/ICP, value proposition,
    messaging/channel suggestions, brief launch-plan outline). Output was concrete and specific
    (real ICP, value prop, channel/messaging ideas, launch-plan bullets tied to Analyst Agent's actual
    findings), not generic boilerplate. `Phase2-05-strategy_agent_gtm_plan.jpg` captured and added to
    `screenshots/`, `SCREENSHOTS.md` updated to match.
  - [x] Head Planner -> Research Agent hand-off proven end-to-end (`Phase2-03` screenshot): Head
    Planner (no tools, per README's orchestrator/documenter role) takes a brief and drafts short,
    single-facet research questions; Research Agent executes them via SerpAPI (`search`) + MCP
    (`fetch`). ~100,384 tokens, ~2m 4s for both agents combined, on a real (not placeholder) brief.
  - [x] Research Agent -> Analyst Agent hand-off built and run successfully end-to-end (full chain:
    Manual Trigger -> Head Planner -> Research Agent -> Analyst Agent, "Workflow executed
    successfully", ~46,187 tokens, ~2m 48s). Analyst Agent has no tools of its own (works only from
    Research Agent's output, per README's sense-maker role); Prompt (User Message) set to
    `{{ $('Research Agent').item.json.output }}`, System Message kept minimal per the academic-scope
    rule (short competitor comparison + one qualitative paragraph).
    - **Node-config gotcha hit and fixed:** the "Source for Prompt (User Message)" field is a
      dropdown (`promptType`: `auto` vs `define`), separate from the actual prompt text field. An
      earlier attempt typed the expression into the dropdown itself (via its own `Fixed`/`Expression`
      toggle), which stored the expression as `promptType`'s value instead of picking `define` --
      leaving the real `text` parameter empty and throwing a persistent "Prompt (User Message) is
      required" error. Fixed by: setting the dropdown itself to `Fixed` mode -> `Define below`, which
      reveals a separate `Prompt (User Message)` text field underneath -- the expression belongs
      there, not in the dropdown. Worth checking for on every future agent node (Strategy Agent next).
    - **Fetch-failure fallback added and confirmed working:** an earlier run hit `403 Forbidden`
      fetching `market.us/report/noise-cancelling-headphones-market/` (the site's own anti-scraping
      block, not a config issue) -- the MCP Client Tool node has no documented Settings-tab retry
      option for this (confirmed against official n8n docs and a matching n8n community thread:
      `retryOnFail` only covers the node itself failing to execute, not a tool call erroring inside an
      AI Agent's reasoning loop). Fixed instead with one line added to Research Agent's System
      Message: "If the fetch tool returns an error for a URL, do not retry that same URL -- move on to
      the next search result instead and fetch that one." Confirmed working in a live re-run: MCP
      Client's fetch failed on turn 1 (blocked site), Research Agent moved on and fetched a different
      result on turn 2, and the overall run still reported "Workflow executed successfully" with a
      real, specific output (~154,997 tokens, ~3m 10s for the full chain). The one-time sub-tool
      failure badge that still shows in n8n's Logs panel is expected/acceptable -- it demonstrates the
      exact resilience the rubric's "source volatility" risk item and this "retries" checklist item
      call for, not a residual bug.
    - **Second real-world confirmation, different error type:** a later run hit a fetch failure again,
      this time `robots.txt disallows fetching` a different URL (`rascasse.com`) -- a distinct failure
      mode from the earlier `403 Forbidden`, but the same underlying cause (a site declining the
      request, consistent with our own MCP server's Phase 1 design choice to respect `robots.txt`).
      The existing fallback instruction ("if the fetch tool returns an error for a URL...") is generic
      enough to cover this too, without needing a separate fix -- confirms the fallback generalizes
      across different fetch-failure reasons, not just the one specific case it was written for.
    - **Lesson learned:** a separate, unrelated run earlier the same session showed the SerpAPI tool
      sub-call with status "Unknown," 0s duration, and "No output data returned" despite a real,
      well-formed query -- initially suspected as a possible SerpAPI quota exhaustion. Checked the
      SerpAPI account dashboard directly (56/250 monthly searches used) and ruled that out. A clean
      re-run afterward showed normal tool activity again (real fetch attempts, real errors like the
      robots.txt case above), suggesting the "Unknown" status was a one-off n8n Logs-panel rendering
      glitch for that specific tool sub-call, not a reproducible functional failure. Worth remembering
      for Phase 3/CrewAI comparison and final testing: an oddly low total token count for a run (e.g.
      ~2,983 vs. the normal ~100K-150K range) is a useful smell test for "something didn't actually
      execute," worth checking the Logs panel over before assuming a tool is broken.
  - **Scope-control fixes required to get here, and why they matter going forward:** an initial
    attempt used a "production-ready" Head Planner brief asking for 6 broad research categories.
    This is an academic/portfolio capstone, not a production system -- that framing was the wrong
    instinct and caused real problems: Research Agent fragmented the broad questions into 18-26+
    tool calls and blew past `gpt-5`'s context window (`400 Your input exceeds the context window of
    this model`). Fixed with three changes, all still in effect and worth keeping for every
    remaining agent (Analyst, Strategy, Docs Writer, and the CrewAI agents in Phase 3):
    1. Head Planner's System Message now demands exactly 2 short, single-facet questions (not
       multi-part ones bundling several sub-topics into "one" question).
    2. Research Agent's System Message caps tool use explicitly: at most one search per question,
       one fetch, short final summary.
    3. SerpApi node's **Additional Fields -> Number of Results (num)** set to `3` (down from the
       default 10) -- shrinks payload size per call independent of call count, directly reducing
       context pressure.
  - **Also fixed along the way:** a stray "When chat message received" Chat Trigger node --
    auto-added by n8n the moment the first AI Agent node was created, wired serially ahead of Head
    Planner -- was silently causing Head Planner to be skipped entirely during execution (n8n error:
    "There is no connection back to the node 'Head Planner'"). Deleted; Manual Trigger now connects
    directly to Head Planner. Lesson: n8n auto-scaffolding nodes need to be actively checked for and
    removed if unused, not left in place by default.
- [x] Wire MCP tools into Research Agent node(s)
- [x] Wire SerpAPI into Research Agent node(s)
  - Both confirmed working together end-to-end: prompt "Search the web for recent news about
    Virginia Tech using SerpAPI. Then use the fetch tool to retrieve and read the full content of
    the top result, and summarize it with its citation." -> clean 3-iteration run (~36,857 tokens,
    44s) -> correct search-then-fetch-then-cite chain, real citation ID returned.
  - **Rubric check before building further:** `documentation/1762856365_capstoneprojectproblemstatement.md`
    names MCP tools and SerpAPI as two distinct required integrations (1.2, 2.2, and the Testing
    section all list them separately) -- so both must stay visibly wired in, not collapsed into one.
  - **Root cause of an earlier stuck-loop bug, and the fix:** the MCP server's own `search` tool
    is itself just a SerpAPI wrapper (see Phase 1), so having MCP's `search` *and* the native SerpApi
    node both attached gave the model two overlapping ways to search the web -- it kept alternating
    between them instead of concluding, burning ~200-270K tokens per run before hitting Max
    Iterations. Fixed by giving each tool one distinct job instead of removing either: MCP Client's
    **Tools to Include** narrowed from `All` to `Selected` -> `fetch` only (search capability
    removed from MCP's side); SerpApi node re-activated and remains the sole search tool. This also
    matches the rubric's own phrasing -- "MCP tools for research **and** SerpAPI for queries" --
    almost exactly: SerpAPI searches, MCP fetches/cites.
  - **AI Agent Options -> Max Iterations set to `5`** (down from the n8n default of 10) as a
    standing safety net against this class of loop -- also surfaces a real error fast instead of
    silently burning tokens, given a known n8n bug ([n8n-io/n8n#22771](https://github.com/n8n-io/n8n/issues/22771))
    where hitting the cap shows "Success" instead of a clear error.
- [x] Logging, retries, cost/latency tracking on each node -- logging/cost/latency solved via
  `ingest_execution.py` (Phase 2.3 below). Retries: n8n's native **Retry On Fail** enabled (defaults:
  3 tries, 1000ms wait) on the two nodes that support it, `Docs Writer - Create a document` and
  `Docs Writer - Insert Content` -- confirmed in the re-exported `n8n/VT Capstone GTM Planner.json`
  (`"retryOnFail": true` on both, diffed against the prior export to confirm nothing else changed).
  The two tool-type nodes, `Google search in SerpAPI - Research Agent` and `MCP Client - Research
  Agent`, do **not** expose Retry On Fail at all -- confirmed by direct screenshot on both, a real
  n8n platform limitation, not a config gap; see "Known Platform Limitations & Blockers" item 4 below
  for the full writeup and the existing prompt-level fallback that covers those two nodes instead.
- [x] Wherever paths reconverge before the Docs Writer, use named-node expressions (`$('NodeName').item.json.field`) instead of bare `$json` — audited the exported workflow JSON directly: it is a single linear chain with no IF/Switch/Merge node anywhere, so no reconvergence point exists, and every cross-node expression already present uses named-node syntax. Nothing to change.
- [x] Use "Using Fields Below" mode (not raw JSON mode) on any HTTP Request node carrying multi-paragraph GTM draft text, to avoid "bad control character" errors on embedded newlines — moot: there is no HTTP Request node in this workflow at all; the real-time logging design that would have needed one was replaced by the post-hoc `ingest_execution.py` script (see "Known Platform Limitations & Blockers" item 1 below).

**2.3 Test & export**
- [x] Execute Node testing per node -- each node individually tested and confirmed during the build
  (Head Planner, Research Agent, Analyst Agent, Strategy Agent, both Docs Writer nodes), plus a full
  single-click **Execute workflow** run of the entire seven-node chain (`Phase2-09` screenshot).
- [x] Debug and validate outputs against a fixed test brief
  - **Fixed test brief, locked in:** "A new budget noise-cancelling headphone for commuters. Who's
    the target customer and who are the main competitors?" -- kept deliberately minimal per the
    academic-scope rule. Proven working end-to-end through the entire chain (`Phase2-09`); reuse it
    verbatim for the CrewAI implementation in Phase 3, so Phase 5's comparison is apples-to-apples.
  - **Exit criterion met:** a single full-chain run completed in **3m 5s** (~166,564 tokens),
    producing a real, readable Google Doc GTM plan -- well within the <15-minute budget, including a
    real, recovered mid-run tool failure (not just a best-case/no-errors run).
- [x] Workflow itself renamed from n8n's default "My workflow" to **`VT Capstone GTM Planner`**
  (matches the Google Cloud project naming precedent from Phase 0, `vt-capstone-gtm-planner`) --
  was still the default name through every prior screenshot in this phase; caught and fixed before
  export.
- [x] Export workflow as JSON → `n8n/VT Capstone GTM Planner.json` (n8n's own export uses the
  workflow's display name as the filename, spaces included). Reviewed the exported file directly:
  credentials are referenced only by internal ID + display name (e.g. `"name": "OpenAI account"`) --
  no actual API keys, OAuth Client Secret, or Client ID values are embedded anywhere, so it's safe to
  track in git. Structure matches the built workflow exactly (all agents' System Messages, Research
  Agent's two scoped tools, Docs Writer's Create + Insert Content fields). Minor, harmless
  inconsistency noted: Strategy Agent has no explicit `maxIterations` override (Research Agent and
  Analyst Agent both do, at `5`) -- falls back to n8n's default of 10, but has no functional impact
  since Strategy Agent has no tools to loop on.
- [x] Backend endpoint built and tested: `comparison/log_server/` (`uv` project, zero new
  dependencies -- Python stdlib `http.server` only), exposing `POST /log`, which validates a row
  against the shared schema and appends it to `comparison/run_logs/run_logs.jsonl`. Same
  n8n-can't-write-files-itself rationale as the Phase 1 MCP server caching layer, now also citing
  two 2026 sandbox-escape CVEs (CVE-2026-1470, CVE-2026-0863) specific to n8n's Code node as the
  reason not to route around the sandbox. Full pytest suite written (18 tests: schema validation
  edge cases, a real `ThreadingHTTPServer` instance driven over a real socket in tests, no mocking
  needed). See `SETUP.md` for run/test commands.
  - **Why a Python backend instead of a native n8n workaround:** researched n8n's own
    "Read/Write Files from Disk" node as an alternative before deciding to build this -- it does
    support an Append mode, but (a) its Write operation only accepts binary input, requiring an
    extra "Convert to File" node just to write plain text/JSON, and (b) on n8n 2.0+ (we're on
    2.27.4), file-write access is restricted by default to `~/.n8n-files`, unreachable from our
    actual project folder without a startup config change (`N8N_RESTRICT_FILE_ACCESS_TO`). A small
    Python endpoint avoided both, and doubles as the shared logging mechanism Phase 3's CrewAI
    implementation will also need (CrewAI is already Python, so it can call the same validation/
    append logic directly, no HTTP hop needed) -- a n8n-only native fix would not have given us that
    reuse.
  - **Design decisions confirmed with the user before building, not assumed:** stdlib
    `http.server` over FastAPI+uvicorn (zero new dependencies, no approval gate needed); pytest
    tests written despite the user's "skip the testing" phrasing, which turned out to mean skip
    only the manual curl-verification step, not skip automated tests entirely (worth double-checking
    this kind of ambiguous phrasing rather than assuming the more minimal reading); no
    `LOG_SERVER_HOST`/`PORT` addition to `.env.example` (mirrors the existing
    `MCP_SERVER_HOST`/`PORT` precedent -- non-secret, safe-defaulted, documented in prose instead);
    `comparison/run_logs/` gitignored like `mcp-server/.cache/`, per the user's explicit call --
    overrides the initial recommendation to track it as KPI evidence, since the user judged it closer
    to disposable runtime output than tracked proof (screenshots remain the tracked evidence trail
    for grading instead).
  - **Lesson learned -- stdout buffering:** after starting the server as a background process, its
    startup log line (`[INFO] log_server listening on ...`) didn't appear even after several
    seconds -- not a real failure, just Python's stdout being block-buffered when output isn't
    attached to a real terminal (a known behavior, not specific to this project). Confirmed the
    server was actually running with a real `curl` `POST` (`HTTP 201`) instead of waiting on the
    buffered print line. Worth remembering for any future background Python process in this
    project: a missing startup log line on its own isn't proof of failure -- verify with a real
    request before assuming something's wrong.
- [x] Emit run-log rows (`run_id, implementation=n8n, agent, timestamp, tokens_in, tokens_out, cost_usd, latency_ms, run_status`) to `comparison/run_logs/` -- **not** via an in-workflow HTTP Request node as originally planned (n8n's Agent node doesn't expose the token/cost data an in-workflow node would need -- see the design-gap note below); solved instead via `ingest_execution.py`, a post-hoc script run once per completed execution. Confirmed working on a real execution with real data (below).

## IMPORTANT: Known Platform Limitations & Blockers (for reflections doc)

Consolidated here, all in one place, so nothing gets lost before the final reflections document is
written. Each of these is a real, encountered, citable limitation of the tools this project is
built on -- not a project design flaw -- and each ties back to a specific rubric line.

### 1. n8n does not expose per-agent token usage -- affects cost/latency tracking

**Where this hits the rubric, verbatim** (`documentation/1762856365_capstoneprojectproblemstatement.md`):
- Tasks section: *"Implement logging, retries, and **cost/latency tracking**"*
- Section 1.2 (n8n build): *"Enable logging, retries, and **cost tracking**"*
- Testing section: *"**Comparison:** Measure **cost, latency**, and reliability across n8n and CrewAI"*
- KPI table: *"**Cost efficiency:** Cloud/API spend per run within budget cap"* and *"**Reproducibility:** >=80% consistent facts across multiple runs"* -- both effectively unmeasurable without real per-run cost/token data.

**The gap:** while designing the `log_server` HTTP Request wiring (this section, above), discovered that n8n's `@n8n/n8n-nodes-langchain.agent` node (used by every one of our five agents) **does not propagate token usage to its own output**. The token/cost data is real and does exist -- it's visible in each Chat Model sub-node's own output panel during execution, and it's what the Logs panel has been showing us manually all session -- but it is **silently dropped** and never appears in the parent Agent node's `$json`, so no downstream node (including an HTTP Request node meant to log it) can read it via a normal expression.

**This is a confirmed n8n platform bug, not a gap in our design or a config mistake:**
- [n8n-io/n8n#26302 -- "Agent node does not expose ChatModel token usage in output or intermediateSteps"](https://github.com/n8n-io/n8n/issues/26302) (open GitHub issue against n8n itself)
- [n8n Community: "Add token usage output to AI Agent and Chat Model subnodes"](https://community.n8n.io/t/add-token-usage-output-to-ai-agent-and-chat-model-subnodes/255475) (open feature request)
- [n8n Community: "How to access tokenUsage from a sub-node Model within an AI Agent?"](https://community.n8n.io/t/how-to-access-tokenusage-from-a-sub-node-model-within-an-ai-agent/294577)
- [n8n Community: "Retrieve LLM Token Usage in AI Agents"](https://community.n8n.io/t/retrieve-llm-token-usage-in-ai-agents/68714)
- [n8n Community: "How to get AI token usage information from AI Agent?"](https://community.n8n.io/t/how-to-get-ai-token-usage-information-from-ai-agent/94671)
- Per-node **execution time** (latency) has the same shape of problem -- no clean built-in expression variable either, per [n8n Community: "Execution Time for Each Node"](https://community.n8n.io/t/execution-time-for-each-node-created/23504) (a multi-year-old, still-open feature request).

**Why a real-time HTTP Request node (the originally planned approach) can't fully solve this:** it can only read what's in `$json` at that point in the graph, and per the above, tokens/cost/latency simply aren't there to read -- wiring it up as originally planned would only be able to log placeholder zeros for those four fields, which would be worse than not logging them at all (misleading data is worse than an honest gap).

**The real data does exist, just not where a workflow-internal expression can reach it:** confirmed n8n's own REST API, `GET /executions/{id}?includeData=true`, returns the full execution record **after a run completes**, including each node's real `runData` (per [n8n Community: "/api/v1/executions/{id} returns summary only, missing node details"](https://community.n8n.io/t/api-v1-executions-id-returns-summary-only-missing-node-details-v1-90-2-self-hosted-docker/116158) and [n8n Community: "Extracting AI Agent Token Usage: 'Get Execution' node returns a massive array..."](https://community.n8n.io/t/extracting-ai-agent-token-usage-get-execution-node-returns-a-massive-array-of-all-executions-instead-of-a-specific-id/297360), the latter describing the exact same problem this project has). This is the same underlying data source the Logs panel has been rendering from all session.

**Path forward -- built and confirmed working on real data:** `comparison/log_server/src/log_server/ingest_execution.py`, a post-hoc ingestion script run once after a real workflow execution completes. Takes an execution ID (or defaults to the most recent one), calls n8n's own REST API (`GET /executions/{id}?includeData=true`) to pull the real per-node data, cross-references it against the exported workflow JSON (`n8n/VT Capstone GTM Planner.json`) to correctly attribute each Chat Model sub-node's token usage to its parent agent, and appends one row per agent/step to `run_logs.jsonl` via the same validation logic `log_server`'s HTTP endpoint uses. 12 new pytest tests (30 total in the suite now), fixtures modeled directly on a real captured execution's structure, not guessed. Requires an `N8N_API_KEY` (Settings -> n8n API in n8n itself; added to `.env`, never read/written directly -- see the incident note below).

**Confirmed against a real execution (id 48, the full seven-node chain run):**
```
Research Agent:                tokens_in=164353  tokens_out=209  cost_usd=0.104587  latency_ms=19258   success
Head Planner:                  tokens_in=82      tokens_out=61   cost_usd=0.000357  latency_ms=26750   success
Analyst Agent:                 tokens_in=271     tokens_out=527  cost_usd=0.002806  latency_ms=35714   success
Strategy Agent:                tokens_in=608     tokens_out=453  cost_usd=0.002648  latency_ms=18096   success
Docs Writer - Insert Content:  tokens_in=0       tokens_out=0    cost_usd=0.0       latency_ms=815     success
Docs Writer - Create a document: tokens_in=0     tokens_out=0    cost_usd=0.0       latency_ms=1742    success
```
Total real cost for this run: **$0.1104** -- see the Open Questions section below, this finally answers the budget-cap question with real per-agent data instead of a single-step estimate.

**Incident during setup, worth remembering:** while debugging why `N8N_API_KEY` wasn't loading via a bash `source .env` command, ran `tail -c 80 .env | od -c` to inspect encoding -- which prints raw file bytes and inadvertently displayed the actual API key value in plaintext in the session transcript, a direct violation of the standing "never read `.env`" rule. The key was immediately revoked and regenerated. Root cause of the original problem (separate from the exposure) was confirmed as `.env`'s Windows CRLF line endings breaking bash's `source` command specifically (even a non-secret existing variable, `OPENAI_MODEL`, failed to load the same way) -- `python-dotenv` (already used by `mcp-server`) handles this correctly, which is why `ingest_execution.py` uses it instead of shell-level sourcing. **Lesson: never use a command that dumps raw file bytes/content (`cat`, `tail`, `od`, etc.) against `.env`, even for encoding diagnostics -- use a language-level loader (`python-dotenv`) and check only derived facts (e.g., string length) if verification is ever needed without touching the file directly.**

**Why this belongs in the final reflections document:** this is a legitimate, citable platform limitation (not a project shortcoming) that materially affects how literally the "cost/latency tracking" and "Comparison" rubric items can be satisfied by n8n specifically -- worth contrasting directly against CrewAI in Phase 3, where token usage is a first-class, directly-accessible property of every LLM call (no equivalent gap expected there), which is itself an interesting, citable data point for the n8n-vs-CrewAI comparison the rubric explicitly asks for.

### 2. Source volatility -- robots.txt and anti-scraping blocks during fetch

**Where this hits the rubric, verbatim:** the Risks and Mitigations table explicitly names this
class of problem: *"**Source volatility:** Mitigate by caching results, storing page snapshots, and
including timestamps"* -- and it touches the **Source quality** KPI (*">=80% citations from
top-tier or primary sources, 0% broken links"*) and **Coverage** KPI (*">=90% of research questions
answered with linked sources"*).

**The limitation:** the MCP server's `fetch` tool deliberately respects `robots.txt` (a Phase 1
design choice, not a bug), and some real-world sites also return `403 Forbidden` to any
programmatic/bot-like request regardless of `robots.txt`. Both are the *site's own* access policy,
not something this project can or should override -- respecting `robots.txt` is the correct,
ethical behavior for a fetch tool, even though it means some search results are simply unreachable.
Encountered live, more than once, during real test runs:
- `403 Forbidden` fetching `market.us` (`Phase2-04`/`Phase2-06` screenshots, `ROADMAP.md` Phase 2.2)
- `robots.txt disallows fetching` on `rascasse.com` (`Phase2-06`/`Phase2-09` screenshots) -- hit
  **twice**, on two separate real runs, for the same URL, confirming this is a consistent, not
  one-off, condition for that particular site/query combination.

**Mitigation already built and proven working, twice, live:** Research Agent's System Message
includes an explicit fallback instruction ("if the fetch tool returns an error for a URL, do not
retry that same URL -- move on to the next search result instead"). Confirmed recovering cleanly
from both error types above, in `Phase2-09`'s full end-to-end run, without derailing the rest of the
chain (see ROADMAP.md Phase 2.2 for the full incident/fix history).

**Residual risk, honest about the limit of the mitigation:** the fallback only helps if *at least
one* of SerpAPI's returned results is fetchable. If every top result for a given research question
happened to be blocked, Research Agent would have to fall back to search-snippet text alone (no
full-page fetch), which is a real, if statistically unlikely, edge case against the Coverage and
Source-quality KPIs above. Not observed happening in any real run so far, but worth naming
explicitly as a known limit rather than claiming the mitigation is bulletproof.

### 3. n8n's AI Agent "Max Iterations" cap can silently report "Success"

**Where this hits the rubric:** the **Reproducibility** KPI (*">=80% consistent facts across
multiple runs"*) depends on being able to trust a run's own reported status.

**The limitation:** a known n8n bug, [n8n-io/n8n#22771](https://github.com/n8n-io/n8n/issues/22771)
-- if an AI Agent node hits its `Max Iterations` cap mid-reasoning, n8n reports the node as
"Success" rather than surfacing a clear error, even though the agent was cut off before it actually
finished. Encountered during early Phase 2.2 development (the MCP+SerpAPI tool-overlap loop, before
that root cause was fixed) -- see ROADMAP.md Phase 2.2 for the full incident.

**Mitigation:** `Max Iterations` set to `5` (down from n8n's default `10`) on both Research Agent and
Analyst Agent as a standing safety net -- surfaces this class of problem faster (fewer iterations
before hitting the cap) rather than eliminating the underlying n8n reporting bug, which isn't
something this project can fix. Worth a manual sanity check of final outputs for quality/completeness
even when n8n reports "Success," rather than trusting the status label alone.

### 4. AI tool sub-nodes have no "Retry On Fail" setting at all

**Where this hits the rubric:** the Tasks section and section 1.2 both name "retries" explicitly,
alongside logging and cost/latency tracking.

**The limitation:** n8n's per-node **Retry On Fail** (Settings tab -- confirmed as a real,
documented field for standard nodes at
[docs.n8n.io: Work with nodes](https://docs.n8n.io/build/understand-workflows/workflow-components/work-with-nodes))
is only available on standard main-chain nodes. Any node wired into an AI Agent as a **tool** (an
`ai_tool` connection, not `main`) does not expose it -- confirmed directly, on two different node
types, by opening each one's Settings tab in this project's own workflow:
- `Google search in SerpAPI - Research Agent` (community node): Settings tab shows only "Request
  Options" (Batching / Ignore SSL Issues / Proxy / Timeout) -- no Retry On Fail field exists.
- `MCP Client - Research Agent` (native n8n node, `@n8n/n8n-nodes-langchain.mcpClientTool`):
  Settings tab shows only "Notes" / "Display Note in Flow?" -- same absence, on an entirely
  different (non-community) node package, ruling out "this one node's package is just incomplete"
  as the explanation.

Even where n8n *does* show a Retry On Fail toggle on an AI tool sub-node (not the case for either
node above, but documented elsewhere), it's a separately confirmed bug: the toggle exists but the
tool still doesn't actually retry --
[n8n-io/n8n#15813 -- "AI tool does not 'Retry On Fail'"](https://github.com/n8n-io/n8n/issues/15813).

**Mitigation:** Retry On Fail *is* enabled on the two nodes in this workflow that are real
main-chain nodes and do support it -- `Docs Writer - Create a document` and
`Docs Writer - Insert Content` (Google Docs API calls). For the two tool nodes that can't use native
retry (`Google search in SerpAPI - Research Agent`, `MCP Client - Research Agent`), the existing
prompt-level fallback in Research Agent's System Message ("if the fetch tool returns an error for a
URL, do not retry that same URL -- move on to the next search result instead") is the *de facto*
retry/resilience mechanism, confirmed working live multiple times (see Phase 2.2's fetch-failure
incidents above, including a fresh `403 Forbidden` on `market.us` captured while diagnosing this
exact gap). It operates at a more useful level anyway -- inside the agent's own reasoning loop,
where the failure actually happens -- rather than n8n's engine blindly re-calling the same tool
input.

**Lesson for how I (the assistant) verify n8n UI claims going forward:** the first version of this
investigation assumed Retry On Fail was available generically across all n8n nodes and gave the user
manual click-through instructions for the SerpAPI tool node before ever confirming that node type
actually has the field. It doesn't. Corrected by requiring a real screenshot of each node's actual
Settings tab before writing any further instructions, rather than reasoning from "how n8n nodes
usually work." See the `feedback_n8n_web_lookups` memory for the standing rule this reinforces.

### 5. n8n's Code node cannot safely access the local filesystem

**Where this hits the rubric:** the **Logging, retries, and cost/latency tracking** task, and the
**Source volatility** mitigation ("caching results, storing page snapshots") both implicitly require
*something* to own local file writes.

**The limitation:** n8n's Code node sandboxes `fs` by design, and two serious 2026 CVEs
([CVE-2026-1470](https://research.jfrog.com/post/achieving-remote-code-execution-on-n8n-via-sandbox-escape/),
CVE-2026-0863) are sandbox-escape vulnerabilities specifically around Code-node file/code execution
-- confirming this restriction is a deliberate, currently-important security boundary, not an
arbitrary inconvenience to route around. Full detail already captured for both places this surfaced:
the Phase 1 MCP server's citation/caching layer, and `log_server`'s existence (Phase 2.2, above).

**Mitigation:** both cases solved the same way -- a small standalone local Python process (`mcp-server/`,
`comparison/log_server/`) owns the actual file I/O, and n8n talks to it over a protocol (MCP/SSE,
or plain HTTP) instead of trying to write files itself. Consistent, reusable pattern across this
project, not a one-off workaround.

**Exit criteria:** one end-to-end run produces a drafted GTM doc in <15 minutes (**met**, `Phase2-09`); JSON export saved (still open).

---
**Phase 2 closed out 2026-08-04.** (Prior resume blocks for PHASE2-AGENT-CHAIN and PHASE2-RETRIES
removed -- both fully resolved; see Phase 2.2/2.3 checklists and the Known Platform Limitations
section above for the full history.) Next session starts fresh on **Phase 3 -- CrewAI
implementation**, below.
---

## Phase 3 — CrewAI Implementation

**3.1 Environment**
- [x] `uv`-structured CrewAI project scaffolded in `crewai/` via `crewai create crew crewai` (JSON-first
  scaffold -- `agents/*.jsonc`, `crew.jsonc`, `tools/`, `pyproject.toml` -- no notebooks, per README's
  Python-approach note). Two real setup bugs found and fixed:
  - The scaffolder ran `git init` inside `crewai/`, creating a nested repo inside this project's own
    git repo -- removed (`crewai/.git/`, was empty, zero commits) so `crewai/` is tracked normally,
    same as `mcp-server/` and `comparison/log_server/`.
  - The generated `pyproject.toml` named the project itself `"crewai"`, colliding with the third-party
    `crewai` package it depends on (`uv sync` failed: "project depends on itself"). Renamed the
    package to `vt-capstone-gtm-crew` (folder name, crew display name, and CLI usage all unaffected --
    only the internal Python package identifier changed).
- [x] MCP server reachable from CrewAI tools -- confirmed via a real fetch call through `mcp_fetch`
  (below) returning a real cited/timestamped snapshot from `mcp-server/`, the same server n8n's MCP
  Client Tool node uses.

**3.2 Agents & flow**
- [x] Define Head Planner, Research, Analyst, Strategy agents with roles/tools -- each agent's
  Role/Goal/Backstory mirrors its n8n System Message closely (same task scope, same academic-scope
  minimalism) so the two implementations are testing the same agent design, not two different designs.
  All four use `openai/gpt-5`, matching n8n. Verified end-to-end by loading the actual `Crew` object
  CrewAI's own runner builds (`crewai.project.crew_loader.load_crew`), not just eyeballing the JSON.
- [x] Chain tasks for hand-offs -- used the JSON-first crew's built-in `"process": "sequential"`
  (each task automatically receives prior tasks' outputs as context), not the separate CrewAI Flows
  API -- Flows is a heavier orchestration layer meant for multi-crew pipelines; sequential process
  achieves the same one-task-after-another hand-off this project actually needs, with no added
  complexity. Worth naming honestly since the original checklist line named Flows specifically.
- [x] Persist interim outputs between stages -- two layers, not one. In-context hand-off between
  tasks is inherent to the sequential process (confirmed live: Research Agent's findings appear
  directly in Analyst Agent's context, etc.), which is what this line originally meant. **Corrected
  2026-08-06 (rubric audit):** that reading was too loose for the rubric's literal wording ("Retain
  interim outputs (tables, markdown)") -- in-context passing is a given mechanic of any sequential
  pipeline, not a distinct retention feature. Each of `crew.jsonc`'s four tasks now also sets
  `output_file` (`outputs/1_head_planner.md` through `4_strategy_agent.md`, `create_directory: true`)
  so every real run writes each agent's raw markdown output to a real file, git-ignored
  (`crewai/outputs/`) since it's regenerated fresh each run, not tracked source.
- [x] CrewAI's retry design mirrors n8n's, documented explicitly (rubric audit item 3, resolved
  2026-08-06): Research Agent's task/goal text says "if a fetch fails for a URL, do not retry it --
  move on to the next search result instead," and `research_agent.jsonc`'s `max_retry_limit` is
  present but deliberately left commented out. Same reasoning as n8n's decision not to enable Retry
  On Fail on its AI Agent nodes (see Known Platform Limitations & Blockers below): retrying a whole
  tool call inside an agent's reasoning loop would re-burn tokens already spent getting to that point,
  and the real failure modes observed live (a SerpAPI timeout, several `robots.txt` blocks) were
  already handled more cheaply by the prompt-level "move to the next result" fallback -- confirmed
  working in real runs (Phase 3/4 screenshots and scenario tests).
- [x] Explicit iteration cap set on Research Agent and Analyst Agent (rubric audit item 2, resolved
  2026-08-06), matching n8n's explicit `maxIterations: 5` on the same two nodes -- `max_iter: 25` in
  both `research_agent.jsonc` and `analyst_agent.jsonc`, previously commented out (implicit framework
  default). **Deliberately not set to a low number like n8n's 5:** real runs' tool-call counters were
  checked directly against the longest captured run (`burh5adcx.output`, crew `e1a5c51f`) and showed
  up to 14 `serpapi_search` calls alone, well past what a 5-10 cap would allow -- a low cap would have
  truncated already-verified-working behavior. `25` matches CrewAI's own framework default exactly,
  making the cap explicit/intentional (closing the audit gap about deliberate enforcement) with zero
  behavior change. Analyst Agent has no tools and always completes in one iteration regardless -- set
  for parity with n8n's pattern (which also set `maxIterations: 5` on its toolless Analyst Agent
  node), not because it changes anything functionally.
- [x] Integrate MCP tools + SerpAPI -- two custom tools built (`crewai/tools/serpapi_search.py`,
  `crewai/tools/mcp_fetch.py`), wired into Research Agent only (`"tools": ["custom:serpapi_search",
  "custom:mcp_fetch"]`), matching n8n's tool split (SerpAPI searches, MCP fetches/cites) exactly.
  `serpapi_search.py` mirrors `mcp-server/src/mcp_server/tools/search.py`'s SerpAPI call pattern for
  consistency. `mcp_fetch.py` wraps `crewai_tools.MCPServerAdapter` (verified via source, not
  assumed -- see below) to call this project's own MCP server's `fetch` tool per-call.
  - **Real dependency bug found and fixed:** `MCPServerAdapter` requires `mcpadapt`, which is not
    installed by `crewai[tools]` alone -- `crewai_tools` has its own separate `mcp` extra
    (confirmed via `Provides-Extra: mcp` in its package metadata) that had to be added explicitly
    (`crewai-tools[mcp]` in `crewai/pyproject.toml`). Without it, every `mcp_fetch` call failed
    silently (empty error message) and the run tried to interactively prompt to auto-install a
    package mid-run -- a real, confirmed gap, not a config mistake.
  - **`.env` gotcha, same shape as the OpenAI key issue:** `crewai run` only ever reads
    `Path.cwd()/.env` (verified directly from `crewai_cli/run_crew.py`'s source, no walk-up to parent
    directories) -- so `SERPAPI_API_KEY` had to be added to `crewai/.env` specifically, even though
    it already existed in the project root's `.env`. Confirmed harmless duplication, not sloppiness:
    this is a third-party CLI's fixed `.env` convention, not something to work around.

**3.3 Test & export**
- [x] Run end-to-end against the same fixed test brief used for n8n -- confirmed on a real run with
  real tool use: 5 SerpAPI searches (including one transient network timeout that recovered on retry,
  a nice live demonstration of the same source-volatility resilience n8n needed), multiple real MCP
  fetches, all four agents completed, real GTM plan produced. **Real cost: $0.3767** (186,158 prompt +
  51,893 completion tokens, 25 LLM requests) vs. n8n's $0.1104 for the same brief -- a first real data
  point for Phase 5, though not yet apples-to-apples: CrewAI's Research Agent made more search calls
  than n8n's capped 2, so this compares differently-scoped runs, not platform efficiency directly.
  - **`crewai run`'s Textual TUI dashboard can't be captured from a non-interactive/background
    process** -- its live dashboard renders via cursor-positioning ANSI codes with no plain-text
    fallback flag, and the actual result text and tool-error details only exist in an interactive
    scrollable panel, invisible in a raw captured log. Worked around by driving the `Crew` object
    directly via CrewAI's own Python API (`load_crew(...).kickoff(inputs=...)`) instead of the CLI,
    which uses plain verbose print output -- readable, capturable, and it's the same underlying
    execution path `crewai run` uses for a JSON crew, just without the CLI's dashboard wrapper.
- [x] Capture logs and debugging notes -- satisfied via prose in this document (Phase 3.2's five real
  bugs: nested git repo, package name collision, missing `mcpadapt` extra, per-tool `.env`
  requirement, uncapturable TUI; Phase 3.3's timezone-naive timestamp fix), matching the same
  no-raw-log-files-tracked precedent set by n8n's Phase 2.3.
- [x] Capture CrewAI chatbot screenshots -- 8 screenshots (`Phase3-01` through `Phase3-08`) from a
  second real end-to-end run (Crew ID `1743ba69-15b9-4ea9-8e8d-d3939a63ac8b`, total cost $0.211878,
  42.4% of the $0.50 cap), captured live in the user's own WSL terminal per the same live-run
  standard as n8n's Phase 2 screenshots (not reused from a background-captured log). Covers: Head
  Planner's questions, Research Agent's SerpAPI resilience (a real transient timeout that recovered)
  and MCP fetch (a real `robots.txt` block plus a real successful cited fetch), Research Agent's
  cited Final Answer, Analyst Agent's comparison table, Strategy Agent's GTM plan, Crew Completion,
  and the real run-log confirmation (`[INFO] logged crew run ... 4 rows appended`). Full details in
  `SCREENSHOTS.md`.
- [x] Save project files (uv structure) → `crewai/`
- [x] Emit run-log rows (same shared schema as n8n: `run_id, implementation=crewai, agent, timestamp, tokens_in, tokens_out, cost_usd, latency_ms, run_status`) to `comparison/run_logs/` -- solved via `crewai/run_and_log.py`, a permanent project script (supersedes the throwaway `run_crew_plain.py` diagnostic). Unlike n8n, no post-hoc REST ingestion was needed: CrewAI exposes per-agent token usage directly in-process via `agent.llm.get_token_usage_summary()` (called internally by `Crew.calculate_usage_metrics()`), and each `Task` has real `start_time`/`end_time` for latency -- simpler design than n8n's `ingest_execution.py`. One real gap found and fixed: `Task.start_time`/`end_time` are timezone-naive local-clock datetimes (verified in crewai's own `task.py`, bare `datetime.datetime.now()`), so `run_and_log.py` converts to UTC-aware (`.astimezone(timezone.utc)`) before logging, matching n8n's UTC-aware rows. Confirmed working on a real run (below).
- [x] Verified on two real end-to-end runs: 4 rows each appended to
  `comparison/run_logs/run_logs.jsonl`, schema-validated, all `run_status=success`.
  - Run 1: **$0.215656** total (Head Planner $0.008328, Research Agent $0.1868, Analyst Agent
    $0.010922, Strategy Agent $0.009506) -- 43.1% of the $0.50/run cap. Crew ID
    `e1a5c51f-0079-4acc-b037-94377913fe9a`.
  - Run 2 (also the screenshot-capture run, below): **$0.211878** total (Head Planner $0.004398,
    Research Agent $0.179429, Analyst Agent $0.015693, Strategy Agent $0.012358) -- 42.4% of the
    $0.50/run cap. Crew ID `1743ba69-15b9-4ea9-8e8d-d3939a63ac8b`.

**Exit criteria:** same test brief as Phase 2 produces a comparable GTM doc (**met**); run-log rows emitted (**met**); screenshots captured (**met**).

**Phase 3 is now fully complete.** Next up: Phase 4 (Testing) and Phase 5 (`comparison/compare.py`).

---

## Phase 4 — Testing

- [x] Unit tests: mocked SerpAPI/MCP/Docs tool I/O.
  - **SerpAPI:** `mcp-server/tests/test_search.py` (Phase 1, mocks `requests.get`) +
    `crewai/tests/test_serpapi_search.py` (new -- mocks `requests.get` for the CrewAI-side
    `SerpApiSearchTool`, covers formatted results, missing-API-key error, and empty-results message).
  - **MCP:** `mcp-server/tests/test_fetch.py`/`test_cache.py` (Phase 1, mocked I/O) +
    `crewai/tests/test_mcp_fetch.py` (new -- mocks `MCPServerAdapter`'s context-manager protocol for
    the CrewAI-side `McpFetchTool`, covers default and custom `MCP_SERVER_URL` handling).
  - **Docs:** not applicable -- Google Docs export is entirely a native n8n node (`Docs Writer -
    Create a document` / `Docs Writer - Insert Content`), not custom Python code, so there is no
    Python-side Docs tool I/O to unit test. n8n's own per-node execution testing (Phase 2.3, "Execute
    Node testing per node") is the equivalent coverage for that piece.
  - Added `pytest>=9.1.1` as a `crewai/pyproject.toml` dev dependency, matching the existing
    `mcp-server`/`log_server` convention exactly (`[dependency-groups] dev = [...]`). All 5 new tests
    pass (`uv run pytest`, `crewai/`), no warnings.

- [x] Scenario tests: fixed briefs with golden expected outputs, run against both implementations.
  Two new briefs beyond the primary one, each with a loose golden-fact checklist (does the output
  name real, correct competitors; does it describe a sensible target customer) rather than exact
  text matching -- appropriate rigor for this project's academic-scope proof-of-concept, not a
  production regression suite.
  - **Brief A (smart water bottle):** "A new smart water bottle that tracks hydration, aimed at
    on-the-go fitness enthusiasts. Who's the target customer and who are the main competitors?"
    Golden facts: target customer = fitness/health-conscious adults; >=2 of {HidrateSpark, Hydro
    Flask, LARQ, Nomader} named.
    - n8n: target customer matched ("US 18-34 fitness doers... wellness-minded young
      professionals"). Competitors: 1 of 4 golden-list matches (HidrateSpark), plus Ulla (a real
      competitor not on the pre-written list) -- **partial match** on the strict "2 named" bar.
      Cost $0.053925.
    - CrewAI: target customer matched ("U.S.-based Millennials/Gen Z (18-40) on-the-go fitness
      enthusiasts"). Competitors: 3 of 4 golden-list matches (HidrateSpark, Thermos, LARQ) --
      **full match**. Cost $0.137965.
  - **Brief B (subscription meal-kit service):** "A new subscription meal-kit service targeting busy
    young professionals. Who's the target customer and who are the main competitors?" Golden facts:
    target customer = busy working adults, roughly 25-44; >=2 of {HelloFresh, Blue Apron, Home Chef,
    Factor, EveryPlate} named.
    - n8n: target customer matched ("Urban, college-educated 22-35-year-olds... busy 22-35s").
      Competitors: 1 of 5 golden-list matches (HelloFresh, via "HelloFresh alternative" positioning)
      -- **partial match**. Cost $0.071787.
    - CrewAI: target customer matched ("Full-time employed U.S. adults aged 25-34... busy
      professionals"). Competitors: 5 of 5 golden-list matches, in a real sourced comparison table
      (HelloFresh, EveryPlate, Factor, Home Chef, Blue Apron), plus Green Chef, Marley Spoon,
      Dinnerly, Sunbasket named too -- **full match, exceeds bar**. Cost $0.122994.
  - **Honest finding, not spun:** both implementations reliably identify a sensible target customer
    across both new briefs (4/4). Named-competitor coverage is asymmetric: CrewAI's dedicated Analyst
    Agent step (a real sourced comparison table as its own task) consistently surfaces more named,
    correct competitors than n8n's Strategy Agent output alone captured in this test. This may
    reflect a genuine architectural difference (a distinct synthesis task vs. folding competitor
    detail into the final GTM plan step) rather than a model-capability gap -- worth noting in the
    final comparison writeup (Phase 5), not just this test result.

- [x] Reproducibility check: 3 reruns of the primary fixed brief per implementation, checking
  fact/cost consistency (target: >=80% consistency).
  - **n8n** (executions 49, 50, 51): target customer/ICP theme consistent across all 3 runs (urban,
    budget-conscious commuters wanting ANC/clear calls/comfort) -- **100% on the core theme**, though
    the specific age bracket varied per run (25-44; unspecified/"students"; 25-34), normal LLM
    run-to-run variance rather than a system failure. Cost: $0.042604 / $0.054443 / $0.051915 (avg
    $0.0497, a relatively tight spread).
  - **CrewAI:** the 2 real full-text runs available on this brief (Phase 3.3's `e1a5c51f` and
    `1743ba69`) both name **Soundcore/Anker, JBL, and TOZO** as competitors -- 100% consistent on
    those three brands across both, though the target age bracket varied (19-29 vs. 25-44), the same
    kind of variance seen in n8n. Cost across all 5 real runs on this brief this session ($0.215656,
    $0.211878, $0.087332, $0.143938, $0.127546) is notably more variable than n8n's (avg ~$0.157,
    range $0.087-$0.216) -- plausibly because Research Agent's tool-calling loop is less tightly
    bounded than n8n's capped search count, so some runs simply do more searches than others.
  - **Known data-collection limitation, disclosed rather than hidden:** the 3 new n8n reruns
    (executions 49-51) only had the Strategy Agent's final output captured, not the Analyst Agent's
    own competitor table (unlike CrewAI, where the full per-agent output was captured for its 2
    reference runs). This means n8n's named-competitor consistency isn't scored here at the same
    granularity as CrewAI's -- an asymmetry in this test's evidence, not a claim that n8n is less
    consistent. Target-customer-theme consistency (the piece with symmetric data for both) is 100%
    for both implementations, which is the strongest evidence available from this round of testing.

- [x] Human rubric review: clarity, feasibility, differentiation (target >=4/5), scored by the user
  against the primary brief's already-captured outputs (n8n's `Phase2-08`, CrewAI's `Phase3-06`/`07`).
  - **n8n:** clarity 4, feasibility 4, differentiation 5 -- **avg 4.33**, exceeds the 4/5 target.
  - **CrewAI:** clarity 4, feasibility 5, differentiation 4 -- **avg 4.33**, exceeds the 4/5 target.
  - Honest read: both implementations score essentially identically overall, each strongest on a
    different criterion (n8n on differentiation, CrewAI on feasibility) -- worth carrying this
    even-handed result into Phase 5's comparison rather than declaring either a clear winner.

**Exit criteria:** unit tests passing (**met**, 5 new CrewAI tests + existing mcp-server/log_server
suites); scenario tests run against both implementations with golden-fact checks (**met**);
reproducibility check on the primary brief for both implementations (**met**, with the n8n
competitor-data-capture asymmetry disclosed above); human rubric review scored (**met**, both
implementations avg 4.33/5, exceeding the target). **Phase 4 is now fully complete.**

---

## Phase 5 — Comparison (n8n vs. CrewAI)

- [x] Build `comparison/compare.py`: reads `comparison/run_logs/run_logs.jsonl` (shared schema, both
  implementations already writing to it) and computes cost, latency, and reliability/error-rate
  stats. Pure stdlib (`json`, `pathlib`, `statistics`, `dataclasses`) -- no new dependency, matching
  `log_server`'s existing stdlib-first convention. Tested: `comparison/tests/test_compare.py`, 5
  tests, all passing (grouping logic, per-run totals, success-rate math).
- [x] `compare.py` writes `comparison/report.md` with the comparison tables -- plain script, no
  notebook, no chart images (kept to tables only; the optional chart-image option in this checklist
  item wasn't exercised, matching this project's lean academic-scope convention -- easy to add later
  if wanted).
- [x] Cost per run (both implementations, same test brief) -- **real finding:** n8n avg **$0.0642**/run
  (6 runs, range $0.0426-$0.1104) vs. CrewAI avg $0.1379/run (9 runs, range $0.0843-$0.2156). n8n is
  roughly 2.1x cheaper on average, consistent with n8n's Research Agent tool-call count being tightly
  capped vs. CrewAI's more open-ended tool-calling loop.
- [x] Latency per run -- **real finding:** n8n avg **1m 59.4s**/run vs. CrewAI avg 6m 39.0s/run (both
  are the sum of each run's per-agent/node latency, a wall-clock proxy -- see `compare.py`'s Notes).
  CrewAI's Research Agent step alone often runs several minutes longer than n8n's capped-search
  equivalent, the same underlying driver as the cost gap above.
- [x] Reliability/error rate across repeated runs -- **real finding:** 100% run-level and row-level
  success rate for both implementations across all 15 currently logged runs (72 agent/node rows).
  Honestly caveated in the report: real tool-level failures did occur and were observed/recovered
  during testing (a SerpAPI read-timeout, several `robots.txt` blocks -- see Phase 2/3/4 above), but
  none were severe enough for an agent/node to log `run_status="error"` -- the fallback/resilience
  design in both implementations absorbed them before they became a logged failure.

**Exit criteria:** `compare.py` runs against real data from both implementations and produces
`comparison/report.md` with cost, latency, and reliability tables (**met**). **Phase 5 is now fully
complete.**

---

## Rubric Audit (Phases 0-5 vs. `documentation/1762856365_capstoneprojectproblemstatement.md`)

Full audit performed 2026-08-06, cross-checking every discrete requirement in the rubric against
actual files on disk (not against ROADMAP's own self-reported checkmarks, and not against memory).
Covers everything except Phase 6, which hasn't started yet.

### Confirmed met (verified against real files)

- Four-agent system, both implementations, matching roles.
- n8n node chain matches exactly: Trigger -> Head Planner -> Research Agent -> Analyst Agent ->
  Strategy Agent -> Docs Writer (Create + Insert).
- MCP tools + SerpAPI integrated in both implementations, Research Agent only.
- MCP tools tested with `curl` (full handshake, `tools/list`, `tools/call`, both tools) -- line 54
  above, commands in `SETUP.md`.
- n8n nodes tested with Execute Node (Phase 2.3); CrewAI tasks tested end-to-end (Phase 3.3/4).
- Unit tests: mocked SerpAPI + MCP, both implementations. "Docs" correctly scoped n/a -- no Python
  code exists for Google Docs export, it's a native n8n node with no unit-testable surface.
- Scenario tests, human rubric review, cost/latency/reliability comparison -- all done (Phase 4/5).
- Citations in JSON format with evidence IDs (`citation_id`, `url`, `source_tool`, `fetched_at`).
- Competitor comparison tables with qualitative synthesis, explicitly instructed as "SWOT-style
  observations" in both implementations' Analyst Agent prompts (`crew.jsonc` line 44,
  `analyst_agent.jsonc` line 11, n8n workflow JSON line 126) -- confirmed present in real outputs.
- Structured GTM plan sections (ICP, value proposition, messaging/channels, launch plan) in every
  real GTM plan output, both implementations.
- Source volatility risk: caching, snapshots, timestamps -- real, encountered live, recovered.
- Cost overruns risk: budget caps -- real, confirmed with data. Token limits: n8n has explicit
  `maxIterations: 5` on its two tool-using agents.
- Logging + cost/latency tracking, both implementations, real data.
- Retries: n8n has "Retry On Fail" on the two nodes that support it (Docs Writer x2); the AI-tool
  sub-nodes (SerpAPI, MCP Client) don't expose the setting at all -- a documented, verified n8n
  platform limitation, not a gap.

### Real gaps found -- resolved 2026-08-06, user interviewed on all four

1. **README's Risk & Mitigations table over-claims three mitigations not actually implemented.**
   **Decision: correct the wording to describe real implementation state.** Fixed in `README.md`'s
   Risk & Mitigations table (API rate limits, Hallucinations, Formatting drift, Cost overruns rows
   rewritten to state what's actually built, not rubric-aspiration language). No code change --
   documentation accuracy only.
2. **CrewAI's `max_iter` was commented out/unconfigured on all four agents.**
   **Decision: set explicitly on the two tool-using agents.** `max_iter: 25` set on
   `crewai/agents/research_agent.jsonc` and `crewai/agents/analyst_agent.jsonc` (the two agents with
   real tools). Set to 25 -- the framework default -- rather than a lower number like n8n's `5`,
   after checking real prior runs used up to ~18-20 tool-call iterations (`burh5adcx.output`, crew
   `e1a5c51f`); a lower cap would have truncated already-verified-working behavior. `head_planner`
   and `strategy_agent` left untouched (`"tools": []`, no iteration loop to cap, matching n8n's
   pattern of not setting `maxIterations` on its non-tool-using nodes either).
3. **CrewAI's retry design decision wasn't documented in ROADMAP.md.** **Decision: document it.**
   See Phase 3.2 above -- `max_retry_limit` is deliberately left commented out, mirroring n8n's
   decision not to enable Retry On Fail on its AI Agent nodes, both for the same reasoning (retrying
   a whole agent reasoning loop would re-burn tokens already spent in the loop).
4. **CrewAI's "interim outputs" weren't retained as files.** **Decision: wire up `Task.output_file`.**
   Added `output_file` + `create_directory: true` to all four tasks in `crew.jsonc`
   (`outputs/1_head_planner.md` through `outputs/4_strategy_agent.md`). `crewai/outputs/` added to
   `.gitignore` (regenerated fresh each run, not source -- same pattern as `mcp-server/.cache/` and
   `comparison/run_logs/`).

**Verification run (2026-08-06, crew `ee5b2e8c`):** ran the crew end-to-end for real after all four
code changes to confirm they work, not just that the config parses. Exit code 0. All four
`outputs/*.md` files created with real content. Cost: $0.539 total (Head Planner $0.0085, Research
Agent $0.5044, Analyst $0.0102, Strategy $0.0159) -- above the prior 9-run CrewAI range
($0.0843-$0.2156) and above the README's stated $0.50/run guideline. Per user direction, the
$0.50 figure is a soft guideline, not a hard gate -- this run is noted as a cost outlier (likely
natural variance in how many searches the Research Agent chose to run, not caused by the `max_iter`
change itself, since 25 was already the framework default before being made explicit) and is not
treated as a blocking regression. The row is already appended to `comparison/run_logs/run_logs.jsonl`
via `run_and_log.py`'s normal logging path; Phase 5's `report.md`/README KPI figures (9-run average
$0.1379, range $0.0843-$0.2156) were not regenerated, since this was a post-gap verification run,
not a new formal Phase 5 benchmark pass.

### Judgment calls -- resolved 2026-08-06, user interviewed on all three

5. **"Chain tasks with CrewAI Flows for hand-offs"** (rubric Action 2.2) -- this project uses
   CrewAI's standard `Crew` + sequential `Process`/`Task` chaining, not the distinct `Flow` class/
   API (`@start()`/`@listen()`). **Decision: keep as-is.** The substantive requirement (ordered
   agent hand-offs) is fully met by sequential Process/Task chaining; rearchitecting to the literal
   Flow API this late was judged a real architectural change for what's likely just terminology,
   not a functional gap. No code change.
6. **"Generate ... pricing matrices"** (rubric Tasks section) -- competitor tables include a price
   range column woven in, but no separate dedicated pricing matrix artifact exists. **Decision:
   keep as-is.** The existing price column reasonably satisfies this; a separate pricing matrix
   would be redundant with data already shown. No code change.
7. **"Export the plan to Google Docs, with PDF option"** (rubric Tasks section) -- Google Docs
   export is real; PDF is not implemented. **Decision: keep as-is, optional.** Matches `README.md`'s
   existing scoping and both deliverables lists (Tasks section, Result section), neither of which
   names PDF as required -- only "Sample Google Doc output." No code change.

**All 7 audit items (4 real gaps + 3 judgment calls) are now resolved.** Rubric audit complete.

---
## >>> RESUME: PHASE6-START (session paused 2026-08-06) <<<
Type "resume PHASE6-START" to pick up exactly here.

State at pause:
- Phase 0 through Phase 5 are all fully complete. Full rubric audit complete (see "Rubric Audit"
  section directly above) -- all 7 items (4 real gaps, 3 judgment calls) resolved with user
  sign-off via two AskUserQuestion interviews. End-to-end verification run confirms the gap-4/gap-2
  code changes (`output_file`, `max_iter: 25`) actually work, not just parse.
- **Not yet committed/pushed:** `crewai/agents/research_agent.jsonc`, `crewai/agents/analyst_agent.jsonc`,
  `crewai/crew.jsonc`, `.gitignore`, `README.md`, `SETUP.md` -- all the gap-remediation changes from
  this audit. (`ROADMAP.md` itself is git-ignored, never committed.)
- Next: commit + push the above, then proceed to Phase 6 (Documentation & Submission Packaging):
  finalize `README.md`, save a sample Google Doc output to `outputs/`, confirm all five deliverables
  present.
---

## Phase 6 — Documentation & Submission Packaging

- [x] README finalized with architecture, setup, and testing notes -- already substantively
  complete (Architecture, Prerequisites -> `SETUP.md`, Testing strategy, real n8n-vs-CrewAI
  comparison data baked into the KPI table from `comparison/report.md`); top status banner and
  the stale `outputs/` note in Repository structure corrected 2026-08-06 to reflect Phase 6
  completion.
- [x] Sample Google Doc output saved → `outputs/sample_gtm_plan_n8n.md` -- real content
  transcribed from the actual Google Doc produced in Phase 2.3 (`screenshots/Phase2-08`, doc
  title `GTM Plan - 2026-08-03T13:54:31.220-04:00`, cross-confirmed against the Drive listing in
  `Phase2-07`). Did **not** trigger a fresh n8n run for this: `n8n execute --id <id>` was tried
  first but conflicts on port 5679 with the user's own already-running n8n instance (PID 7235, a
  separate live terminal session, not one this session started) -- stopping someone else's live
  process to force a new run wasn't worth it when Phase 2.3 already produced and fully verified a
  real sample. `outputs/` created fresh (did not exist before).
- [x] All five (now six, with the reflection doc) deliverables from the assignment confirmed
  present -- see README's Deliverables checklist, all boxes now checked.
- [x] Reflection document (`.docx`/`.pdf`) -- built 2026-08-06, see "Reflection Document"
  subsection below. Personal Reflections (Section 7) was drafted from real project history; the
  user should still confirm it reads as their own voice before final submission, but no
  in-document draft marker remains (one was mistakenly added, then removed -- see that
  subsection's note).
- [x] Submission package assembled -- `submission/writeup.zip`, `submission/screenshots.zip`,
  `submission/source_code.zip`, matching the portal's three required upload slots. See
  "Submission Package" subsection below.

### Reflection Document

Standard VT AGI Post-Graduate Program per-project submission requirement (not part of this
project's own rubric), matching the pattern from two prior course projects
(`documentation/patterns_carried_over_from_prior_VT_projects.md` line 13).

**2026-08-06: audited `reflection/` and found it holds a different prior project's finished
document, not this project's.** `reflection.docx`/`reflection.pdf`, `STYLE_GUIDE.md`, and
`notes.md` all describe a *different* VT course project (LangGraph-based Research
Agent/Funding Advisor/Pitch Coach pitch tool, Azure Application Insights, fintech/vertical-
farming/telehealth domains) -- carried over intentionally as a **format/structure reference**,
not as content to reuse. `generate_diagrams.py`/`generate_reflection.py` (python-docx/matplotlib
tooling) are real, reusable code, not yet adapted to this project's content.

The true original reference document (cleanest format template, plain markdown, no foreign
content) is `documentation/other_projects/reflection-final.md` -- an n8n+FastAPI LinkedIn
automation project's reflection doc: 8 sections (Overview, Architecture, Design Decisions,
Challenges and Resolutions, Trade-offs table, Conclusion, Personal Reflections, Build Walkthrough
screenshots), figure-caption format `**Figure N -- Title**` followed by a plain-text explainer,
footer `<Course> | <Author> | <Date>`.

This project's own real source material for the new document:
- **Logos** already in place: `screenshots/logos/{Virginia_Tech,simplilearn,Microsoft}.jpg`.
- **24 real screenshots** already captured and fully written up in `SCREENSHOTS.md`: Phase 0
  (Google Cloud/OAuth setup, 7 files, `Phase0-07` intentionally skipped), Phase 2 (n8n
  implementation, 9 files), Phase 3 (CrewAI implementation, 8 files). No screenshots yet from
  Phase 1 (MCP server), Phase 4 (testing), Phase 5 (comparison), or Phase 6 itself.
- **README.md** and this file (`ROADMAP.md`) hold the full design-decision/challenge/trade-off
  narrative already (rubric audit, framework choices, CVE-driven MCP-server design, n8n platform
  limitations, cost/latency KPIs) -- usable as source material for Sections 3-6, unlike the prior
  project which had to capture that narrative fresh in a running `notes.md`.
- **Not yet available anywhere:** genuine first-person "Personal Reflections" content (Section 7)
  -- this needs real input from the user, not fabricated prose, matching how both prior reference
  documents handle that section (direct, first-person, unguarded voice).

**Decisions (interviewed via AskUserQuestion, all "Recommended" options chosen):**
1. Custom diagrams -- built, matching both prior projects' format.
2. New dependencies approved -- `python-docx` + `matplotlib` in a new, separate
   `reflection/requirements-reflection.txt`, isolated from `crewai/pyproject.toml` and
   `mcp-server/pyproject.toml`.
3. Screenshot coverage scoped to Phase 0/2/3 (24 files) for this pass -- Phases 1/4/5/6 covered
   in the narrative sections' prose instead, not left as a blocker.
4. Personal Reflections (Section 7) -- the user asked for this to be drafted rather than composed
   from scratch (fatigue signal mid-session, see the harness's own memory system note on this).
   Drafted from the project's real documented history, clearly marked `[DRAFT]` inside the
   document itself, for the user to edit/approve before final submission.

**2026-08-06: built.** `reflection/generate_diagrams.py` rewritten for this project's real
architecture (this project's own `Color_codes.md` palette, VT Chicago Maroon `#630031` -- not the
prior project's inherited `#861F41`, which was an artifact of the copied template, not a
deliberate choice for this document): `diagrams/diagram_workflow.jpg` (the shared four-agent
chain, tool layer, and per-node run-log annotation) and `diagrams/diagram_swimlane.jpg` (three
lanes -- n8n Implementation, Shared MCP Server + SerpAPI, CrewAI Implementation -- converging on
the shared `run_logs.jsonl` schema). `reflection/generate_reflection.py` rewritten with this
project's real content: Sections 1-6 drawn from `README.md`/`ROADMAP.md`'s actual design
decisions, challenges (n8n token-usage gap, the stuck search-tool loop, the Source-for-Prompt
node-config gotcha, the rubric audit itself), and real KPI data (`comparison/report.md`); Section
7 drafted as described above; Section 8 uses all 24 real Phase 0/2/3 screenshots, captions
condensed from `SCREENSHOTS.md`.

Environment note: `python3-venv` isn't installed in this WSL2 instance and there's no passwordless
`sudo` to install it, so the isolated environment was created with `uv venv` instead (already the
project's own toolchain elsewhere). PDF conversion used Windows-side Microsoft Word via COM
automation (`Documents.Open` -> `SaveAs(wdFormatPDF)`), since neither LibreOffice nor `docx2pdf`
is available in this WSL2 instance -- unlike the prior project, which had no working PDF path at
all and shipped `.docx` only.

**Verified**, not just generated: `python-docx` structural check (22 headings across the correct
8 top-level sections, 29 inline images -- 3 logos + 2 diagrams + 24 screenshots -- zero `[WARN]`
missing-file lines), Word COM page count (18 pages), and visual spot-check of 4 rendered PDF pages
(title page, Figure A/B captions, a mid-document screenshot page, the final page) via `pymupdf`
page rendering -- logos, footer, pagination, and figure captions all confirmed correct.

**Files:** `reflection/reflection.docx`, `reflection/reflection.pdf` (both git-ignored, local
only, matching the whole `reflection/` folder). `reflection/diagrams/` (new subfolder, kept
separate from the tracked root `outputs/` folder so reflection-only assets never mix with actual
graded deliverables). `reflection/.venv-reflection/` (isolated tooling venv, disposable/
regenerable via `uv venv` + `uv pip install -r requirements-reflection.txt`).

**Correction, same day:** the first version of Section 7 included a bracketed in-document note
("[DRAFT -- ... please read, edit freely ... before this is submitted]") addressed to the user.
The user caught this and was rightly angry -- meta-commentary about a document's drafting status
does not belong inside the document itself, regardless of intent. Removed immediately, both
`.docx` and `.pdf` rebuilt, and a permanent rule saved to the harness's memory system (never add
unrequested content to a deliverable; always ask first). A second borderline case (an explanatory
note inside a figure caption about the `Phase0-07` numbering gap) was raised to the user
explicitly rather than decided alone, and removed per their answer.

### Submission Package

Built 2026-08-06, after reviewing the rubric's Result/Deliverables section again and matching it
against the actual submission portal's three upload slots (Writeup, Screenshots, Source Code,
each with an unstated-but-implied 10 MB cap per the portal's own "file size shouldn't exceed
10 MB" note; a fourth field, Additional Remarks, caps at 1200 characters).

All four open questions were interviewed via AskUserQuestion rather than decided independently,
given the stakes (this directly determines graded-submission content):

1. **Writeup contents:** `reflection.pdf` only (not `.docx`, not both) -- smallest, most portable,
   leaves headroom under the cap.
2. **Sample Google Doc output placement:** bundled into Source Code (`outputs/`), since the
   portal has no dedicated slot for this rubric-required deliverable.
3. **Source Code scope:** everything -- n8n export, `crewai/`, `mcp-server/`, `comparison/`,
   `README.md`/`SETUP.md`.
4. **Additional Remarks:** drafted by Claude for the user's review, not left blank.

Two further judgment calls, also interviewed rather than assumed, since both touch files that had
been deliberately git-ignored/local-only all project long:

5. **`ROADMAP.md` in Source Code:** included -- it's the only place with the detailed "test runs
   and error resolutions" narrative the rubric explicitly asks for; staying off GitHub doesn't
   have to mean staying out of the graded submission.
6. **`comparison/run_logs/run_logs.jsonl` in Source Code:** included -- real per-run data backing
   every KPI number cited in README/the reflection doc, not just the aggregated summary in
   `comparison/report.md`.

**Built via a one-off script** (`build_submission.py`, scratchpad only, not part of the tracked
repo) using Python's stdlib `zipfile`, with an explicit exclude list (`.venv/`, `__pycache__/`,
`.pytest_cache/`, `.cache/`, `node_modules/`, `.git/`, plus exact/pattern secret-file matching:
`.env`, `*.env`, `client_secret*.json`, `*credentials*.json`) applied while walking each source
tree, followed by a post-build safety pass that opens every produced zip and re-checks every
entry's filename against the same secret patterns before declaring success. This caught and
correctly excluded `crewai/.env` (a real, live secrets file sitting inside `crewai/`, protected by
the root `.gitignore`'s `.env`/`*.env` patterns already, but exclusion needed to be re-verified
independently for the zip-building path rather than assumed from `.gitignore` alone).

**Results, all well under the 10 MB cap:**

| Zip | Size | Contents |
|---|---:|---|
| `submission/writeup.zip` | 1.56 MB | `reflection.pdf` |
| `submission/screenshots.zip` | 7.63 MB | 24 build-walkthrough screenshots, `logos/` (3 partner logos + its own README), `SCREENSHOTS.md` as an index (29 files total) |
| `submission/source_code.zip` | 0.32 MB | n8n export, `crewai/` (agents, tools, tests, `outputs/`), `mcp-server/` (src, tests), `comparison/` (compare.py, report.md, `log_server/`, `run_logs/run_logs.jsonl`), `README.md`, `SETUP.md`, `ROADMAP.md`, `.env.example`, `outputs/sample_gtm_plan_n8n.md` (56 files total) |

**`.gitignore`:** added `submission/` -- packaging output regenerated from tracked source, not
itself source, same category as `crewai/outputs/` and `mcp-server/.cache/`.

**Not yet done:** the user still needs to manually upload the three zips through the portal UI
(no API access to that portal exists), and review/paste the drafted Additional Remarks text before
submitting -- both are outside what Claude can do directly.

---

## Open Questions

Resolved during initial planning:

- ~~Dev environment~~ → WSL2, Ubuntu 24.04.4 LTS, local (no VM)
- ~~LLM provider~~ → OpenAI `gpt-5` baseline (switched from `gpt-4.1-mini`, which had itself replaced an initial `gpt-4o-mini` proposal); Claude Haiku 4.5 optional stretch comparison
- ~~Google Docs auth~~ → OAuth user-consent using a personal Google account (details kept out of documentation), both implementations local
- ~~Chatbot screenshots~~ → CLI-based (e.g. `crewai chat`) for now
- ~~Timeline~~ → No hard deadline; course-end project for the VT Applied Agentic AI Post-Graduate Program, paced at your discretion

- ~~Reference projects~~ → `documentation/other_projects/` (git-ignored, local only): a LangGraph pitch-deck planner and an n8n+FastAPI LinkedIn PRD. Neither uses CrewAI or MCP, so they contribute conventions (logging, testing, secrets handling), not portable code.
- ~~Git~~ → local repo initialized, merged with the existing GitHub initial commit (`LICENSE` + placeholder `README.md`) via `--allow-unrelated-histories`, and pushed to `origin/main`.
- ~~Python approach (notebooks vs. modular)~~ → fully modular `.py` throughout, no Jupyter notebooks anywhere in the repo, including the n8n-vs-CrewAI comparison (`comparison/compare.py`, not a notebook). See README's Repository-structure note for the shared run-log schema this depends on.
- ~~Where Python code runs (WSL vs. Windows working directory)~~ → developed/run from this same project folder via WSL's `/mnt/d/...` mount, not a separate WSL-native clone. Same git repo either way; `git push` from WSL goes straight to GitHub, no extra step to move code out of WSL. See SETUP.md's "Important environment caveats" for the accepted I/O-speed tradeoff.
- ~~MCP server choice~~ → adapted the official reference `fetch` server rather than building from scratch or using an unverified off-the-shelf bundle; added a custom `search` tool (SerpAPI) plus a citation/caching layer; real MCP protocol over SSE so both n8n and CrewAI connect natively. See Phase 1 above.

Resolved with real data:

- ~~Budget cap number~~ → **decided: $0.50 per end-to-end run, per implementation** (tightened down
  from the original $1.00 proposal, which was based on `gpt-4.1-mini` pricing -- a cheap "mini" tier
  model long since replaced by flagship `gpt-5`, at $0.63/M input / $5.00/M output tokens). Real data
  behind the decision:
  - n8n: **$0.1104** total for one complete run (Head Planner $0.000357, Research Agent $0.104587 --
    dominant cost, 164,353 prompt tokens across a 4-iteration tool loop -- Analyst Agent $0.002806,
    Strategy Agent $0.002648, both Docs Writer steps $0). **22% of the $0.50 cap -- passes with
    substantial room to spare.**
  - CrewAI: **$0.3767** total for one complete run (186,158 prompt + 51,893 completion tokens, 25 LLM
    requests). **75% of the $0.50 cap -- passes, but with much less headroom than n8n.** Not yet an
    apples-to-apples comparison against n8n's figure, though: CrewAI's Research Agent made 5 real
    SerpAPI searches in that run vs. n8n's hard cap of 2 (one per question), so part of the gap is
    scope, not pure platform overhead -- worth re-examining once Research Agent's search budget is
    tightened to match n8n's, or once repeat runs establish whether 5 searches is typical or a
    one-off.
  - **This is a real, useful finding for Phase 5's comparison, not a problem to hide** -- both
    implementations pass the cap, but with a meaningfully different margin (22% vs. 75% of budget
    used), giving the n8n-vs-CrewAI comparison something concrete to measure and explain, rather than
    both trivially passing a loose $1.00 ceiling.
