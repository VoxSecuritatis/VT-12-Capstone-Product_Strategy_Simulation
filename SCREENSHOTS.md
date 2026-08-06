# Screenshots

Index of every file in `screenshots/`: what it shows, and the configuration details/data points worth
citing in the final reflections/submission document. Updated every time a new screenshot is added.

Naming convention: `<Phase>-<NN>-name.jpg`, where `<Phase>` matches the `ROADMAP.md` phase (e.g.
`Phase0`) and `<NN>` is a two-digit sequence starting at `01`. Screenshots are tracked and pushed to
GitHub (unlike `documentation/`), since they're evidence for a graded deliverable. Any visible
secrets/PII are checked and redacted/cropped before saving -- see the per-file notes below for what
was redacted in each one.

`screenshots/logos/` is a separate reserved subfolder (not part of the naming convention above) for
learning-partner logos, for the final reflections `.docx`/`.pdf` document:
- `Microsoft.jpg` -- Microsoft logo
- `Virginia_Tech.jpg` -- Virginia Tech Continuing and Professional Education logo
- `simplilearn.jpg` -- Simplilearn logo

## Phase 0 -- Environment & Access Setup

### Phase0-01-google_cloud_project_created.jpg
Google Cloud Console "Welcome" page confirming the project exists.
- **Project ID:** `vt-capstone-gtm-planner`
- **Project number:** redacted (boxed out in the image)
- Confirms: Google Cloud project created and selected as the active project.

### Phase0-02-google_docs_api_enabled.jpg
API/Service Details page for the Google Docs API.
- **Service name:** `docs.googleapis.com`
- **Type:** Public API
- **Status:** Enabled
- Confirms: Google Docs API enabled on the project.

### Phase0-03-google_drive_api_enabled.jpg
API/Service Details page for the Google Drive API.
- **Service name:** `drive.googleapis.com`
- **Type:** Public API
- **Status:** Enabled
- Confirms: Google Drive API enabled on the project (needed alongside Docs for file access).

### Phase0-04-oauth_branding_created.jpg
Google Auth Platform Overview page, right after initial branding/consent-screen setup.
- Toast notification: "OAuth configuration created!"
- Metrics panel still reads "You haven't configured any OAuth clients for this project yet" -- this
  screenshot is the branding step specifically, before any OAuth Client ID existed.
- Confirms: Google Auth Platform (the renamed "OAuth consent screen") branding step completed.

### Phase0-05-oauth_scopes_added.jpg
Google Auth Platform > Data Access page, showing the two scopes added to the app.
- **Non-sensitive scope:** Google Docs API, `.../auth/drive.file` -- "See, edit, create, and delete
  only the specific Google Drive files you use with this app"
- **Sensitive scope:** Google Docs API, `.../auth/documents` -- "See, edit, create, and delete all
  your Google Docs documents"
- No restricted scopes added.
- Toast notification: "Data access changes saved!"
- Confirms: both OAuth scopes required for Docs export are configured.

### Phase0-06-oauth_audience_test_user_added.jpg
Google Auth Platform > Audience page.
- **Publishing status:** Testing
- **User type:** External
- **OAuth user cap:** 1 user (1 test, 0 other) / 100 user cap
- One test user listed under "Test users" -- **email username redacted** (boxed out in the image),
  only the `@gmail.com` domain is visible.
- Confirms: app is in Testing mode (External), with the one required test user added.

