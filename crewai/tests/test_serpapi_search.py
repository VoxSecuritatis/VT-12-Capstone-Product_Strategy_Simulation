import pytest

import tools.serpapi_search as serpapi_search_module
from tools.serpapi_search import SerpApiSearchTool


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self.payload


def test_run_returns_formatted_results(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    payload = {
        "organic_results": [
            {"title": "Example", "link": "https://example.com", "snippet": "An example site"},
        ]
    }

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(serpapi_search_module.requests, "get", fake_get)

    result = SerpApiSearchTool()._run("example query", num_results=5)
    assert "Example" in result
    assert "https://example.com" in result
    assert "An example site" in result


def test_run_requires_api_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        SerpApiSearchTool()._run("example query")


def test_run_no_results(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    payload: dict = {"organic_results": []}

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(serpapi_search_module.requests, "get", fake_get)

    result = SerpApiSearchTool()._run("no results query")
    assert "No results found for query: no results query" == result
