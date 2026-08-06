# mcp-server

Shared MCP server for this capstone -- exposes `search` (SerpAPI) and `fetch` (fetch + markdown
conversion) as real MCP tools over SSE transport, with a citation/caching layer backing both.
Adapted from the official reference `fetch` server (`modelcontextprotocol/servers`) rather than
built from scratch. See the top-level `README.md` ("MCP server" section) and `SETUP.md`
("`mcp-server` (shared MCP server)" section) for the full design, run commands, and curl
smoke-test procedure.

## Quick start

```bash
uv run mcp-server        # starts the server on http://127.0.0.1:8000 (SSE transport)
uv run pytest            # runs the test suite (mocked HTTP, no live network needed)
```

Requires `SERPAPI_API_KEY` in the project-root `.env` (auto-discovered by python-dotenv).

---

> © 2026 Brock Frary. All rights reserved.
