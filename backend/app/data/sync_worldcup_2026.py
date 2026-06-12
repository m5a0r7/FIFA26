from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backend.app.data.cache import DEFAULT_MATCH_CACHE_PATH, save_match_cache
from backend.app.data.mock_data import MATCHES


def sync_seed_schedule(output_path: Path = DEFAULT_MATCH_CACHE_PATH) -> dict[str, Any]:
    return save_match_cache(list(MATCHES), source="seed_worldcup_2026_schedule", path=output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync FIFA World Cup 2026 schedule data into the local cache.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_MATCH_CACHE_PATH),
        help="Path to write the match cache JSON.",
    )
    args = parser.parse_args()

    result = sync_seed_schedule(Path(args.output))
    print(json.dumps({"ok": True, "result": result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
