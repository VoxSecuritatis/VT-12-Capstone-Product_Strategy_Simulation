# Environment Setup

This file records the actual toolchain installed and verified for this capstone, with exact versions, locations, and the commands used to obtain/verify each one. It complements `README.md`'s Prerequisites (which states what's needed) by recording the as-built state.

Environment: WSL2, Ubuntu 24.04.4 LTS, on Windows.

## Summary

| Tool | Version | Location | Purpose |
|---|---|---|---|
| WSL2 | 2.7.3.0 | Windows host | Linux environment hosting n8n, Python, MCP server |
| Ubuntu | 24.04.4 LTS | WSL2 distro | Base OS |
| Python (WSL) | 3.12.3 | `/usr/bin/python3.12` (symlinked as `/usr/bin/python3`) | CrewAI project runtime, MCP server |
| uv | 0.12.1 | `~/.local/bin/uv`, `~/.local/bin/uvx` | Python package/project manager (uv-structured CrewAI project per rubric) |
| Python (Windows) | 3.12.10 | `D:\Python312\python.exe` | Base interpreter for the Windows-side project `.venv` |
| `.venv` (Windows) | 3.12.10 | `.venv\` in project root | Local Windows-side virtual environment, modeled on `D:\Python312`; git-ignored |
| nvm | 0.40.6 | `~/.nvm` | Node.js version manager |
| Node.js | 24.18.0 | `~/.nvm/versions/node/v24.18.0/bin/node` | n8n runtime |
| npm | 11.16.0 | bundled with the above Node.js install | Package manager used to install n8n |
| n8n | 2.27.4 | `~/.nvm/versions/node/v24.18.0/bin/n8n` | Workflow orchestration (one of the two required implementations) |
| `.env` / `.env.example` | n/a | project root | Secrets (`.env`, git-ignored, never read/written directly) and their variable-name template (`.env.example`, tracked) |
| `mcp-server` (uv project) | 0.1.0 | `mcp-server/` | Shared MCP server (search + fetch + citation/caching), adapted from the official reference `fetch` server |
| `log_server` (uv project) | 0.1.0 | `comparison/log_server/` | Local HTTP endpoint (`POST /log`) that appends run-log rows to the shared `comparison/run_logs/run_logs.jsonl` file |
| `n8n-nodes-serpapi` (n8n community node) | 0.1.10 | installed via n8n Settings -> Community Nodes | Native SerpAPI Google Search tool node (`SerpApi Official`), used by the Research Agent alongside MCP's `fetch` tool |
| `crewai` (uv project) | 0.1.0 (`vt-capstone-gtm-crew`) | `crewai/` | CrewAI implementation: four agents (Head Planner, Research, Analyst, Strategy), JSON-first scaffold, built via `crewai create crew` |
| `compare.py` | n/a (plain script) | `comparison/compare.py` | Reads `comparison/run_logs/run_logs.jsonl` (shared schema) and writes `comparison/report.md` with cost/latency/reliability comparison tables for both implementations |

## Per-tool detail

### WSL2 + Ubuntu
- **What:** Windows Subsystem for Linux, running an Ubuntu 24.04.4 LTS distro. Hosts everything below.
- **Obtain:** `wsl --install` from an elevated PowerShell (Microsoft's standard installer); already provisioned here.
- **Verify:** `wsl --version` (from PowerShell); `lsb_release -d` (inside WSL).

### Python (WSL) 3.12.3
- **What:** CPython interpreter. Ships preinstalled with Ubuntu 24.04 LTS — no install step was needed.
- **Obtain (if ever missing):** `sudo apt install python3`, or `uv python install 3.12` to have `uv` manage it instead.
- **Verify:** `python3 --version`

### Python (Windows) 3.12.10 + project `.venv`
- **What:** a separate, existing Windows-side Python 3.12.10 install at `D:\Python312`, used as the base interpreter for this project's Windows-side virtual environment (`.venv` in the project root). Distinct from the WSL Python above.
- **Obtain:** `.venv` created with `D:\Python312\python.exe -m venv .venv` from the project root.
- **Verify:**
  ```powershell
  .venv\Scripts\python.exe --version
  Get-Content .venv\pyvenv.cfg
  ```
- Git-ignored (`.venv/` in `.gitignore`).

### run.ps1
- **What:** creates the Windows-side `.venv` from `D:\Python312` if missing, dot-sources `.venv\Scripts\Activate.ps1` to genuinely activate it (`$env:VIRTUAL_ENV` set, `python`/`pip` resolve to the venv), upgrades `pip`, installs/updates from `requirements.txt`, then launches `main.py`. Same pattern as the prior FinEdge project's `run.ps1`.
- **Run:** `.\run.ps1` from the project root. Local-only, git-ignored (not part of the public repo).
- **Note:** `requirements.txt` and `main.py` don't exist yet (no CrewAI scaffolding has been built), so the last two steps currently fail with a plain "file not found" error — expected until Phase 3 scaffolds the CrewAI project.
- **Activation scope:** because environment variables in PowerShell are process-wide (not scoped like regular variables), running `.\run.ps1` leaves `$env:VIRTUAL_ENV`/`$env:PATH` activated in your current shell even without dot-sourcing the script itself. The one thing that does require dot-sourcing the outer script (`. .\run.ps1`) is the `(.venv)` prompt-prefix visual indicator, since that's a PowerShell function definition, which is scoped.

### uv 0.12.1
- **What:** Rust-based Python package/project manager. Used to scaffold and manage the CrewAI project (the rubric requires "UV structure").
- **Obtain:** `curl -LsSf https://astral.sh/uv/install.sh | sh` (installs to `~/.local/bin`; a new shell picks it up on PATH automatically).
- **Verify:** `uv --version`
- **Test (installs a real package end-to-end):**
  ```bash
  uv venv /tmp/uv_test
  uv pip install --python /tmp/uv_test/bin/python requests
  rm -rf /tmp/uv_test
  ```

