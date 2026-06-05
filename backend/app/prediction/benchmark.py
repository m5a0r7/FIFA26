from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from backend.app.prediction.engine import PredictionEngine, TeamSnapshot
from backend.app.prediction.metrics import accuracy, brier_score, calibration_error, log_loss


@dataclass(frozen=True)
class BenchmarkSummary:
    model_version: str
    matches: int
    brier_score: float
    log_loss: float
    accuracy: float
    calibration_error: float

    def as_row(self) -> dict[str, object]:
        return {
            "model_version": self.model_version,
            "matches": self.matches,
            "brier_score": round(self.brier_score, 4),
            "log_loss": round(self.log_loss, 4),
            "accuracy": round(self.accuracy, 4),
            "calibration_error": round(self.calibration_error, 4),
        }


class BenchmarkRunner:
    def __init__(self, engine: PredictionEngine | None = None) -> None:
        self.engine = engine or PredictionEngine()

    def run(self, csv_path: Path) -> BenchmarkSummary:
        evaluated_rows = []
        with csv_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                team_a = self._snapshot(row, "a")
                team_b = self._snapshot(row, "b")
                prediction = self.engine.predict(team_a, team_b)
                probabilities = {
                    "A": prediction.team_a_win,
                    "D": prediction.draw,
                    "B": prediction.team_b_win,
                }
                evaluated_rows.append((probabilities, row["actual_result"].strip().upper()))

        return BenchmarkSummary(
            model_version=self.engine.model_version,
            matches=len(evaluated_rows),
            brier_score=brier_score(evaluated_rows),
            log_loss=log_loss(evaluated_rows),
            accuracy=accuracy(evaluated_rows),
            calibration_error=calibration_error(evaluated_rows),
        )

    def write_report(self, summary: BenchmarkSummary, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(summary.as_row().keys())
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(summary.as_row())

    def _snapshot(self, row: dict[str, str], side: str) -> TeamSnapshot:
        suffix = f"_{side}"
        return TeamSnapshot(
            name=row[f"team{suffix}"],
            elo=float(row[f"elo{suffix}"]),
            fifa_rank=int(row[f"fifa_rank{suffix}"]),
            squad_quality=float(row[f"squad_quality{suffix}"]),
            recent_form_points=float(row[f"last5_points{suffix}"]),
            goals_for_last5=float(row[f"goals_for_last5{suffix}"]),
            goals_against_last5=float(row[f"goals_against_last5{suffix}"]),
            injuries=int(row[f"injuries{suffix}"]),
            suspensions=int(row[f"suspensions{suffix}"]),
            tournament_experience=float(row[f"tournament_experience{suffix}"]),
            host=row[f"host{suffix}"].strip().lower() == "true",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the prediction CSV benchmark.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="data/benchmarks/historical_matches.csv",
        help="Path to the historical match benchmark CSV.",
    )
    parser.add_argument(
        "output_path",
        nargs="?",
        default="reports/prediction_benchmark_report.csv",
        help="Path where the benchmark report CSV should be written.",
    )
    args = parser.parse_args()

    runner = BenchmarkRunner()
    summary = runner.run(Path(args.csv_path))
    runner.write_report(summary, Path(args.output_path))
    print(summary.as_row())


if __name__ == "__main__":
    main()
