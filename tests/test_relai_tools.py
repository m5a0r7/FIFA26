import tempfile
import unittest
from pathlib import Path

from backend.app.data.cache import get_cached_matches, get_match_cache_status, save_match_cache
from backend.app.relai_tools import _run_smoke_checks
from backend.app.tools import FootballTools


class RelaiToolsTest(unittest.TestCase):
    def test_seed_schedule_has_no_tbd(self) -> None:
        matches = FootballTools().get_match_schedule()

        self.assertGreater(len(matches), 0)
        self.assertFalse(any("TBD" in {match.get("team_a"), match.get("team_b")} for match in matches))

    def test_cache_status_tracks_written_matches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matches.json"
            save_match_cache([{"team_a": "Mexico", "team_b": "South Africa"}], "test", path)

            status = get_match_cache_status(path)

            self.assertTrue(status["exists"])
            self.assertFalse(status["stale"])
            self.assertEqual(status["match_count"], 1)
            self.assertEqual(get_cached_matches(path), [{"team_a": "Mexico", "team_b": "South Africa"}])

    def test_relai_smoke_checks_pass(self) -> None:
        result = _run_smoke_checks()

        self.assertTrue(result["ok"], result["failures"])
        self.assertGreater(result["match_count"], 0)


if __name__ == "__main__":
    unittest.main()
