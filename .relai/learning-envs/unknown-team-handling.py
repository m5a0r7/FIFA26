"""RELAI learning environment for unknown-team handling in prediction requests."""

from __future__ import annotations

import re
import sys
from difflib import get_close_matches
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


TAGS = ["end-to-end", "unknown-team-clear-disclosure-helpful-options"]
UNKNOWN_TEAM = "Braziii"
OPPONENT_TEAM = "Germany"
PROMPT = f"/predict {UNKNOWN_TEAM} vs {OPPONENT_TEAM}"
AVAILABLE_TEAMS = FootballTools().list_teams()
SUGGESTED_TEAMS = get_close_matches(UNKNOWN_TEAM, AVAILABLE_TEAMS, n=2, cutoff=0.6)
SUGGESTION_CUES = (
    "did you mean",
    "maybe you meant",
    "perhaps you meant",
    "were you asking for",
    "you might mean",
    "try",
    "use",
)
UNKNOWN_CUES = (
    "unknown",
    "not found",
    "don't recognize",
    "do not recognize",
    "couldn't find",
    "could not find",
    "invalid team",
)
NORMAL_ANSWER_PATTERNS = (
    r"\bwin:\s*\d",
    r"\bdraw:\s*\d",
    r"\bconfidence\b",
    r"\bready for comparison\b",
    r"\bpredic",
)


def _final_output_text(simulation_result: Any) -> str:
    final_output = getattr(simulation_result, "final_output", None)
    if final_output is None and isinstance(simulation_result, dict):
        final_output = simulation_result.get("final_output")
    return "" if final_output is None else str(final_output).strip()


def _mentions_unknown_team(answer_lower: str) -> bool:
    refers_to_problem_team = UNKNOWN_TEAM.lower() in answer_lower or any(
        phrase in answer_lower for phrase in ("that team", "first team", "team name")
    )
    return refers_to_problem_team and any(cue in answer_lower for cue in UNKNOWN_CUES)


def _count_named_team_mentions(answer_lower: str) -> int:
    mentions = 0
    for team in AVAILABLE_TEAMS:
        if team.lower() in answer_lower:
            mentions += 1
    return mentions


def _offers_helpful_recovery(answer_lower: str) -> bool:
    if "available team" in answer_lower or "available teams" in answer_lower:
        return True
    if _count_named_team_mentions(answer_lower) >= 3:
        return True
    if any(team.lower() in answer_lower for team in SUGGESTED_TEAMS) and any(
        cue in answer_lower for cue in SUGGESTION_CUES
    ):
        return True
    return False


def _silently_treats_typo_as_valid(answer: str, answer_lower: str) -> bool:
    if _mentions_unknown_team(answer_lower):
        return False
    return any(re.search(pattern, answer_lower) for pattern in NORMAL_ANSWER_PATTERNS)


def evaluate_unknown_team_handling(simulation_result: Any) -> EvaluationResult:
    answer = _final_output_text(simulation_result)
    expected_help = (
        f"Expected the reply to clearly say '{UNKNOWN_TEAM}' is unknown and then either list valid teams "
        f"or suggest a correction such as {', '.join(SUGGESTED_TEAMS) or 'a close valid team name'}."
    )
    if not answer:
        return EvaluationResult(
            score=0.0,
            feedback=f"The agent did not answer the typo request. {expected_help}",
        )

    answer_lower = answer.lower()
    issues: list[str] = []
    satisfied_checks = 0

    if _mentions_unknown_team(answer_lower):
        satisfied_checks += 1
    else:
        issues.append(
            f"The reply does not clearly state that '{UNKNOWN_TEAM}' is an unknown team. Observed answer: {answer}"
        )

    if _offers_helpful_recovery(answer_lower):
        satisfied_checks += 1
    else:
        issues.append(
            f"The reply does not offer helpful recovery guidance. Expected a valid-team list or a correction such as {', '.join(SUGGESTED_TEAMS) or 'a close valid team name'}, but observed: {answer}"
        )

    if _silently_treats_typo_as_valid(answer, answer_lower):
        issues.append(
            f"The reply appears to continue as a normal prediction or comparison instead of stopping on the unknown team '{UNKNOWN_TEAM}'. Observed answer: {answer}"
        )
    else:
        satisfied_checks += 1

    score = satisfied_checks / 3
    if issues:
        return EvaluationResult(
            score=score,
            feedback=f"{' '.join(issues)} {expected_help}",
        )

    return EvaluationResult(
        score=1.0,
        feedback=(
            f"The reply clearly marks '{UNKNOWN_TEAM}' as unknown, offers recovery help, and does not silently treat the typo as a confirmed team."
        ),
    )


environment = RELAIEnvironment(
    schema_version="relai.learning_environment.v1",
    id="unknown-team-handling",
    name="Unknown Team Recovery",
    description="Tests whether the agent clearly handles an unknown team name and offers helpful recovery guidance.",
    tags=["end-to-end", "unknown-team-clear-disclosure-helpful-options"],
    input=FixedInput(
        turns=[
            FixedTurn(content=PROMPT),
        ]
    ),
    mocks={},
    evaluators=[
        CodeEvaluator(
            id="unknown-team-disclosure-and-recovery",
            description="Checks that the reply clearly flags the unknown team and offers helpful next-step guidance.",
            evaluate=evaluate_unknown_team_handling,
        )
    ],
)
