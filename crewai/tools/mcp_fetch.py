# ================================================================
# MCP Fetch Tool
# ================================================================
# Objective:
#       Give the Research Agent the same page-fetch capability its n8n
#       counterpart has via the MCP Client Tool node -- fetching a URL's
#       content through this project's own MCP server (mcp-server/),
#       which respects robots.txt and returns a cited, timestamped
#       snapshot. See ROADMAP.md's Known Platform Limitations & Blockers,
#       item 2, for why some fetches fail (robots.txt / anti-scraping
#       blocks) -- Research Agent's own task instructions already say to
#       move on to the next result rather than retry, matching n8n's
#       design.
# Inputs:
#       - url: the page to fetch
# Outputs:
#       - the fetched page's cited, timestamped content
# Notes:
#   - Requires mcp-server/ to be running locally (uv run mcp-server,
#     default http://127.0.0.1:8000/sse) -- the same server n8n's MCP
#     Client Tool node connects to, so both implementations share one
#     source of truth for citation/caching logic (Phase 1).
#   - Opens a short-lived MCP connection per call rather than holding one
#     open for the whole crew run, since Research Agent fetches at most
#     twice per run -- simplest correct option at this call volume.
# ================================================================

import os

from crewai.tools import BaseTool
from crewai_tools import MCPServerAdapter
from pydantic import BaseModel, Field

MCP_SERVER_URL_DEFAULT = "http://127.0.0.1:8000/sse"


class McpFetchInput(BaseModel):
    """Arguments for McpFetchTool."""

    url: str = Field(..., description="The URL of the page to fetch.")


class McpFetchTool(BaseTool):
    """Fetch a URL's content through this project's local MCP server."""

    name: str = "mcp_fetch"
    description: str = (
        "Fetch a URL's content through this project's MCP server, which respects "
        "robots.txt and returns a cited, timestamped snapshot. If this errors for a "
        "URL, do not retry it -- move on to the next search result instead."
    )
    args_schema: type[BaseModel] = McpFetchInput

    def _run(self, url: str) -> str:
        """Fetch a URL via the local MCP server's 'fetch' tool and return its content."""
        server_url = os.environ.get("MCP_SERVER_URL", MCP_SERVER_URL_DEFAULT)
        with MCPServerAdapter({"url": server_url}, "fetch") as tools:
            fetch_tool = tools[0]
            return fetch_tool.run(url=url)
