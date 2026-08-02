# ================================================================
# Cache and Citation Store
# ================================================================
# Objective:
#       Give every fetched or searched piece of evidence a stable citation
#       ID and a timestamped snapshot on disk, so downstream agents can
#       cite a source and so repeated lookups within max_age_seconds reuse
#       the snapshot instead of re-fetching (source-volatility mitigation).
# Inputs:
#       - url: the source URL a snapshot is keyed on
#       - content: the text/markdown to persist for that URL
# Outputs:
#       - one JSON file per citation under .cache/, keyed by a hash of the URL
# Notes:
#   - This server owns all local file I/O for research evidence. n8n cannot
#     write local files directly (Code node sandboxes fs, Write to File
#     needs binary input), so caching must live here, not in n8n.
# ================================================================

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".cache"


class CacheEntry(BaseModel):
    citation_id: str
    url: str
    source_tool: str
    fetched_at: str
    content: str
    extra: dict[str, Any] = {}


def cache_key(url: str) -> str:
    """Return a stable, filesystem-safe citation ID for a URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def get_cached(url: str, max_age_seconds: int) -> CacheEntry | None:
    """Return a fresh cached snapshot for url, or None if missing/stale."""
    path = CACHE_DIR / f"{cache_key(url)}.json"
    if not path.exists():
        return None

    entry = CacheEntry.model_validate_json(path.read_text(encoding="utf-8"))
    fetched_at = datetime.fromisoformat(entry.fetched_at)
    if datetime.now(timezone.utc) - fetched_at > timedelta(seconds=max_age_seconds):
        return None
    return entry


def store_snapshot(
    url: str, source_tool: str, content: str, extra: dict[str, Any] | None = None
) -> CacheEntry:
    """Persist a timestamped, cited snapshot of content for url and return it."""
    entry = CacheEntry(
        citation_id=cache_key(url),
        url=url,
        source_tool=source_tool,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        content=content,
        extra=extra or {},
    )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{entry.citation_id}.json"
    path.write_text(json.dumps(entry.model_dump(), indent=2), encoding="utf-8")
    return entry
