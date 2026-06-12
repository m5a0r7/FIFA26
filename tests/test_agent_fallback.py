import unittest

try:
    from backend.app.agents import WorldCupAgent
except ModuleNotFoundError:
    WorldCupAgent = None


@unittest.skipIf(WorldCupAgent is None, "Backend runtime dependencies are not installed.")
class AgentFallbackTest(unittest.IsolatedAsyncioTestCase):
    async def test_prediction_question_returns_prediction_payload(self) -> None:
        response = await WorldCupAgent().answer("/predict Brazil vs Germany", session_id="test")

        self.assertEqual(response.mode, "prediction")
        self.assertIn("prediction", response.data)
        self.assertIn("Brazil win", response.answer)

    async def test_help_question_returns_supported_teams(self) -> None:
        response = await WorldCupAgent().answer("/help")

        self.assertEqual(response.mode, "help")
        self.assertIn("teams", response.data)

    async def test_next_match_question_returns_next_loaded_date(self) -> None:
        class FakeTools:
            def get_next_matches(self) -> list[dict[str, object]]:
                return [
                    {
                        "date": "2026-06-12",
                        "team_a": "Canada",
                        "team_b": "Bosnia and Herzegovina",
                    }
                ]

            def get_data_freshness(self) -> dict[str, object]:
                return {"source": "test", "stale": False}

        response = await WorldCupAgent(FakeTools()).answer("When is the next match?")

        self.assertEqual(response.mode, "facts")
        self.assertIn("matches", response.data)
        self.assertGreater(len(response.data["matches"]), 0)
        self.assertNotIn("Mexico vs South Africa", response.answer)
        self.assertIn("Canada vs Bosnia and Herzegovina", response.answer)

    async def test_result_question_does_not_invent_score(self) -> None:
        response = await WorldCupAgent().answer("Who won Canada vs Bosnia and Herzegovina?")

        self.assertEqual(response.mode, "facts")
        self.assertIn("result", response.data)
        self.assertIn("do not have a confirmed", response.answer)
        self.assertIn("winner", response.answer)


if __name__ == "__main__":
    unittest.main()