### nvm 0.40.6
- **What:** Node Version Manager — manages Node.js versions inside WSL.
- **Obtain:** `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash` (adds sourcing lines to `~/.bashrc`).
- **Verify:** `nvm --version` and `nvm ls` (lists installed/default versions).

### Node.js 24.18.0
- **What:** JavaScript runtime n8n runs on. Installed and managed via nvm, not the system package manager.
- **Obtain:** `nvm install --lts` (or `nvm install 24` for this exact major version).
- **Verify:** `node --version`

### npm 11.16.0
- **What:** Node's package manager, bundled with the Node.js install above.
- **Verify:** `npm --version`

### n8n 2.27.4
- **What:** Low-code workflow automation platform — one of this project's two required implementations.
- **Obtain:** `npm install -g n8n` (installs under the active nvm Node version).
- **Verify:** `n8n --version`
- **Run:** `n8n start`, then open `http://localhost:5678`. **Must be launched from an interactive WSL shell** — see caveat below. Confirmed working: dashboard loads cleanly both via `curl` (`HTTP 200`) and manually in a browser.

### Secrets: `.env` / `.env.example`
- **What:** `.env.example` (tracked, public) lists the required variable names with clean placeholder values — `SERPAPI_API_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-5`). `.env` (git-ignored) holds the real values and already exists locally.
- **Obtain:** copy `.env.example` to `.env`, then fill in real values: a SerpAPI key and an OpenAI API key. Both are already in place locally.
- **Rule:** `.env` is never read or written directly, under any circumstances (standing project rule) — only `.env.example` is ever touched programmatically. Verifying `.env`'s contents or filling in real keys is done by the user directly.

