import unittest

from backend.app.prediction.engine import PredictionEngine, TeamSnapshot


class PredictionEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PredictionEngine()

    def test_probabilities_sum_to_one(self) -> None:
        prediction = self.engine.predict(
            TeamSnapshot("Team A", 2050, 5, 88, 11, 10, 4),
            TeamSnapshot("Team B", 1980, 18, 80, 8, 7, 6),
        )

        total = prediction.team_a_win + prediction.draw + prediction.team_b_win
        self.assertAlmostEqual(total, 1.0, places=3)

    def test_stronger_profile_gets_higher_win_probability(self) -> None:
        prediction = self.engine.predict(
            TeamSnapshot("Stronger", 2120, 2, 92, 13, 12, 3, tournament_experience=95),
            TeamSnapshot("Weaker", 1800, 45, 70, 5, 4, 10, injuries=3, tournament_experience=45),
        )

        self.assertGreater(prediction.team_a_win, prediction.team_b_win)
        self.assertEqual(prediction.confidence, "high")

    def test_host_advantage_can_move_close_matchup(self) -> None:
        neutral = self.engine.predict(
            TeamSnapshot("Host", 1900, 20, 78, 8, 7, 6, host=False),
            TeamSnapshot("Visitor", 1900, 20, 78, 8, 7, 6, host=False),
        )
        hosted = self.engine.predict(
            TeamSnapshot("Host", 1900, 20, 78, 8, 7, 6, host=True),
            TeamSnapshot("Visitor", 1900, 20, 78, 8, 7, 6, host=False),
        )

        self.assertGreater(hosted.team_a_win, neutral.team_a_win)


if __name__ == "__main__":
    unittest.main()
