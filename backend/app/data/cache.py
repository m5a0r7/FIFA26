from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_MATCH_CACHE_PATH = Path("data/cache/worldcup_2026_matches.json")
DEFAULT_MAX_AGE_MINUTES = 60


def save_match_cache(
    matches: list[dict[str, Any]],
    source: str,
    path: Path = DEFAULT_MATCH_CACHE_PATH,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": source,
        "synced_at": datetime.now(UTC).isoformat(),
        "matches": matches,
    }
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temporary_path.replace(path)
    return get_match_cache_status(path=path)


def load_match_cache(path: Path = DEFAULT_MATCH_CACHE_PATH) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_cached_matches(path: Path = DEFAULT_MATCH_CACHE_PATH) -> list[dict[str, Any]] | None:
    payload = load_match_cache(path)
    if not payload:
        return None
    matches = payload.get("matches")
    if not isinstance(matches, list):
        return None
    return matches


def get_match_cache_status(
    path: Path = DEFAULT_MATCH_CACHE_PATH,
    max_age_minutes: int = DEFAULT_MAX_AGE_MINUTES,
) -> dict[str, Any]:
    payload = load_match_cache(path)
    if not payload:
        return {
            "exists": False,
            "stale": True,
            "source": None,
            "synced_at": None,
            "age_seconds": None,
            "max_age_minutes": max_age_minutes,
            "match_count": 0,
            "path": str(path),
        }

    synced_at_raw = payload.get("synced_at")
    synced_at = _parse_datetime(synced_at_raw)
    age_seconds = None
    stale = True
    if synced_at:
        age_seconds = max(0, int((datetime.now(UTC) - synced_at).total_seconds()))
        stale = age_seconds > max_age_minutes * 60

    matches = payload.get("matches")
    match_count = len(matches) if isinstance(matches, list) else 0
    return {
        "exists": True,
        "stale": stale,
        "source": payload.get("source"),
        "synced_at": synced_at_raw,
        "age_seconds": age_seconds,
        "max_age_minutes": max_age_minutes,
        "match_count": match_count,
        "path": str(path),
    }


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