### Phase0-08-oauth_client_details_saved.jpg
Google Auth Platform > Clients page, detail view of the OAuth 2.0 Client ID used by n8n.
- **Client name:** `n8n local`
- **Client type:** Web application
- **Client ID:** visible in the screenshot; not reproduced here (treated the same as a credential
  for documentation purposes, even though Google itself doesn't treat Client IDs as secret)
- **Client secret:** masked by Google's own UI as `****tg_x`
- **Authorized redirect URI:** `http://localhost:5678/rest/oauth2-credential/callback`
- **Creation date:** August 2, 2026, 8:38:17 AM GMT-5
- **Status:** Enabled
- Toast notification: "OAuth client saved"
- Confirms: the OAuth Client ID/Secret pair n8n uses for its Google Docs/Drive OAuth flow.

**Note:** `Phase0-07` does not exist -- a gap in the sequence from the original walkthrough, not a
missing/lost file. Left as-is; the next new screenshot continues at whatever the next unused number
is for its phase, not by backfilling this gap.

## Phase 2 -- n8n Implementation

### Phase2-01-mcp_client_tool_end_to_end_test.jpg
n8n editor, full canvas view plus the MCP Client node's INPUT/OUTPUT panel, after a real
end-to-end run.
- **Workflow:** Trigger manually -> AI Agent (OpenAI Chat Model, `gpt-5`) -> MCP Client Tool
  (`http://127.0.0.1:8000/sse`, SSE transport, no auth, all tools included).
- **Test input:** prompt instructed the Agent to fetch `https://example.com` (IANA's reserved
  documentation/test domain, chosen deliberately to keep this screenshot free of personal content)
  and summarize it.
- **MCP Client node INPUT:** `url: https://example.com`, `tool: MCP_Client_fetch` -- confirms the
  Agent chose to call the tool itself, not a manual/forced call.
- **MCP Client node OUTPUT:** a cited, timestamped snapshot (`citation_id`, `source_tool: fetch`,
  `fetched_at` timestamp, page content) -- confirms the Phase 1 citation/caching design working
  end-to-end from n8n.
- **Run stats:** MCP Client node succeeded in 16.79s; full Agent run succeeded in 27.612s (~350
  tokens).
- Confirms: Phase 2.1 exit criterion ("n8n running, MCP server reachable from it") met with a real
  agent-driven tool call, not just a raw connectivity check.

### Phase2-02-research_agent_search_fetch_chain.jpg
n8n editor, full canvas view plus the **Research Agent** node's OUTPUT panel (renamed from n8n's
generic default "AI Agent" to reflect its actual role, per the README's agent table), after fixing a
stuck tool-call loop (see `ROADMAP.md` Phase 2.2 for the full diagnosis).
- **Workflow:** Trigger manually -> Research Agent (OpenAI Chat Model, `gpt-5`, Max Iterations `5`)
  -> two distinct tools: **MCP Client** (`fetch` only -- `search` deliberately excluded) and
  **SerpApi Official** (Google Search).
- **Test input:** prompt instructed the Agent to search the web for recent Virginia Tech news via
  SerpAPI, then fetch and summarize the top result via MCP -- a genuine two-tool chain, each tool
  doing a distinct job (SerpAPI searches, MCP fetches/cites).
- **Research Agent OUTPUT:** clean search -> fetch -> cite chain -- top result identified
  (`news.vt.edu`), page fetched and summarized, citation block with source URL, snapshot timestamp,
  and citation ID.
- **Run stats:** succeeded in 3 LLM iterations (well under the Max Iterations cap of 5), ~36,857
  tokens, ~44s -- a large improvement over the ~200-270K-token stuck-loop runs that preceded the
  fix.
- Confirms: MCP tools and SerpAPI both wired into the Research Agent and working together
  correctly, per the rubric's explicit requirement that both be present as distinct integrations
  (`documentation/1762856365_capstoneprojectproblemstatement.md`).

### Phase2-03-head_planner_research_agent_chain.jpg
n8n editor, full canvas view after the first successful **Head Planner -> Research Agent** run on a
real (not placeholder) project brief -- see `ROADMAP.md` Phase 2.2 for the scope-control fixes this
required.
- **Workflow:** Trigger manually -> Head Planner (no tools, drafts 2 short research questions) ->
  Research Agent (MCP Client `fetch` + SerpApi `search`, `num=3` results per search).
- **Test input:** a short budget-headphone GTM brief -- kept deliberately minimal, since this is an
  academic/portfolio proof-of-concept, not a production system.
- **Result:** "Workflow executed successfully" -- Head Planner produced 2 single-facet research
  questions; Research Agent ran exactly 2 SerpAPI searches (one per question) plus MCP tool calls,
  no context-window overflow.
- **Run stats:** ~100,384 tokens, ~2m 4s total for both agents combined.
- Confirms: the two-agent hand-off (Head Planner drafting a research brief, Research Agent
  executing it) works end-to-end with real, non-placeholder input.

### Phase2-04-analyst_agent_synthesis.jpg
n8n editor, full canvas view plus the **Analyst Agent** node's OUTPUT panel, after the first
successful three-agent chain run (Head Planner -> Research Agent -> Analyst Agent) -- see
`ROADMAP.md` Phase 2.2 for the node-config gotcha and fetch-failure fallback fix this run proves out.
- **Workflow:** Trigger manually -> Head Planner -> Research Agent (MCP Client `fetch` + SerpApi
  `search`) -> Analyst Agent (no tools of its own -- synthesizes Research Agent's output only).
  Analyst Agent's Prompt (User Message) is the named-node expression
  `{{ $('Research Agent').item.json.output }}`; System Message is a short, minimal synthesis
  instruction per the academic-scope rule.
- **Test input:** the same locked-in fixed test brief (budget noise-cancelling headphone for
  commuters) used throughout Phase 2.3.
- **Analyst Agent OUTPUT:** a short, specific competitor comparison (Anker Soundcore, JBL, JLab,
  Skullcandy, TOZO) plus a brief qualitative paragraph -- genuinely derived from Research Agent's
  actual findings, not generic/hallucinated content.
- **Notable event proven in this run:** MCP Client's `fetch` failed once (`403 Forbidden`, a
  market-research site's own anti-scraping block) on the first attempt; Research Agent's
  fetch-failure fallback instruction (added to its System Message specifically because of this) had
  it move on to a different search result instead of retrying the blocked URL, and the overall run
  still completed cleanly. Demonstrates the resilience fix working end-to-end under a real failure,
  not just in theory.
- **Run stats:** ~154,997 tokens, ~3m 10s for the full three-agent chain.
- Confirms: Research Agent -> Analyst Agent hand-off works end-to-end, and the fetch-failure
  fallback (rubric's "source volatility" risk mitigation) holds up under a real, live failure.

### Phase2-05-strategy_agent_gtm_plan.jpg
n8n editor, full canvas view plus the **Strategy Agent** node's OUTPUT panel, after the first
successful five-node chain run (Head Planner -> Research Agent -> Analyst Agent -> Strategy Agent).
- **Workflow:** Trigger manually -> Head Planner -> Research Agent (MCP Client `fetch` + SerpApi
  `search`) -> Analyst Agent (synthesis, no tools) -> Strategy Agent (GTM plan drafting, no tools).
  Strategy Agent's Prompt (User Message) is the named-node expression
  `{{ $('Analyst Agent').item.json.output }}`; System Message is a short, minimal GTM-drafting
  instruction per the academic-scope rule.
- **Test input:** the same locked-in fixed test brief (budget noise-cancelling headphone for
  commuters) used throughout Phase 2.3.
- **Strategy Agent OUTPUT:** a concrete, specific GTM plan -- target customer/ICP statement, value
  proposition, messaging/channel suggestions (e.g. Amazon A+ content, creator/earned-media seeding),
  and a brief launch-plan outline -- all genuinely tied to Analyst Agent's actual synthesis, not
  generic boilerplate.
- **Run stats:** Strategy Agent itself succeeded in 28.691s (~853 tokens); ~121,416 tokens for the
  full five-node chain end-to-end.
- Confirms: Analyst Agent -> Strategy Agent hand-off works end-to-end with no repeat of the earlier
  "Source for Prompt" dropdown-vs-text-field gotcha (`ROADMAP.md` Phase 2.2) -- correctly avoided
  this time.

### Phase2-06-docs_writer_create_success.jpg
n8n editor, full canvas view after the first successful six-node chain run through the **Docs
Writer** node (Head Planner -> Research Agent -> Analyst Agent -> Strategy Agent -> Docs Writer),
renamed from n8n's default "Create a document" label per the standing node-naming rule.
- **Workflow:** same fixed test brief chain as every prior Phase 2.2 screenshot, now extended one
  more step: Docs Writer (Resource: Document, Operation: Create) takes no input content itself --
  it only creates a blank, titled Google Doc (Title: `GTM Plan - {{ $now }}`); inserting the actual
  GTM plan text is a separate, not-yet-built Update step (see `ROADMAP.md` Phase 2.2).
- **MCP Client error hit and recovered from during this run:** `Error executing tool fetch:
  robots.txt disallows fetching https://rascasse.com/explore/us/noise-cancelling-headphones-17739`
  -- a different failure type than the earlier `403 Forbidden` case (`Phase2-04`), but the same
  underlying cause (a site declining the request; consistent with the MCP server's own Phase 1
  design choice to respect `robots.txt`). Research Agent's existing fetch-failure fallback
  instruction handled this correctly without any prompt changes, confirming the fix generalizes
  across different fetch-failure reasons, not just the one case it was originally written for.
- **Google Docs node output:** `kind: drive#file`, `mimeType: application/vnd.google-apps.document`,
  `name: GTM Plan - 2026-08-03T13:54:31.220-04:00` -- this exact name matches the file shown in the
  `Phase2-07` Google Drive screenshot, cross-confirming the same run's result in both places.
- Confirms: Docs Writer's Create operation works end-to-end and survives a real mid-run fetch
  failure without derailing the rest of the chain.

### Phase2-07-gtm_plan_doc_created_in_drive.jpg
Google Drive "My Drive" listing (personal account), confirming the document created by the
`Phase2-06` run actually exists in Google Drive, not just in n8n's own execution log.
- Surrounding files in the listing are redacted (blacked out) per the standing PII/secrets
  screenshot policy; only the relevant row is visible.
- **Visible row:** `GTM Plan - 2026-08-03T13:54:31.220-04:00`, Google Docs file type icon, Owner
  "me", modified at the matching timestamp -- confirms this is the same document referenced in the
  `Phase2-06` n8n Create-a-document output, not a different/stale file.
- Confirms: the OAuth2 credential (Client ID/Secret from `.env`, `drive.file` + `documents` scopes
  only -- full Drive access was deliberately declined during consent) is correctly wired and able to
  create real files in the authenticated Google account.

### Phase2-08-gtm_plan_final_document_content.jpg
The actual opened Google Doc (`GTM Plan - 2026-08-03T13:54:31.220-04:00`) in the Google Docs editor,
showing the real inserted content -- the end product of the full n8n agent chain.
- **Content:** genuine, well-formatted GTM plan text with real paragraph breaks (not literal `\n`
  characters), organized into clear sections -- Target customer/ICP, one-line value proposition,
  messaging/channel suggestions, and a launch plan (POC) with pricing, readiness, seeding, Amazon/
  retail promo, and measure/iterate bullets.
- **Node that produced this:** `Docs Writer - Insert Content` (Update operation, Insert Text action,
  Body segment), inserting `{{ $('Strategy Agent').item.json.output }}` into the document created by
  `Docs Writer - Create a document`. Confirms the `\n`-embedded string from Strategy Agent's raw
  output renders as real line breaks once inserted via the Google Docs node's Insert Text action, not
  as garbled literal backslash-n characters -- an open concern going in, now resolved.
- Confirms: the full n8n agent chain -- Manual Trigger -> Head Planner -> Research Agent -> Analyst
  Agent -> Strategy Agent -> Docs Writer (Create + Insert Content) -- works end-to-end and produces a
  real, readable Google Doc GTM plan from a single fixed test brief, with no re-execution of the
  upstream LLM agents needed to test the final Insert Content step (cached input data reused).

### Phase2-09-full_chain_end_to_end_success.jpg
n8n editor, full canvas view after a single **Execute workflow** run (not a per-node "Execute step")
completing the entire seven-node chain in one pass: Manual Trigger -> Head Planner -> Research Agent
-> Analyst Agent -> Strategy Agent -> Docs Writer - Create a document -> Docs Writer - Insert
Content. All nodes green.
- **Notable event within this run:** MCP Client's fetch hit the same `robots.txt disallows fetching`
  error on `rascasse.com` seen in `Phase2-06` -- SerpAPI consistently surfaces this site as a top
  result for this query, and the MCP server consistently and correctly respects its `robots.txt`.
  Research Agent's fetch-failure fallback recovered from it again, with no manual intervention.
- **Run stats:** ~166,564 tokens, 3m 5s total for the entire seven-node chain, end to end, in a
  single click.
- Confirms the **Phase 2.3 exit criterion** directly: "one end-to-end run produces a drafted GTM doc
  in <15 minutes" -- 3m 5s is well within that budget. This is the clearest single piece of evidence
  that the full n8n implementation works as designed, including graceful recovery from a real,
  reproducible source-volatility failure, not just a best-case/no-errors run.

## Phase 3 -- CrewAI Implementation

All eight screenshots below are from a single real end-to-end run (Crew ID
`1743ba69-15b9-4ea9-8e8d-d3939a63ac8b`), driven via `crewai/run_and_log.py` (plain verbose terminal
output, not CrewAI's own uncapturable Textual TUI dashboard -- see `ROADMAP.md` Phase 3.3), using the
same locked-in fixed test brief as every Phase 2 n8n screenshot: "A new budget noise-cancelling
headphone for commuters. Who's the target customer and who are the main competitors?" Terminal
title-bar usernames are redacted (boxed out) in every screenshot per the standing PII/secrets policy.

### Phase3-01-crew_started_head_planner.jpg
Terminal (WSL, `uv run python run_and_log.py`), Crew Execution Started panel through Head Planner's
Task Completion.
- **Task:** `plan_research_questions`, **Agent:** Head Planner (no tools -- drafts the research brief)
- **Head Planner's Final Answer:** a one-sentence objective restatement plus exactly two short,
  single-facet research questions (primary age bracket of U.S. commuters buying sub-$100 ANC
  headphones; current top five best-selling sub-$100 ANC headphones on Amazon U.S.)
- Confirms: the crew's first hand-off point (kickoff -> Head Planner) works end-to-end with real,
  non-placeholder input.

### Phase3-02-research_agent_serpapi_resilience.jpg
Terminal, Research Agent's task/tool execution, showing a real transient failure and recovery.
- **Task:** `research_questions`, **Agent:** Research Agent, **Tool:** `serpapi_search` (SerpAPI)
- **Real failure captured:** Tool Execution #1 failed with `HTTPSConnectionPool(host='serpapi.com',
  port=443): Read timed out. (read timeout=15)` -- a genuine transient network error, not staged.
- **Recovery:** Research Agent's own reasoning loop moved on to Tool Execution #2 (a reworded query)
  and #3, with no manual intervention.
- Confirms: SerpAPI is wired into Research Agent as a real, working tool, and the agent handles a
  real transient failure gracefully -- the same source-volatility risk category the n8n
  implementation also had to handle (see README's Risks & Mitigations).

### Phase3-03-research_agent_mcp_fetch.jpg
Terminal, Research Agent's `mcp_fetch` tool calls (this project's own MCP server), showing both a
real blocked fetch and a real successful one.
- **Tool:** `mcp_fetch` -> this project's MCP server (`http://127.0.0.1:8000/sse`)
- **Real failure:** Tool Execution #1 on `rascasse.com` returned `Error executing tool fetch:
  robots.txt disallows fetching ...` -- the MCP server correctly respecting `robots.txt`, the same
  behavior already proven in n8n's `Phase2-06`/`Phase2-09` screenshots.
- **Real success:** Tool Execution #2 on an Amazon Best Sellers page returned a full citation
  object -- `citation_id`, `url`, `source_tool: fetch`, `fetched_at` timestamp, and page content --
  confirming the Phase 1 citation/caching design working end-to-end from CrewAI, not just n8n.
- Confirms: both of Research Agent's distinct tool integrations (SerpAPI + this project's own MCP
  server) are real and working together, matching the rubric's explicit requirement that both be
  present (same proof point as n8n's `Phase2-02`).

### Phase3-04-research_agent_final_answer_citations.jpg
Terminal, the tail end of Research Agent's Final Answer and its Task Completion panel.
- **Agent:** Research Agent, **Task:** `research_questions`
- Final Answer includes, for each research question, a concise finding, the source cited, and a full
  content snapshot (URL, `Fetched at` timestamp, title, raw content) -- real citations, not
  paraphrased/hallucinated summaries.
- **Notable honesty from the agent itself:** for question 2 (top five best-selling ANC headphones),
  the agent explicitly noted the Amazon Best Sellers page is dynamic and its snapshot only revealed
  partial product details, recommending live verification rather than overstating confidence in the
  sub-$100 ranking.
- Confirms: the Research Agent -> rest-of-chain hand-off carries forward real, cited evidence, not
  synthetic content.

### Phase3-05-analyst_agent_synthesis.jpg
Terminal, Analyst Agent's Task Started through Task Completion panels.
- **Task:** `synthesize_findings`, **Agent:** Analyst Agent (no tools of its own -- synthesizes
  Research Agent's output only)
- **Final Answer:** a markdown competitor comparison table (Brand/Model, Under $100 now?, Key
  commuter/ANC features, Battery, Validation status) across five real competitor products (Soundcore
  by Anker Life Q20i, Soundcore Life Q30, JBL Tune 660NC, TOZO HT2/HT6, Srhythm NC25/NC35), plus a
  short qualitative "Competitive reality" paragraph.
- Confirms: Research Agent -> Analyst Agent hand-off works end-to-end, genuinely derived from the
  prior task's real findings (mirrors n8n's `Phase2-04` proof point).

### Phase3-06-strategy_agent_gtm_plan.jpg
Terminal, Strategy Agent's Task Started through Task Completion panels.
- **Task:** `draft_gtm_plan`, **Agent:** Strategy Agent (no tools -- drafts the GTM plan from Analyst
  Agent's synthesis only)
- **Final Answer:** ICP/target customer statement, one-line value proposition, three
  messaging/channel suggestions, and a brief launch-plan outline (positioning/pricing, pre-launch,
  launch weeks 1-4, post-launch days 30-60).
- Confirms: Analyst Agent -> Strategy Agent hand-off works end-to-end, producing a concrete, specific
  GTM plan tied to the real competitor data upstream (mirrors n8n's `Phase2-05` proof point).

### Phase3-07-crew_completion_and_run_log.jpg
Terminal, the Crew Completion panel and the script's printed `===== FINAL RESULT =====` block.
- **Crew ID:** `1743ba69-15b9-4ea9-8e8d-d3939a63ac8b`
- **Final Output:** the same GTM plan text from Strategy Agent's Final Answer (`Phase3-06`),
  confirming the crew's actual return value matches the last task's output.
- Confirms the **Phase 3.3 exit criterion**: the entire four-agent chain (Head Planner -> Research
  Agent -> Analyst Agent -> Strategy Agent) completes end-to-end in a single script invocation,
  producing a real, readable GTM plan.

### Phase3-08-run_log_confirmation.jpg
Terminal, the tail of the same run -- the Tracing Status panel followed by `run_and_log.py`'s own
`[INFO]` summary lines.
- `[INFO] logged crew run 1743ba69-15b9-4ea9-8e8d-d3939a63ac8b: 4 rows appended`
- **Real per-agent data:** Head Planner (227 in / 851 out tokens, $0.004398, ~18.9s); Research Agent
  (51,260 in / 29,427 out tokens, $0.179429, ~8m 1.5s); Analyst Agent (1,941 in / 2,894 out tokens,
  $0.015693, ~37.2s); Strategy Agent (2,433 in / 2,165 out tokens, $0.012358, ~24.7s).
- **Total real cost for this run: $0.211878** -- 42.4% of the $0.50/run cap.
- Confirms: `run_and_log.py`'s run-log emission (Phase 3.3's last engineering item) works end-to-end
  on a real run, appending exactly 4 schema-valid rows to `comparison/run_logs/run_logs.jsonl` --
  the same run independently verified directly against the file earlier this session.

---

> © 2026 Brock Frary. All rights reserved.
