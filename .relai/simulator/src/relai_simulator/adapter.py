from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.app.agents.world_cup_agent import Runner, WorldCupAgent
from backend.app.tools import FootballTools
from relai_simulator.adapter_contract import AgentAdapter
from relai_simulator.adapter_contract import AgentTurnResult
from relai_simulator.adapter_contract import ToolCallRecord, ToolResultRecord


def predict_match_component(team_a: str, team_b: str) -> dict[str, Any]:
    return FootballTools().predict_match(team_a, team_b)


def get_team_profile_component(team_name: str) -> dict[str, Any]:
    return FootballTools().get_team_profile(team_name)


def get_match_schedule_component(team_name: str | None = None) -> list[dict[str, Any]]:
    return FootballTools().get_match_schedule(team_name)


def get_data_freshness_component() -> dict[str, Any]:
    return FootballTools().get_data_freshness()


def get_group_standings_component(group: str | None = None) -> list[dict[str, Any]]:
    return FootballTools().get_group_standings(group)


class ProjectAgentAdapter:
    def __init__(self) -> None:
        self._recorder = _TurnToolRecorder()
        self._tools = _RecordingFootballTools(self._recorder)
        self._agent = WorldCupAgent(self._tools)
        self.agent_or_tools = getattr(self._agent, "_sdk_agent", None)
        self._enable_live_openai = os.getenv("RELAI_SIMULATOR_ENABLE_LIVE_OPENAI") == "1"

    async def run_turn(self, user_input: object) -> AgentTurnResult:
        turn = _coerce_turn_input(user_input)
        use_live_openai = (
            self._enable_live_openai
            and self.agent_or_tools is not None
            and Runner is not None
            and bool(os.getenv("OPENAI_API_KEY"))
        )
        self._recorder.start_turn()

        with _force_fallback_mode(enabled=not use_live_openai):
            response = await self._agent.answer(
                turn["message"],
                session_id=turn.get("session_id"),
            )

        tool_calls, tool_results = self._recorder.finish_turn()
        return AgentTurnResult(
            assistant_message=response.answer,
            metadata={
                "channel": turn.get("channel", "web"),
                "mode": response.mode,
                "data": response.data,
                "data_source": response.data_source,
                "execution_mode": "live_openai" if use_live_openai else "fallback",
                "live_openai_requested": self._enable_live_openai,
                "live_openai_used": use_live_openai,
                "sdk_agent_available": self.agent_or_tools is not None,
                "session_id": turn.get("session_id"),
            },
            tool_calls=tool_calls,
            tool_results=tool_results,
        )


def build_agent_adapter() -> AgentAdapter:
    return ProjectAgentAdapter()


@dataclass(slots=True)
class _TurnToolRecorder:
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    tool_results: list[ToolResultRecord] = field(default_factory=list)
    _call_index: int = 0

    def start_turn(self) -> None:
        self.tool_calls = []
        self.tool_results = []
        self._call_index = 0

    def finish_turn(self) -> tuple[list[ToolCallRecord], list[ToolResultRecord]]:
        return list(self.tool_calls), list(self.tool_results)

    def record(self, name: str, arguments: object, func: Callable[[], Any]) -> Any:
        call_id = f"{name}-{self._call_index}"
        self._call_index += 1
        self.tool_calls.append(
            ToolCallRecord(
                name=name,
                arguments=arguments,
                call_id=call_id,
            )
        )
        try:
            result = func()
        except Exception as error:
            self.tool_results.append(
                ToolResultRecord(
                    name=name,
                    error=f"{type(error).__name__}: {error}",
                    call_id=call_id,
                )
            )
            raise

        self.tool_results.append(
            ToolResultRecord(
                name=name,
                result=result,
                call_id=call_id,
            )
        )
        return result


class _RecordingFootballTools(FootballTools):
    def __init__(self, recorder: _TurnToolRecorder) -> None:
        super().__init__()
        self._recorder = recorder

    def predict_match(self, team_a: str, team_b: str) -> dict[str, Any]:
        return self._recorder.record(
            "predict_match",
            {"team_a": team_a, "team_b": team_b},
            lambda: FootballTools.predict_match(self, team_a, team_b),
        )

    def get_team_profile(self, team_name: str) -> dict[str, Any]:
        return self._recorder.record(
            "get_team_profile",
            {"team_name": team_name},
            lambda: FootballTools.get_team_profile(self, team_name),
        )

    def get_match_schedule(self, team_name: str | None = None) -> list[dict[str, Any]]:
        return self._recorder.record(
            "get_match_schedule",
            {"team_name": team_name},
            lambda: FootballTools.get_match_schedule(self, team_name),
        )

    def get_data_freshness(self) -> dict[str, Any]:
        return self._recorder.record(
            "get_data_freshness",
            {},
            lambda: FootballTools.get_data_freshness(self),
        )

    def get_group_standings(self, group: str | None = None) -> list[dict[str, Any]]:
        return self._recorder.record(
            "get_group_standings",
            {"group": group},
            lambda: FootballTools.get_group_standings(self, group),
        )


def _coerce_turn_input(user_input: object) -> dict[str, Any]:
    if isinstance(user_input, str):
        return {"message": user_input, "channel": "web", "session_id": None}

    if not isinstance(user_input, dict):
        raise TypeError("Simulator agent turns must be a string or an object with a 'message' field.")

    message = user_input.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Simulator agent turn objects must include a non-empty string 'message'.")

    session_id = user_input.get("session_id")
    channel = user_input.get("channel", "web")

    if session_id is not None and not isinstance(session_id, str):
        raise ValueError("'session_id' must be a string when provided.")
    if not isinstance(channel, str) or not channel.strip():
        raise ValueError("'channel' must be a non-empty string when provided.")

    return {
        "message": message,
        "session_id": session_id,
        "channel": channel,
    }


@contextmanager
def _force_fallback_mode(*, enabled: bool):
    if not enabled:
        yield
        return

    previous_api_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        yield
    finally:
        if previous_api_key is not None:
            os.environ["OPENAI_API_KEY"] = previous_api_key
