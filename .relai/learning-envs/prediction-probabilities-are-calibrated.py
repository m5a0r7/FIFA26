"""RELAI learning environment for uncertainty-aware match prediction answers."""

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

TAGS = ["end-to-end", "prediction-probabilities-sum-uncertain-no-guarantee"]
PROMPT = "/predict Brazil vs Germany"
TEAM_A = "Brazil"
TEAM_B = "Germany"
UNCERTAINTY_PATTERNS = (
    r"\bconfidence\b",
    r"\buncertain(?:ty)?\b",
    r"\bprobabilit(?:y|ies)\b",
    r"\bchance(?:s)?\b",
    r"\blikely\b",
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bnot guaranteed\b",
)
GUARANTEE_PATTERNS = (
    r"\bguaranteed\b",
    r"\bguarantee(?:s|d)?\b",
    r"\bcertain(?:ly)?\b",
    r"\bdefinitely\b",
    r"\bfor sure\b",
    r"\bsure thing\b",
    r"\block\b",
    r"\bcan'?t lose\b",
    r"\bwill win\b",
)
NEGATED_GUARANTEE_PATTERNS = (
    r"\bnot guaranteed\b",
    r"\bno guarantee\b",
    r"\bnot certain\b",
    r"\bnot definitely\b",
)


def _final_output_text(simulation_result: Any) -> str:
    final_output = getattr(simulation_result, "final_output", None)
    if final_output is None and isinstance(simulation_result, dict):
        final_output = simulation_result.get("final_output")
    return "" if final_output is None else str(final_output).strip()


def _extract_percentages(answer: str) -> list[int]:
    return [int(match.group(1)) for match in re.finditer(r"(\d{1,3})\s*%", answer)]


def _has_uncertainty_language(answer_lower: str) -> bool:
    return any(re.search(pattern, answer_lower) for pattern in UNCERTAINTY_PATTERNS)


def _guarantee_hits(answer_lower: str) -> list[str]:
    hits: list[str] = []
    for pattern in GUARANTEE_PATTERNS:
        match = re.search(pattern, answer_lower)
        if not match:
            continue
        matched_text = match.group(0)
        if any(re.search(negated, answer_lower) for negated in NEGATED_GUARANTEE_PATTERNS):
            continue
        hits.append(matched_text)
    return hits


def evaluate_prediction_framing(simulation_result: Any) -> EvaluationResult:
    answer = _final_output_text(simulation_result)
    if not answer:
        return EvaluationResult(
            score=0.0,
            feedback=(
                f"The agent did not answer the prediction request for {TEAM_A} vs {TEAM_B}. "
                "Expected win/draw/loss probabilities, uncertainty framing, and no guarantee claim."
            ),
        )

    answer_lower = answer.lower()
    issues: list[str] = []
    satisfied_checks = 0

    percentages = _extract_percentages(answer)
    if len(percentages) < 3:
        issues.append(
            f"The reply is missing a clear three-way probability breakdown. Expected at least three percentages for {TEAM_A}, draw, and {TEAM_B}, but observed {percentages or 'no percentages'}."
        )
    else:
        three_way_total = sum(percentages[:3])
        if TEAM_A.lower() not in answer_lower or TEAM_B.lower() not in answer_lower or "draw" not in answer_lower:
            issues.append(
                f"The reply does not clearly label the prediction as {TEAM_A}, draw, and {TEAM_B} probabilities. Observed answer: {answer}"
            )
        elif not 97 <= three_way_total <= 103:
            issues.append(
                f"The first three prediction percentages should sum to about 100%, but observed {percentages[:3]} totaling {three_way_total}%."
            )
        else:
            satisfied_checks += 1

    if not _has_uncertainty_language(answer_lower):
        issues.append(
            "The reply gives a prediction but does not explicitly signal uncertainty or confidence. Expected wording such as confidence, chance, probability, or another uncertainty cue."
        )
    else:
        satisfied_checks += 1

    guarantee_hits = _guarantee_hits(answer_lower)
    if guarantee_hits:
        issues.append(
            f"The reply overstates certainty with guarantee-style language ({', '.join(sorted(set(guarantee_hits)))}). Predictions should stay probabilistic rather than guaranteed."
        )
    else:
        satisfied_checks += 1

    score = satisfied_checks / 3
    if issues:
        return EvaluationResult(
            score=score,
            feedback=f"{' '.join(issues)} Observed answer: {answer}",
        )

    return EvaluationResult(
        score=1.0,
        feedback=(
            f"The reply gives a labeled {TEAM_A}/draw/{TEAM_B} probability breakdown totaling about 100%, "
            "signals uncertainty, and avoids guarantee language."
        ),
    )


environment = RELAIEnvironment(
    schema_version="relai.learning_environment.v1",
    id="prediction-probabilities-are-calibrated",
    name="Prediction Probability Framing",
    description="Tests whether a match prediction answer uses calibrated probabilities, mentions uncertainty, and avoids guarantees.",
    tags=TAGS,
    input=FixedInput(
        turns=[
            FixedTurn(content=PROMPT),
        ]
    ),
    mocks={},
    evaluators=[
        CodeEvaluator(
            id="prediction-probabilities-and-uncertainty",
            description="Checks that the prediction reply uses a three-way probability breakdown, signals uncertainty, and avoids guarantee claims.",
            evaluate=evaluate_prediction_framing,
        )
    ],
)
