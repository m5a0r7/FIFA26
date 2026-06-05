import tempfile
import unittest
from pathlib import Path

from backend.app.prediction.benchmark import BenchmarkRunner


class BenchmarkRunnerTest(unittest.TestCase):
    def test_benchmark_runs_against_seed_csv(self) -> None:
        summary = BenchmarkRunner().run(Path("data/benchmarks/historical_matches.csv"))

        self.assertEqual(summary.model_version, "v0_rule_based")
        self.assertGreater(summary.matches, 0)
        self.assertGreater(summary.log_loss, 0)
        self.assertGreaterEqual(summary.accuracy, 0)
        self.assertLessEqual(summary.accuracy, 1)

    def test_report_writer_creates_csv(self) -> None:
        runner = BenchmarkRunner()
        summary = runner.run(Path("data/benchmarks/historical_matches.csv"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.csv"
            runner.write_report(summary, output)

            self.assertTrue(output.exists())
            self.assertIn("model_version", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
