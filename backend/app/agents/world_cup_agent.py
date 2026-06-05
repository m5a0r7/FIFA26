from __future__ import annotations

import os
from typing import Any

from backend.app.schemas import ChatResponse
from backend.app.tools import FootballTools

try:
    from agents import Agent, Runner, function_tool
except Exception:  # pragma: no cover - optional dependency path
    Agent = None
    Runner = None
    function_tool = None


class WorldCupAgent:
    def __init__(self, tools: FootballTools | None = None) -> None:
        self.tools = tools or FootballTools()
        self._sdk_agent = self._build_sdk_agent()

    async def answer(self, message: str, session_id: str | None = None) -> ChatResponse:
        if self._sdk_agent and Runner and os.getenv("OPENAI_API_KEY"):
            try:
                result = await Runner.run(self._sdk_agent, message)
                return ChatResponse(answer=str(result.final_output), mode="analysis", data={"session_id": session_id})
            except Exception:
                # Keep the product usable in local/dev environments if the SDK path fails.
                pass

        return self._fallback_answer(message, session_id)

    def _fallback_answer(self, message: str, session_id: str | None) -> ChatResponse:
        lowered = message.lower().strip()

        if lowered.startswith("/start") or lowered.startswith("/help") or lowered in {"help", "hi", "hello"}:
            teams = ", ".join(self.tools.list_teams()[:8])
            return ChatResponse(
                answer=(
                    "Ask me for match schedules, standings, team profiles, or predictions. "
                    f"Try: /predict Brazil vs Germany. Available sample teams include {teams}."
                ),
                mode="help",
                data={"session_id": session_id, "teams": self.tools.list_teams()},
            )

        if "predict" in lowered or "chance" in lowered or lowered.startswith("/predict"):
            matchup = self.tools.extract_matchup(message)
            if not matchup:
                return ChatResponse(
                    answer="Tell me the matchup, for example: /predict Brazil vs Germany.",
                    mode="prediction",
                    data={"session_id": session_id},
                )
            try:
                prediction = self.tools.predict_match(*matchup)
            except ValueError as error:
                return ChatResponse(answer=str(error), mode="prediction", data={"session_id": session_id})
            return ChatResponse(
                answer=self._prediction_text(prediction),
                mode="prediction",
                data={"prediction": prediction, "session_id": session_id},
            )

        if "standing" in lowered or lowered.startswith("/standings"):
            standings = self.tools.get_group_standings()
            return ChatResponse(
                answer="Current sample standings are pre-tournament placeholders until live data is connected.",
                mode="facts",
                data={"standings": standings, "session_id": session_id},
            )

        if "today" in lowered or "schedule" in lowered or "next" in lowered or lowered.startswith("/today"):
            matches = self.tools.get_match_schedule()
            return ChatResponse(
                answer="Here are the sample scheduled matches currently loaded.",
                mode="facts",
                data={"matches": matches, "session_id": session_id},
            )

        if "compare" in lowered or lowered.startswith("/compare"):
            matchup = self.tools.extract_matchup(message)
            if not matchup:
                return ChatResponse(
                    answer="Tell me two teams to compare, for example: /compare France Argentina.",
                    mode="analysis",
                    data={"session_id": session_id},
                )
            profiles = [self.tools.get_team_profile(team) for team in matchup]
            return ChatResponse(
                answer=f"{profiles[0]['name']} and {profiles[1]['name']} are ready for comparison.",
                mode="analysis",
                data={"teams": profiles, "session_id": session_id},
            )

        return ChatResponse(
            answer="I can help with schedules, standings, team comparisons, and match predictions.",
            mode="help",
            data={"session_id": session_id},
        )

    def _build_sdk_agent(self) -> Any | None:
        if Agent is None or function_tool is None:
            return None

        tools = self.tools

        @function_tool
        def predict_match(team_a: str, team_b: str) -> dict[str, Any]:
            """Predict win/draw/loss probabilities for a football matchup."""
            return tools.predict_match(team_a, team_b)

        @function_tool
        def get_team_profile(team_name: str) -> dict[str, Any]:
            """Fetch the current team profile from the app data layer."""
            return tools.get_team_profile(team_name)

        @function_tool
        def get_match_schedule(team_name: str | None = None) -> list[dict[str, Any]]:
            """Fetch sample schedule data, optionally filtered by team."""
            return tools.get_match_schedule(team_name)

        return Agent(
            name="WorldCupAgent",
            instructions=(
                "You are a FIFA World Cup 2026 football intelligence assistant. "
                "Use tools for schedules, team data, and predictions. "
                "Never invent live results. Say when data is sample or stale. "
                "Predictions must be framed as probabilities, not guarantees."
            ),
            tools=[predict_match, get_team_profile, get_match_schedule],
        )

    @staticmethod
    def _prediction_text(prediction: dict[str, Any]) -> str:
        team_a = prediction["team_a"]
        team_b = prediction["team_b"]
        a_pct = round(float(prediction["team_a_win"]) * 100)
        draw_pct = round(float(prediction["draw"]) * 100)
        b_pct = round(float(prediction["team_b_win"]) * 100)
        factors = " ".join(str(factor) for factor in prediction["top_factors"])
        return (
            f"{team_a} win: {a_pct}%, draw: {draw_pct}%, {team_b} win: {b_pct}%. "
            f"Confidence is {prediction['confidence']}. {factors}"
        ).strip()
