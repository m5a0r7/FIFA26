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

    def test_next_matches_skip_past_seed_fixtures(self) -> None:
        matches = FootballTools().get_next_matches("2026-06-12")

        self.assertEqual({match["date"] for match in matches}, {"2026-06-12"})
        self.assertIn(
            ("Canada", "Bosnia and Herzegovina"),
            {(match["team_a"], match["team_b"]) for match in matches},
        )
        self.assertNotIn(
            ("Mexico", "South Africa"),
            {(match["team_a"], match["team_b"]) for match in matches},
        )

    def test_extract_matchup_prefers_known_team_names_in_long_questions(self) -> None:
        matchup = FootballTools().extract_matchup(
            "According to your schedule, what is the live score for Canada vs Bosnia and Herzegovina on 2026-06-12, and who won?"
        )

        self.assertEqual(matchup, ("Canada", "Bosnia and Herzegovina"))

    def test_prediction_accepts_common_team_aliases(self) -> None:
        prediction = FootballTools().predict_match("United States", "Turkey")

        self.assertEqual(prediction["team_a"], "USA")
        self.assertEqual(prediction["team_b"], "Turkiye")

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