### `mcp-server` (shared MCP server)
- **What:** a `uv`-structured Python project at `mcp-server/`, adapted from the official reference `fetch` MCP server (`modelcontextprotocol/servers`) plus a custom `search` tool (SerpAPI) and a citation/caching layer. Serves both tools over real MCP protocol via SSE transport (`mcp_server.run(transport="sse")`), so n8n's MCP Client Tool node and CrewAI's `MCPServerAdapter` both connect natively, on the same running server, over `http://127.0.0.1:8000/sse` by default.
- **Dependencies:** `mcp[cli]`, `markdownify`, `protego`, `readabilipy`, `pydantic`, `requests`, `python-dotenv` (runtime); `pytest` (dev). Installed via `uv add` inside `mcp-server/`; see `mcp-server/pyproject.toml`.
- **Run:** `cd mcp-server && uv run mcp-server` (from WSL, via the `/mnt/d/...` path per the "where the code lives" note below). Reads `SERPAPI_API_KEY` from the project-root `.env` automatically (python-dotenv walks up from the current directory to find it).
- **Test:** `cd mcp-server && uv run pytest` -- 9 tests, all mocked HTTP responses, no live network/API calls needed.
- **Smoke-test with curl** (per the rubric's explicit instruction), with the server running in one terminal:
  ```bash
  # 1. Open the SSE stream in the background, capture the session endpoint it announces
  curl -sN http://127.0.0.1:8000/sse > /tmp/mcp-sse.log &
  cat /tmp/mcp-sse.log   # look for: event: endpoint / data: /messages/?session_id=...

  # 2. Complete the MCP handshake against that session endpoint
  SESSION_URL="http://127.0.0.1:8000/messages/?session_id=<id from step 1>"
  curl -s -X POST "$SESSION_URL" -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl-smoke-test","version":"0.1"}}}'
  curl -s -X POST "$SESSION_URL" -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

  # 3. List tools, then call one -- responses arrive on the SSE stream from step 1, not the POST body
  curl -s -X POST "$SESSION_URL" -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
  curl -s -X POST "$SESSION_URL" -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"fetch","arguments":{"url":"https://example.com"}}}'
  ```
  Confirmed working: `initialize` returns server info/capabilities, `tools/list` returns both `search` and `fetch` with their schemas, and `tools/call` for both tools returns cited, timestamped JSON. A repeated `fetch` on the same URL returned instantly from cache instead of re-fetching.
- **Node.js note:** the `fetch` tool uses `readabilipy` for higher-quality article extraction when Node.js is available, gated by `shutil.which("node")` at call time (stdlib only, no extra dependency) rather than a bare try/except -- a known upstream issue (`modelcontextprotocol/servers#4199`) means `readabilipy`'s Node path **hangs indefinitely** if Node is missing or misconfigured, since its subprocess call has no timeout. With Node present (as it is here, for n8n), the *first* live `fetch` call incurs a one-time ~15-20s delay while `npx` installs a helper package; later calls are fast. If Node is ever unavailable, the tool falls back to a pure-Python extraction path (~1.2s per the upstream issue's own benchmark) instead of hanging.
- **Caching:** `mcp-server/.cache/` (git-ignored) holds one JSON file per citation, keyed by a hash of the URL, with a 6-hour freshness window -- this file I/O lives in the MCP server itself, not n8n (see the Phase 1 note in `ROADMAP.md` on why n8n can't own this directly).

### `log_server` (run-log HTTP endpoint)
- **What:** a `uv`-structured Python project at `comparison/log_server/`, providing a single local HTTP endpoint (`POST /log`) that n8n's HTTP Request node calls after each agent node finishes. Appends one JSON line per call to the shared `comparison/run_logs/run_logs.jsonl` file (schema: `run_id, implementation, agent, timestamp, tokens_in, tokens_out, cost_usd, latency_ms, run_status`), used by both this n8n implementation and the future CrewAI implementation, so Phase 5's `compare.py` can read both without special-casing either. This file I/O lives here because n8n's Code node sandboxes `fs` and cannot safely write local files itself -- same rationale as `mcp-server/`'s caching layer, plus two 2026 sandbox-escape CVEs (CVE-2026-1470, CVE-2026-0863) around Code-node file/code execution that make routing around the sandbox the wrong move.
- **Dependencies:** `python-dotenv`, `requests` (runtime, added for `ingest_execution.py` below); `pytest` (dev). No web framework -- the HTTP server itself is stdlib `http.server` only.
- **Run:** `cd comparison/log_server && uv run log-server` (from WSL). Reads `LOG_SERVER_HOST` / `LOG_SERVER_PORT` from the shell environment if set (defaults `127.0.0.1:8100` -- not in `.env`/`.env.example`, since neither is a secret and both have safe local defaults, matching the `MCP_SERVER_HOST`/`MCP_SERVER_PORT` precedent above). Prints one startup line once ready -- `[INFO] log_server listening on http://127.0.0.1:8100/log` -- that line is the signal it's up and ready for n8n to call.
- **Test:** `cd comparison/log_server && uv run pytest` -- 30 tests.
- **Stop:** Ctrl-C in its terminal; prints `[INFO] log_server shutting down` before exiting.
- **Storage:** `comparison/run_logs/run_logs.jsonl` (git-ignored, like `mcp-server/.cache/`) -- one JSON object per line, created automatically on the first successful `POST /log`.

### `ingest_execution` (post-hoc token/cost/latency capture)
- **What:** a second entry point in the same `log_server` project, `uv run ingest-execution [execution_id]`. n8n's AI Agent node doesn't expose token usage to downstream nodes (`ROADMAP.md`'s "Known Platform Limitations & Blockers"), so real cost/latency data can't be logged from inside the workflow in real time. This script instead calls n8n's own REST API after a run completes, pulling the real per-node data (which does include it), cross-references it against the exported workflow JSON to attribute each Chat Model's tokens to the right agent, and appends one row per agent/step to `run_logs.jsonl`.
- **Requires:** `N8N_API_KEY` in `.env` (n8n itself: Settings -> n8n API -> Create an API key). Not in `.env.example` as a value, just the variable name pattern (matches the non-secret host/port precedent's spirit, though this one genuinely is a secret -- still user-pasted directly into `.env`, never through Claude).
- **Run:** `cd comparison/log_server && uv run ingest-execution` (ingests the most recent execution) or `uv run ingest-execution <id>` (a specific one). Prints one summary line per agent/step logged.
- **Caution:** never inspect `.env`'s raw content to debug this (e.g., `cat`/`tail`/`od`) -- a real incident during this component's own setup did exactly that and exposed an API key in a session transcript, requiring immediate revocation. Use `python-dotenv` (which this script already does) and, if verification is ever needed, check only derived facts (e.g., whether a variable is set, its length) -- never the raw value.

### `n8n-nodes-serpapi` (n8n community node) 0.1.10
- **What:** SerpAPI's own official, n8n-verified community node (`SerpApi Official`), providing a native Google Search tool for the AI Agent — used alongside MCP's `fetch` tool by the Research Agent (MCP does the fetch/cite step, SerpAPI does the search step; see `ROADMAP.md` Phase 2.2 for why they're split this way).
- **Obtain:** in n8n, **Settings** -> **Community Nodes** -> **Install** -> package name `n8n-nodes-serpapi`. Self-hosted n8n only (not built in, unlike n8n Cloud where SerpAPI is preinstalled) — requires Owner/Admin role.
- **Credential:** created directly in n8n's own credential form (API Key field), using the same `SERPAPI_API_KEY` value already in `.env`. Never entered by Claude.

### `crewai` (CrewAI implementation)
- **What:** the second of the two required implementations (Phase 3), a `uv`-structured CrewAI
  project at `crewai/` (package name `vt-capstone-gtm-crew` -- see note below), scaffolded via
  `crewai create crew crewai` using CrewAI's JSON-first structure (`agents/*.jsonc`, `crew.jsonc`,
  `tools/`), not the older Python/YAML scaffold. Four agents (Head Planner, Research Agent, Analyst
  Agent, Strategy Agent) mirror the n8n implementation's roles and System Messages closely, all on
  `openai/gpt-5`, so the two implementations test the same agent design on two platforms.
- **Dependencies:** `crewai[tools]` and `crewai-tools[mcp]` (the latter pulls in `mcpadapt`, required
  by `MCPServerAdapter` -- not included by `crewai[tools]` alone; see gotcha below).
- **Requires:** its own `crewai/.env` with **both** `OPENAI_API_KEY` and `SERPAPI_API_KEY` -- `crewai
  run` only ever reads `Path.cwd()/.env` (verified directly from `crewai_cli`'s source), never the
  project root's `.env`, even though both keys already exist there. Add both directly to
  `crewai/.env` yourself; Claude never reads or writes `.env` files.
- **Run:** `cd crewai && uv run python run_and_log.py ["optional brief text"]` -- the standard way to
  run this crew. `crewai run` itself launches an interactive Textual TUI dashboard that **cannot be
  captured from a non-interactive/background process** (no plain-text output flag exists), so
  `run_and_log.py` drives the `Crew` object directly instead (`crewai.project.crew_loader.load_crew`
  + `.kickoff()` -- the same execution path `crewai run` uses for a JSON crew, just without the CLI's
  dashboard wrapper), printing plain, readable verbose output. It also appends one run-log row per
  agent to `comparison/run_logs/run_logs.jsonl` (real per-agent token usage via
  `agent.llm.get_token_usage_summary()`, real per-task latency via `Task.start_time`/`end_time`,
  converted to UTC-aware timestamps to match n8n's rows). Defaults to the fixed test brief if no
  argument is given.
- **Custom tools:** `crewai/tools/serpapi_search.py` and `crewai/tools/mcp_fetch.py`, wired into
  Research Agent only (`custom:serpapi_search`, `custom:mcp_fetch` in `agents/research_agent.jsonc`).
  `mcp_fetch.py` requires `mcp-server/` running locally (see above) -- opens a short-lived
  `MCPServerAdapter` connection per call rather than holding one open for the whole run.
- **Real setup gotchas hit and fixed (worth knowing before re-scaffolding or debugging a fresh
  clone):**
  - `crewai create crew` runs `git init` inside the new folder -- creates a nested git repo inside
    this project's own repo. Remove `crewai/.git/` so it's tracked normally (safe as long as it's
    still empty/no commits).
  - The scaffold's own `pyproject.toml` names the project `"crewai"`, colliding with the third-party
    `crewai` package it depends on (`uv sync` fails: "project depends on itself"). Renamed to
    `vt-capstone-gtm-crew` -- the folder name, crew display name, and `crewai run` usage are
    unaffected, only the internal Python package identifier changed.
  - `MCPServerAdapter` needs `mcpadapt`, which requires the separate `crewai-tools[mcp]` extra (see
    Dependencies above) -- without it, every `mcp_fetch` call fails with an empty error message and
    the run tries to interactively prompt to install a missing package mid-run.
- **Test:** `cd crewai && uv run pytest` -- 5 tests (`crewai/tests/`) covering `serpapi_search.py` and
  `mcp_fetch.py` with mocked I/O (`pytest>=9.1.1` added as a dev dependency, matching
  `mcp-server`/`log_server`'s convention). Plus real end-to-end runs via `run_and_log.py` as described
  above; see `ROADMAP.md` Phase 3.3/4 for the full verified run history (real SerpAPI searches, real
  MCP fetches, real cost figures, scenario/reproducibility testing).

### Google Cloud project + OAuth (Docs export)
- **What:** a Google Cloud project (`vt-capstone-gtm-planner`) with the Google Docs API and Google Drive API enabled; an OAuth consent screen (External, Testing status, scopes `.../auth/documents` + `.../auth/drive.file`, one test user); and an OAuth 2.0 Client ID (Web application type, redirect URI `http://localhost:5678/rest/oauth2-credential/callback` for n8n).
- **Obtain:** walked through in Google Cloud Console (console.cloud.google.com) — see `screenshots/Phase0-01` through `Phase0-08` for the build walkthrough.
- **Credentials:** Client ID/Secret added to `.env` as `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` by the user. The downloaded `client_secret*.json` file Google's console offers is git-ignored (`client_secret*.json` / `*credentials*.json` patterns) — it was briefly sitting untracked in the project root unprotected before that pattern was added; no exposure occurred since it was never committed.
- **Note:** this Client ID has one redirect URI (n8n's), and that remains the only one needed --
  CrewAI's implementation (Phase 3) ends at the drafted GTM plan text and never adds its own Google
  Docs export step, confirmed during Phase 4 testing (no Google API code anywhere in `crewai/`).

### `compare.py` (n8n vs. CrewAI comparison report)
- **What:** a plain, standalone script at `comparison/compare.py` (Phase 5) -- reads
  `comparison/run_logs/run_logs.jsonl` (the shared schema both `log_server`'s `ingest-execution` and
  `crewai/run_and_log.py` write to) and writes `comparison/report.md` with cost, latency, and
  reliability/error-rate comparison tables across both implementations. Pure standard library
  (`json`, `pathlib`, `statistics`, `dataclasses`) -- no new dependency, matching this project's
  established stdlib-first convention (same reasoning as `log_server`'s stdlib `http.server` choice).
- **Run:** `cd comparison/log_server && uv run python ../compare.py` (reuses `log_server`'s existing
  venv, since `compare.py` itself needs no dependencies beyond the standard library -- no separate
  `uv` project was created just for one script).
- **Test:** `cd comparison/log_server && uv run pytest ../tests/` -- 5 tests
  (`comparison/tests/test_compare.py`) covering run-grouping, per-run cost/latency totals, and
  success-rate math against a temporary JSONL fixture.

### Screenshots (`screenshots/`)
- **What:** build-walkthrough screenshots for the final reflections/submission document. Tracked (pushed to GitHub), unlike `documentation/`.
- **Naming:** `<Phase>-<NN>-name.jpg`, where `<Phase>` matches the ROADMAP.md phase (e.g. `Phase0`) and `<NN>` is a two-digit sequence starting at `01`. Screenshot-worthy moments are flagged one at a time, at the point each is actually reached (not a pre-emptive batch list).
- **Rule:** check for visible secrets/PII (API keys, OAuth client secrets, email addresses) before saving; redact/crop/blur as needed. Google's own UI already masks OAuth client secrets after creation, which helps.

## Important environment caveats

### Where the Python code lives: Windows path via WSL mount, not a separate clone
This project's Python code (MCP server in Phase 1, CrewAI project in Phase 3) is developed and run from this same project folder, accessed from a WSL terminal through the Windows-drive mount WSL2 sets up automatically: `/mnt/d/Python_Projects/VT-Projects/12-Capstone-Product_Strategy_Simulation`. That's the identical git repo already rooted on the Windows `D:` drive — not a second copy cloned into WSL's native filesystem (e.g. `~/projects/...`). `cd` there from WSL, then run `uv`/`python` normally; `git push` from WSL pushes straight to GitHub over the network like any other git remote, so there's no separate "get the code out of WSL" step.

Tradeoff accepted: file I/O across the `/mnt/` bridge (9p/drvfs) is somewhat slower than a Linux-native path, but is a non-issue at this project's scale (a handful of Python files, no large datasets, no heavy file-watcher workloads). A WSL-native clone would only be worth the added complexity of keeping two copies in sync if I/O performance actually became a bottleneck.

### Node/n8n only resolve correctly from an interactive WSL shell
nvm's PATH setup lives in `~/.bashrc`, which is sourced by **interactive** shells (`bash -ic "..."`, or a normal terminal you type into) but *not* by non-interactive login shells (`bash -lc "..."`, which reads `~/.profile` instead). Invoked the wrong way, `node`/`npm`/`n8n` silently fall through to whatever same-named entries exist elsewhere on the inherited Windows `PATH` (e.g. a Windows-side Node.js install), which can't execute from Linux and fail with a confusing "Permission denied". Always start n8n (or run any Node/npm command) from an actual interactive terminal, not a scripted non-interactive invocation.

### WSL networking changes made to get here
Three changes were needed to get reliable internet access working inside WSL (SerpAPI, Google APIs, and PyPI/npm registry access all depend on this):

1. **`/etc/wsl.conf`** — `generateResolvConf = false` was disabling WSL's automatic DNS configuration, leaving no DNS servers assigned at all. Commented out so WSL manages `/etc/resolv.conf` again.
2. **`/etc/sysctl.d/99-disable-ipv6.conf`** — disables IPv6 inside WSL (`net.ipv6.conf.all.disable_ipv6 = 1` and the `default` equivalent). May no longer be strictly necessary after fix #3 below, but is harmless and left in place.
3. **`C:\Users\<your-username>\.wslconfig`** — created with:
   ```ini
   [wsl2]
   networkingMode=mirrored
   dnsTunneling=true
   autoProxy=true
   firewall=true
   ```
   This, combined with disabling an active VPN, resolved a conflict where WSL2's virtual NAT adapter and the VPN interfered with each other — DNS was slow/flaky and real HTTPS connections (e.g. to PyPI) timed out after resolving, even though raw IP connectivity looked fine. Requires WSL >= 2.0 (confirmed here: 2.7.3.0). Apply changes with `wsl --shutdown` followed by reopening a WSL terminal.
