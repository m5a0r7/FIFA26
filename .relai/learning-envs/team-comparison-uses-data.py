"""RELAI learning environment for profile-grounded team comparison answers."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from relai import CodeEvaluator
from relai import EvaluationResult
from relai import FixedInput
from relai import FixedTurn
from relai import RELAIEnvironment


PROJECT_ROOT = Path(__file__).resolve().parent / "project"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.tools import FootballTools


TAGS = ["end-to-end", "team-comparison-profile-grounding-visible-factors"]
TEAM_A = "France"
TEAM_B = "USA"
PROMPT = f"/compare {TEAM_A} vs {TEAM_B}"
TOOLS = FootballTools()
TEAM_A_PROFILE = TOOLS.get_team_profile(TEAM_A)
TEAM_B_PROFILE = TOOLS.get_team_profile(TEAM_B)
TARGET_TEAMS = (TEAM_A, TEAM_B)
PROFILE_TOOL_NAME = "get_team_profile"
MIN_FACTOR_COUNT = 4

FACTOR_SPECS = (
    {
        "id": "elo",
        "label": "Elo rating",
        "cues": ("elo",),
        "values": (str(TEAM_A_PROFILE["elo"]), str(TEAM_B_PROFILE["elo"])),
    },
    {
        "id": "fifa-rank",
        "label": "FIFA rank",
        "cues": ("fifa", "rank", "ranking"),
        "values": (str(TEAM_A_PROFILE["fifa_rank"]), str(TEAM_B_PROFILE["fifa_rank"])),
    },
    {
        "id": "squad-quality",
        "label": "squad quality",
        "cues": ("squad", "quality", "talent"),
        "values": (str(TEAM_A_PROFILE["squad_quality"]), str(TEAM_B_PROFILE["squad_quality"])),
    },
    {
        "id": "recent-form",
        "label": "recent form",
        "cues": ("form", "momentum"),
        "values": (
            str(TEAM_A_PROFILE["recent_form_points"]),
            str(TEAM_B_PROFILE["recent_form_points"]),
        ),
    },
    {
        "id": "recent-goals",
        "label": "recent goals",
        "cues": ("goal", "goals", "scoring", "attack", "defense", "defence", "conced"),
        "values": (
            str(TEAM_A_PROFILE["goals_for_last5"]),
            str(TEAM_A_PROFILE["goals_against_last5"]),
            str(TEAM_B_PROFILE["goals_for_last5"]),
            str(TEAM_B_PROFILE["goals_against_last5"]),
        ),
    },
    {
        "id": "injuries",
        "label": "injuries",
        "cues": ("injur", "injuries"),
        "values": (str(TEAM_A_PROFILE["injuries"]), str(TEAM_B_PROFILE["injuries"])),
    },
    {
        "id": "suspensions",
        "label": "suspensions",
        "cues": ("suspension", "suspended"),
        "values": (str(TEAM_A_PROFILE["suspensions"]), str(TEAM_B_PROFILE["suspensions"])),
    },
    {
        "id": "experience",
        "label": "tournament experience",
        "cues": ("experience", "tournament"),
        "values": (
            str(TEAM_A_PROFILE["tournament_experience"]),
            str(TEAM_B_PROFILE["tournament_experience"]),
        ),
    },
    {
        "id": "host-status",
        "label": "host status",
        "cues": ("host", "home advantage", "home-field", "home field", "home soil"),
        "values": (),
    },
)


def _final_output_text(simulation_result: Any) -> str:
    final_output = getattr(simulation_result, "final_output", None)
    if final_output is None and isinstance(simulation_result, dict):
        final_output = simulation_result.get("final_output")
    return "" if final_output is None else str(final_output).strip()


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return " ".join(f"{key} {_stringify(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_stringify(item) for item in value)
    if hasattr(value, "__dict__"):
        return _stringify(vars(value))
    return str(value)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _extract_events(simulation_result: Any) -> list[Any]:
    candidates = [
        simulation_result,
        _get_value(simulation_result, "transcript"),
        _get_value(simulation_result, "result"),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        events = _get_value(candidate, "events")
        if isinstance(events, list):
            return events
        transcript = _get_value(candidate, "transcript")
        nested_events = _get_value(transcript, "events")
        if isinstance(nested_events, list):
            return nested_events
    return []


def _profile_tool_event_texts(simulation_result: Any) -> list[str]:
    texts: list[str] = []

    for event in _extract_events(simulation_result):
        event_type = str(_get_value(event, "type", _get_value(event, "event_type", "")) or "").lower()
        if event_type not in {"tool_call", "tool_result"}:
            continue
        name = str(_get_value(event, "name", _get_value(event, "tool_name", "")) or "")
        if name != PROFILE_TOOL_NAME:
            continue
        texts.append(_stringify(event).lower())

    direct_tool_calls = _get_value(simulation_result, "tool_calls")
    if not texts and isinstance(direct_tool_calls, list):
        for call in direct_tool_calls:
            name = str(_get_value(call, "name", _get_value(call, "tool_name", "")) or "")
            if name == PROFILE_TOOL_NAME:
                texts.append(_stringify(call).lower())

    return texts


def _teams_seen_in_profile_events(profile_event_texts: list[str]) -> set[str]:
    observed: set[str] = set()
    for team in TARGET_TEAMS:
        normalized_team = _normalize(team)
        if any(normalized_team in _normalize(text) for text in profile_event_texts):
            observed.add(team)
    return observed


def _answer_mentions_factor(answer_lower: str, spec: dict[str, Any]) -> bool:
    if not any(cue in answer_lower for cue in spec["cues"]):
        return False
    values = spec["values"]
    if not values:
        return True
    return any(value in answer_lower for value in values)


def evaluate_team_comparison(simulation_result: Any) -> EvaluationResult:
    answer = _final_output_text(simulation_result)
    if not answer:
        return EvaluationResult(
            score=0.0,
            feedback=(
                f"The agent did not answer the comparison request for {TEAM_A} vs {TEAM_B}. "
                "Expected a profile-backed comparison that fetches both teams and cites multiple concrete factors."
            ),
        )

    answer_lower = answer.lower()
    issues: list[str] = []
    satisfied_checks = 0

    missing_named_teams = [team for team in TARGET_TEAMS if team.lower() not in answer_lower]
    if missing_named_teams:
        issues.append(
            f"The reply does not clearly compare both requested teams by name. Missing: {', '.join(missing_named_teams)}."
        )
    else:
        satisfied_checks += 1

    profile_event_texts = _profile_tool_event_texts(simulation_result)
    observed_teams = _teams_seen_in_profile_events(profile_event_texts)
    if len(profile_event_texts) < 2:
        issues.append(
            f"The run did not show two {PROFILE_TOOL_NAME} lookups. Expected one profile fetch per team, but observed {len(profile_event_texts)} relevant tool events."
        )
    elif observed_teams and observed_teams != set(TARGET_TEAMS):
        issues.append(
            f"The transcript does not show profile fetches for both teams. Expected {TEAM_A} and {TEAM_B}, but observed {', '.join(sorted(observed_teams)) or 'unnamed profile calls'}."
        )
    else:
        satisfied_checks += 1

    matched_factors = [spec["label"] for spec in FACTOR_SPECS if _answer_mentions_factor(answer_lower, spec)]
    if len(matched_factors) < MIN_FACTOR_COUNT:
        issues.append(
            "The reply stays too generic and does not surface enough concrete profile-backed comparison factors. "
            f"Expected at least {MIN_FACTOR_COUNT} distinct factors such as Elo {TEAM_A_PROFILE['elo']} vs {TEAM_B_PROFILE['elo']}, "
            f"FIFA rank {TEAM_A_PROFILE['fifa_rank']} vs {TEAM_B_PROFILE['fifa_rank']}, squad quality {TEAM_A_PROFILE['squad_quality']} vs {TEAM_B_PROFILE['squad_quality']}, "
            f"recent form {TEAM_A_PROFILE['recent_form_points']} vs {TEAM_B_PROFILE['recent_form_points']}, "
            f"tournament experience {TEAM_A_PROFILE['tournament_experience']} vs {TEAM_B_PROFILE['tournament_experience']}, or {TEAM_B}'s host status. "
            f"Observed factors: {', '.join(matched_factors) or 'none'}."
        )
    else:
        satisfied_checks += 1

    if "ready for comparison" in answer_lower:
        issues.append(
            "The reply stops at a placeholder readiness statement instead of delivering the actual comparison."
        )
    else:
        satisfied_checks += 1

    score = satisfied_checks / 4
    if issues:
        return EvaluationResult(
            score=score,
            feedback=f"{' '.join(issues)} Observed answer: {answer}",
        )

    return EvaluationResult(
        score=1.0,
        feedback=(
            f"The reply fetches both team profiles for {TEAM_A} and {TEAM_B}, names both teams, "
            f"and compares them with at least {MIN_FACTOR_COUNT} concrete profile-backed factors."
        ),
    )


environment = RELAIEnvironment(
    schema_version="relai.learning_environment.v1",
    id="team-comparison-uses-data",
    name="Profile-Grounded Team Comparison",
    description="Tests whether a team comparison answer fetches both profiles and cites multiple concrete profile-backed factors.",
    tags=["end-to-end", "team-comparison-profile-grounding-visible-factors"],
    input=FixedInput(
        turns=[
            FixedTurn(content=PROMPT),
        ]
    ),
    mocks={},
    evaluators=[
        CodeEvaluator(
            id="comparison-uses-profile-data",
            description="Checks that the comparison fetches both team profiles and cites several concrete profile-backed factors.",
            evaluate=evaluate_team_comparison,
        )
    ],
)
