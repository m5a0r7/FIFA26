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


if __name__ == "__main__":
    unittest.main()
