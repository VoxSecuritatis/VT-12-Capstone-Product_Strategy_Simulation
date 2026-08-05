import tools.mcp_fetch as mcp_fetch_module
from tools.mcp_fetch import MCP_SERVER_URL_DEFAULT, McpFetchTool


class FakeFetchTool:
    def __init__(self, content: str):
        self.content = content
        self.last_url = None

    def run(self, url: str) -> str:
        self.last_url = url
        return self.content


class FakeMCPServerAdapter:
    """Records the config it was constructed with and hands back a fake fetch tool."""

    last_server_params = None

    def __init__(self, server_params, tool_name):
        FakeMCPServerAdapter.last_server_params = server_params
        self.tool = FakeFetchTool("fetched content")

    def __enter__(self):
        return [self.tool]

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def test_run_fetches_and_returns_content(monkeypatch):
    monkeypatch.delenv("MCP_SERVER_URL", raising=False)
    monkeypatch.setattr(mcp_fetch_module, "MCPServerAdapter", FakeMCPServerAdapter)

    result = McpFetchTool()._run("https://example.com")

    assert result == "fetched content"
    assert FakeMCPServerAdapter.last_server_params == {"url": MCP_SERVER_URL_DEFAULT}


def test_run_uses_custom_server_url_env_var(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_URL", "http://127.0.0.1:9000/sse")
    monkeypatch.setattr(mcp_fetch_module, "MCPServerAdapter", FakeMCPServerAdapter)

    McpFetchTool()._run("https://example.com")

    assert FakeMCPServerAdapter.last_server_params == {"url": "http://127.0.0.1:9000/sse"}
