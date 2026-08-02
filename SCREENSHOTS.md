# Screenshots

Index of every file in `screenshots/`: what it shows, and the configuration details/data points worth
citing in the final reflections/submission document. Updated every time a new screenshot is added.

Naming convention: `<Phase>-<NN>-name.jpg`, where `<Phase>` matches the `ROADMAP.md` phase (e.g.
`Phase0`) and `<NN>` is a two-digit sequence starting at `01`. Screenshots are tracked and pushed to
GitHub (unlike `documentation/`), since they're evidence for a graded deliverable. Any visible
secrets/PII are checked and redacted/cropped before saving -- see the per-file notes below for what
was redacted in each one.

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
