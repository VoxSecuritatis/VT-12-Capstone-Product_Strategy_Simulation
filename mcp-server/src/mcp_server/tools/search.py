# ================================================================
# Search Tool
# ================================================================
# Objective:
#       Search the web via SerpAPI and return cited results, so the
#       Research Agent (n8n and CrewAI alike) can ground claims in
#       linked, timestamped sources.
# Inputs:
#       - query: search terms
#       - num_results: how many organic results to return
# Outputs:
#       - a list of SearchResult records (title, link, snippet, citation_id)
# Notes:
#   - Uses SERPAPI_API_KEY from the environment (.env), loaded by the
#     server entrypoint via python-dotenv. This module never reads .env
#     directly.
# ================================================================

import os

import requests
from pydantic import BaseModel

from mcp_server.tools.cache import store_snapshot

SERPAPI_ENDPOINT = "https://serpapi.com/search"


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str
    citation_id: str


def search_web(query: str, num_results: int = 5) -> list[SearchResult]:
    """Search the web via SerpAPI and return cited results."""
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY is not set in the environment")

    params = {"q": query, "engine": "google", "api_key": api_key, "num": num_results}
    response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    results = []
    for item in payload.get("organic_results", [])[:num_results]:
        link = item.get("link", "")
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        entry = store_snapshot(
            url=link,
            source_tool="search",
            content=snippet,
            extra={"title": title, "query": query},
        )
        results.append(
            SearchResult(title=title, link=link, snippet=snippet, citation_id=entry.citation_id)
        )
    return results
