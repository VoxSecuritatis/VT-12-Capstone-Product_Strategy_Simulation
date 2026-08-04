# ================================================================
# SerpAPI Search Tool
# ================================================================
# Objective:
#       Give the Research Agent the same web-search capability its n8n
#       counterpart has via n8n's dedicated SerpApi node.
# Inputs:
#       - query: search terms
#       - num_results: how many organic results to return (default 3,
#         matching n8n's Research Agent tool-budget cap)
# Outputs:
#       - a short, readable summary of the top results (title, link, snippet)
# Notes:
#   - Runs as a standalone requests call rather than reusing mcp-server's
#     search tool, since this executes in-process as a CrewAI tool, not
#     over MCP -- mirrors mcp-server/src/mcp_server/tools/search.py's
#     SerpAPI call pattern for consistency across both implementations.
#   - Uses SERPAPI_API_KEY from the environment (crewai/.env), loaded by
#     crewai's own CLI at startup. This module never reads .env directly.
# ================================================================

import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

SERPAPI_ENDPOINT = "https://serpapi.com/search"


class SerpApiSearchInput(BaseModel):
    """Arguments for SerpApiSearchTool."""

    query: str = Field(..., description="The search query to run.")
    num_results: int = Field(3, description="How many organic results to return.")


class SerpApiSearchTool(BaseTool):
    """Search the web via SerpAPI and return the top results."""

    name: str = "serpapi_search"
    description: str = (
        "Search the web via SerpAPI and return the top results with title, link, "
        "and snippet for each -- use this to find candidate sources before fetching one."
    )
    args_schema: type[BaseModel] = SerpApiSearchInput

    def _run(self, query: str, num_results: int = 3) -> str:
        """Search the web via SerpAPI and return a short summary of results."""
        api_key = os.environ.get("SERPAPI_API_KEY")
        if not api_key:
            raise RuntimeError("SERPAPI_API_KEY is not set in the environment")

        params = {"q": query, "engine": "google", "api_key": api_key, "num": num_results}
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()

        lines = []
        for item in payload.get("organic_results", [])[:num_results]:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            lines.append(f"- {title}\n  {link}\n  {snippet}")

        if not lines:
            return f"No results found for query: {query}"
        return "\n".join(lines)
