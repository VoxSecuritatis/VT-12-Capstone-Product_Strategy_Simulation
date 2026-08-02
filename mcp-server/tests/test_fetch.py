import pytest

import mcp_server.tools.fetch as fetch_module


class FakeResponse:
    def __init__(self, text: str = "", status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise fetch_module.requests.HTTPError(f"status {self.status_code}")


def test_robots_allow_defaults_true_on_network_error(monkeypatch):
    def fake_get(url, timeout=None, headers=None):
        raise fetch_module.requests.RequestException("no network")

    monkeypatch.setattr(fetch_module.requests, "get", fake_get)
    assert fetch_module.robots_allow("https://example.com/page", "test-agent") is True


def test_fetch_url_returns_markdown_snapshot(monkeypatch):
    monkeypatch.setattr(fetch_module, "node_available", lambda: False)

    html_page = "<html><body><h1>Title</h1><p>Body text</p></body></html>"
    robots_txt = "User-agent: *\nAllow: /\n"

    def fake_get(url, timeout=None, headers=None):
        if url.endswith("robots.txt"):
            return FakeResponse(text=robots_txt)
        return FakeResponse(text=html_page)

    monkeypatch.setattr(fetch_module.requests, "get", fake_get)

    result = fetch_module.fetch_url("https://example.com/page")
    assert "Title" in result["content"]
    assert result["url"] == "https://example.com/page"
    assert result["citation_id"]


def test_fetch_url_raises_when_robots_disallow(monkeypatch):
    monkeypatch.setattr(fetch_module, "node_available", lambda: False)
    robots_txt = "User-agent: *\nDisallow: /\n"

    def fake_get(url, timeout=None, headers=None):
        return FakeResponse(text=robots_txt)

    monkeypatch.setattr(fetch_module.requests, "get", fake_get)

    with pytest.raises(PermissionError):
        fetch_module.fetch_url("https://example.com/private")
