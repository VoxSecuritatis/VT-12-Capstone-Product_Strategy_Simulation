# ================================================================
# Fetch Tool
# ================================================================
# Objective:
#       Fetch a URL, respect robots.txt, convert the page to markdown, and
#       return a cited, timestamped snapshot. Adapted from the official
#       MCP reference "fetch" server (modelcontextprotocol/servers).
# Inputs:
#       - url: the page to fetch
# Outputs:
#       - a citation record (see tools/cache.py) containing markdown content
# Notes:
#   - readabilipy's use_readability=True mode shells out to Node.js for
#     better extraction quality, but hangs indefinitely (no clean
#     exception) if Node is missing or misconfigured, per a known upstream
#     issue (modelcontextprotocol/servers#4199). We probe for Node with
#     shutil.which before attempting readability mode, rather than
#     try/except around the call, per that issue's own recommended fix.
# ================================================================

import shutil
from urllib.parse import urlparse

import requests
from markdownify import markdownify as convert_to_markdown
from protego import Protego
from readabilipy import simple_json_from_html_string

from mcp_server.tools.cache import get_cached, store_snapshot

DEFAULT_USER_AGENT = (
    "vt-capstone-gtm-research-bot/0.1 "
    "(+https://github.com/VoxSecuritatis/VT-12-Capstone-Product_Strategy_Simulation)"
)
DEFAULT_MAX_AGE_SECONDS = 6 * 60 * 60


def node_available() -> bool:
    """Return True if a node executable is on PATH."""
    return shutil.which("node") is not None


def robots_allow(url: str, user_agent: str) -> bool:
    """Check robots.txt for url; default to allow if it can't be read."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = requests.get(robots_url, timeout=10, headers={"User-Agent": user_agent})
    except requests.RequestException:
        return True
    if response.status_code >= 400:
        return True
    robots = Protego.parse(response.text)
    return robots.can_fetch(url, user_agent)


def fetch_url(url: str, max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> dict:
    """Fetch url, convert it to markdown, and return a cited, timestamped snapshot."""
    cached = get_cached(url, max_age_seconds)
    if cached is not None:
        return cached.model_dump()

    user_agent = DEFAULT_USER_AGENT
    if not robots_allow(url, user_agent):
        raise PermissionError(f"robots.txt disallows fetching {url}")

    response = requests.get(url, timeout=20, headers={"User-Agent": user_agent})
    response.raise_for_status()

    use_readability = node_available()
    article = simple_json_from_html_string(response.text, use_readability=use_readability)
    html_content = article.get("content") or response.text
    markdown = convert_to_markdown(html_content, heading_style="ATX")

    entry = store_snapshot(
        url=url,
        source_tool="fetch",
        content=markdown,
        extra={"title": article.get("title", ""), "used_readability": use_readability},
    )
    return entry.model_dump()
