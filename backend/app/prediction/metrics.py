from __future__ import annotations

import math
from collections.abc import Iterable


Outcome = str
ProbabilityRow = dict[str, float]


def brier_score(rows: Iterable[tuple[ProbabilityRow, Outcome]]) -> float:
    total = 0.0
    count = 0
    for probabilities, actual in rows:
        count += 1
        for outcome in ("A", "D", "B"):
            expected = 1.0 if actual == outcome else 0.0
            total += (probabilities[outcome] - expected) ** 2
    return total / count if count else 0.0


def log_loss(rows: Iterable[tuple[ProbabilityRow, Outcome]]) -> float:
    total = 0.0
    count = 0
    epsilon = 1e-12
    for probabilities, actual in rows:
        count += 1
        total -= math.log(max(epsilon, min(1.0 - epsilon, probabilities[actual])))
    return total / count if count else 0.0


def accuracy(rows: Iterable[tuple[ProbabilityRow, Outcome]]) -> float:
    correct = 0
    count = 0
    for probabilities, actual in rows:
        count += 1
        predicted = max(probabilities, key=probabilities.get)
        correct += int(predicted == actual)
    return correct / count if count else 0.0


def calibration_error(rows: Iterable[tuple[ProbabilityRow, Outcome]], bins: int = 5) -> float:
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for probabilities, actual in rows:
        predicted = max(probabilities, key=probabilities.get)
        confidence = probabilities[predicted]
        index = min(bins - 1, int(confidence * bins))
        buckets[index].append((confidence, int(predicted == actual)))

    weighted_error = 0.0
    total = 0
    for bucket in buckets:
        if not bucket:
            continue
        bucket_size = len(bucket)
        avg_confidence = sum(item[0] for item in bucket) / bucket_size
        avg_accuracy = sum(item[1] for item in bucket) / bucket_size
        weighted_error += bucket_size * abs(avg_confidence - avg_accuracy)
        total += bucket_size

    return weighted_error / total if total else 0.0
