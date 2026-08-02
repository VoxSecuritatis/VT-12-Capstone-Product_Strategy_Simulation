# ================================================================
# MCP Server Entrypoint
# ================================================================
# Objective:
#       Register the shared research tools (search, fetch) and serve them
#       over real MCP protocol via SSE transport, so both n8n's MCP
#       Client Tool node and CrewAI's MCPServerAdapter can connect to the
#       same server natively.
# Inputs:
#       - .env: SERPAPI_API_KEY (required), MCP_SERVER_HOST/PORT (optional)
# Outputs:
#       - a running MCP server exposing the "search" and "fetch" tools
# Notes:
#   - Never read/write .env directly here; python-dotenv loads it into the
#     process environment, and tools read values via os.environ.
# ================================================================

import os

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from mcp_server.tools.fetch import fetch_url
from mcp_server.tools.search import search_web

load_dotenv()

mcp_server = MCPServer(
    name="capstone-gtm-research-mcp",
    instructions=(
        "Research tools (search, fetch, citation tracking) shared by the n8n "
        "and CrewAI GTM planning implementations."
    ),
)


@mcp_server.tool()
def search(query: str, num_results: int = 5) -> list[dict]:
    """Search the web via SerpAPI and return cited results."""
    return [result.model_dump() for result in search_web(query, num_results)]


@mcp_server.tool()
def fetch(url: str) -> dict:
    """Fetch a URL, convert it to markdown, and return a cited, timestamped snapshot."""
    return fetch_url(url)


def main() -> None:
    """Run the MCP server over SSE transport."""
    host = os.environ.get("MCP_SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_SERVER_PORT", "8000"))
    mcp_server.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
