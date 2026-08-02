import pytest

from mcp_server.tools import cache as cache_module


@pytest.fixture(autouse=True)
def isolate_cache_dir(tmp_path, monkeypatch):
    """Redirect the citation cache to a throwaway directory for every test."""
    monkeypatch.setattr(cache_module, "CACHE_DIR", tmp_path / ".cache")
