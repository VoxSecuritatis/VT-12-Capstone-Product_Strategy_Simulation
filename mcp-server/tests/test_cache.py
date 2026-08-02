from datetime import datetime, timedelta, timezone

from mcp_server.tools import cache as cache_module
from mcp_server.tools.cache import get_cached, store_snapshot


def test_store_snapshot_writes_and_returns_entry():
    entry = store_snapshot(url="https://example.com", source_tool="fetch", content="hello")
    assert entry.url == "https://example.com"
    assert entry.content == "hello"
    assert entry.citation_id


def test_get_cached_returns_none_when_missing():
    assert get_cached("https://example.com/missing", max_age_seconds=3600) is None


def test_get_cached_returns_fresh_entry():
    store_snapshot(url="https://example.com", source_tool="fetch", content="hello")
    cached = get_cached("https://example.com", max_age_seconds=3600)
    assert cached is not None
    assert cached.content == "hello"


def test_get_cached_returns_none_when_stale():
    entry = store_snapshot(url="https://example.com", source_tool="fetch", content="hello")
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=7200)
    stale_entry = entry.model_copy(update={"fetched_at": stale_time.isoformat()})
    path = cache_module.CACHE_DIR / f"{entry.citation_id}.json"
    path.write_text(stale_entry.model_dump_json(indent=2), encoding="utf-8")

    assert get_cached("https://example.com", max_age_seconds=3600) is None
