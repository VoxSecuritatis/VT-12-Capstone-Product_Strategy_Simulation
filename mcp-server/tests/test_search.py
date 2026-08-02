import pytest

import mcp_server.tools.search as search_module
from mcp_server.tools.search import search_web


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self.payload


def test_search_web_returns_cited_results(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    payload = {
        "organic_results": [
            {"title": "Example", "link": "https://example.com", "snippet": "An example site"},
        ]
    }

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(search_module.requests, "get", fake_get)

    results = search_web("example query", num_results=5)
    assert len(results) == 1
    assert results[0].title == "Example"
    assert results[0].link == "https://example.com"
    assert results[0].citation_id


def test_search_web_requires_api_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        search_web("example query")
