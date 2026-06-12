from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.data.cache import DEFAULT_MATCH_CACHE_PATH, get_match_cache_status
from backend.app.data.sync_worldcup_2026 import sync_seed_schedule
from backend.app.prediction.benchmark import BenchmarkRunner
from backend.app.tools import FootballTools


def main() -> None:
    parser = argparse.ArgumentParser(description="Relai-friendly operational tools for the FIFA 2026 agent.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Refresh the local match cache.")
    sync_parser.add_argument("--output", default=str(DEFAULT_MATCH_CACHE_PATH))

    freshness_parser = subparsers.add_parser("freshness", help="Report match cache freshness.")
    freshness_parser.add_argument("--max-age-minutes", type=int, default=60)
    freshness_parser.add_argument("--fail-on-stale", action="store_true")

    benchmark_parser = subparsers.add_parser("benchmark", help="Run the prediction benchmark.")
    benchmark_parser.add_argument("--csv", default="data/benchmarks/historical_matches.csv")
    benchmark_parser.add_argument("--output", default="reports/prediction_benchmark_report.csv")

    subparsers.add_parser("smoke", help="Run lightweight agent/tool smoke checks.")

    args = parser.parse_args()
    if args.command == "sync":
        _print({"ok": True, "command": "sync", "result": sync_seed_schedule(Path(args.output))})
        return

    if args.command == "freshness":
        status = get_match_cache_status(max_age_minutes=args.max_age_minutes)
        ok = not status["stale"]
        _print({"ok": ok, "command": "freshness", "result": status})
        if args.fail_on_stale and not ok:
            sys.exit(1)
        return

    if args.command == "benchmark":
        runner = BenchmarkRunner()
        summary = runner.run(Path(args.csv))
        runner.write_report(summary, Path(args.output))
        _print({"ok": True, "command": "benchmark", "result": summary.as_row()})
        return

    if args.command == "smoke":
        result = _run_smoke_checks()
        _print({"ok": result["ok"], "command": "smoke", "result": result})
        if not result["ok"]:
            sys.exit(1)


def _run_smoke_checks() -> dict[str, Any]:
    tools = FootballTools()
    matches = tools.get_match_schedule()
    prediction = tools.predict_match("Brazil", "Morocco")
    failures = []

    if not matches:
        failures.append("match_schedule_empty")

    if any("TBD" in {match.get("team_a"), match.get("team_b")} for match in matches):
        failures.append("match_schedule_contains_tbd")

    probability_sum = prediction["team_a_win"] + prediction["draw"] + prediction["team_b_win"]
    if abs(probability_sum - 1.0) > 0.01:
        failures.append("prediction_probabilities_do_not_sum_to_one")

    return {
        "ok": not failures,
        "failures": failures,
        "match_count": len(matches),
        "sample_prediction": prediction,
        "freshness": tools.get_data_freshness(),
    }


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
