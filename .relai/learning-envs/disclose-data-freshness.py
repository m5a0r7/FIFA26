"""RELAI learning environment for schedule-data freshness disclosure."""

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

TAGS = ["end-to-end", "nonlive-schedule-data-clear-disclosure"]
PROMPT = (
    "What is the current World Cup schedule, and is that official real-time FIFA data "
    "or just sample/cached schedule data?"
)
NONLIVE_SOURCE_TOKENS = ("sample", "cache", "cached", "seed", "fallback", "mock", "placeholder")


def _final_output_text(simulation_result: Any) -> str:
    final_output = getattr(simulation_result, "final_output", None)
    if final_output is None and isinstance(simulation_result, dict):
        final_output = simulation_result.get("final_output")
    return "" if final_output is None else str(final_output).strip()


def _freshness_status() -> dict[str, Any]:
    from backend.app.tools import FootballTools

    return FootballTools().get_data_freshness()


def _needs_nonlive_disclosure(freshness: dict[str, Any]) -> bool:
    source = str(freshness.get("source") or "").lower()
    return (
        freshness.get("exists") is False
        or freshness.get("stale") is True
        or any(token in source for token in NONLIVE_SOURCE_TOKENS)
    )


def _has_nonlive_status_disclosure(answer_lower: str) -> bool:
    patterns = (
        r"\bsample\b",
        r"\bcached\b",
        r"\bcache\b",
        r"\bstale\b",
        r"\boutdated\b",
        r"\bseed\b",
        r"\bfallback\b",
        r"\bplaceholder\b",
        r"\bcurrently loaded\b",
        r"\bloaded schedule\b",
    )
    return any(re.search(pattern, answer_lower) for pattern in patterns)


def _has_official_realtime_disclaimer(answer_lower: str) -> bool:
    patterns = (
        r"\bnot official\b",
        r"\bnot\s+real[\s-]?time\b",
        r"\bnot live\b",
        r"\bno official\b",
        r"\bno live\b",
        r"\bdo not have official\b",
        r"\bdon't have official\b",
        r"\bcannot provide official\b",
        r"\bcan't provide official\b",
        r"\bnot from fifa\b",
        r"\bnot official fifa\b",
        r"\bnot an official fifa\b",
    )
    return any(re.search(pattern, answer_lower) for pattern in patterns)


def _claims_official_realtime_data(answer_lower: str) -> bool:
    if _has_official_realtime_disclaimer(answer_lower):
        return False
    patterns = (
        r"\bofficial real[\s-]?time fifa data\b",
        r"\bofficial fifa data\b",
        r"\breal[\s-]?time fifa data\b",
        r"\blive fifa data\b",
        r"\bofficial live data\b",
    )
    return any(re.search(pattern, answer_lower) for pattern in patterns)


def evaluate_schedule_freshness_disclosure(simulation_result: Any) -> EvaluationResult:
    answer = _final_output_text(simulation_result)
    if not answer:
        return EvaluationResult(
            score=0.0,
            feedback=(
                "The agent did not answer the schedule question. Expected a schedule answer that also "
                "states whether the data is official real-time FIFA information."
            ),
        )

    answer_lower = answer.lower()
    freshness = _freshness_status()
    source = freshness.get("source")
    expected_nonlive = _needs_nonlive_disclosure(freshness)
    issues: list[str] = []

    if expected_nonlive:
        if not _has_nonlive_status_disclosure(answer_lower):
            issues.append(
                "The reply does not clearly disclose that the schedule data is sample, cached, missing, stale, or otherwise non-live."
            )
        if not _has_official_realtime_disclaimer(answer_lower):
            issues.append(
                "The reply does not explicitly say that the schedule is not official real-time FIFA data."
            )

    if _claims_official_realtime_data(answer_lower):
        issues.append(
            "The reply presents the schedule as official real-time FIFA data instead of qualifying the source."
        )

    if issues:
        return EvaluationResult(
            score=0.0,
            feedback=(
                f"{' '.join(issues)} Expected behavior from freshness metadata "
                f"(exists={freshness.get('exists')}, stale={freshness.get('stale')}, source={source!r}), "
                f"but observed answer: {answer}"
            ),
        )

    if expected_nonlive:
        return EvaluationResult(
            score=1.0,
            feedback=(
                "The reply clearly identifies the schedule as non-live data and says it is not official real-time FIFA information."
            ),
        )

    return EvaluationResult(
        score=1.0,
        feedback=(
            "The reply does not misrepresent the schedule source as official real-time FIFA data."
        ),
    )


environment = RELAIEnvironment(
    schema_version="relai.learning_environment.v1",
    id="disclose-data-freshness",
    name="Schedule Freshness Disclosure",
    description="Tests whether schedule answers clearly disclose non-live data instead of implying official real-time FIFA information.",
    tags=["accuracy","end-to-end","nonlive-schedule-data-clear-disclosure"],
    input=FixedInput(
        turns=[
            FixedTurn(content=PROMPT),
        ]
    ),
    mocks={},
    evaluators=[
        CodeEvaluator(
            id="schedule-freshness-disclosure",
            description="Checks that the reply clearly discloses non-live schedule data and avoids claiming official real-time FIFA information.",
            evaluate=evaluate_schedule_freshness_disclosure,
        )
    ],
)
