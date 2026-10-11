"""Regression decisions against the committed baseline and synthetic bars."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lab.gate import (
    BASELINE_SCHEMA,
    DEFAULT_BASELINE,
    TOLERANCE,
    GateError,
    evaluate,
    load_baseline,
)
from lab.paths import repo_root
from lab.score import grade


def _score(accuracy: float, n: int = 5, task: str = "toy_arithmetic") -> dict:
    return {"task": task, "n": n, "metrics": {"accuracy": accuracy}}


def _baseline(accuracy: float = 1.0, n: int = 5, task: str = "toy_arithmetic") -> dict:
    return {
        "schema": BASELINE_SCHEMA,
        "task": task,
        "n": n,
        "metrics": {"accuracy": accuracy},
    }


class GateTests(unittest.TestCase):
    def test_committed_baseline_matches_the_working_agent(self) -> None:
        report = grade("working")
        baseline = load_baseline()
        self.assertEqual(
            DEFAULT_BASELINE,
            repo_root() / "baseline" / "toy_arithmetic.json",
        )
        self.assertTrue(DEFAULT_BASELINE.is_file())
        self.assertEqual(baseline["schema"], BASELINE_SCHEMA)
        self.assertEqual(baseline["task"], report["task"])
        self.assertEqual(baseline["n"], report["n"])
        self.assertEqual(baseline["metrics"], report["metrics"])
        result = evaluate(report, baseline)
        self.assertTrue(result.ok)
        self.assertEqual(result.failures, ())
        self.assertTrue(any(line.startswith("accuracy 1.000000") for line in result.checks))

    def test_broken_agent_regresses(self) -> None:
        result = evaluate(grade("broken"), load_baseline())
        self.assertFalse(result.ok)
        self.assertEqual(
            result.failures,
            ("accuracy 0.600000 < baseline 1.000000",),
        )

    def test_equal_and_higher_scores_pass(self) -> None:
        even = evaluate(_score(1.0), _baseline(1.0))
        higher = evaluate(_score(1.0), _baseline(0.6))
        self.assertTrue(even.ok)
        self.assertTrue(higher.ok)
        self.assertEqual(higher.failures, ())

    def test_sample_count_change_fails_even_at_full_accuracy(self) -> None:
        result = evaluate(_score(1.0, n=4), _baseline(1.0, n=5))
        self.assertFalse(result.ok)
        self.assertIn("sample count 4 != baseline 5", result.failures)

    def test_task_name_change_fails(self) -> None:
        result = evaluate(_score(1.0, task="other"), _baseline())
        self.assertFalse(result.ok)
        self.assertIn("task other != baseline toy_arithmetic", result.failures)

    def test_missing_metric_fails_and_extra_metric_is_ignored(self) -> None:
        missing = evaluate(
            {"task": "toy_arithmetic", "n": 5, "metrics": {"other": 1.0}},
            _baseline(),
        )
        self.assertFalse(missing.ok)
        self.assertIn("missing metric accuracy", missing.failures)
        extra = evaluate(
            {
                "task": "toy_arithmetic",
                "n": 5,
                "metrics": {"accuracy": 1.0, "other": 0.0},
            },
            _baseline(),
        )
        self.assertTrue(extra.ok)

    def test_tolerance_allows_a_json_round_trip_of_one(self) -> None:
        self.assertLess(TOLERANCE, 1e-6)
        current = _score(1.0)
        baseline = _baseline(1.0 + (TOLERANCE / 10))
        self.assertTrue(evaluate(current, baseline).ok)

    def test_invalid_baseline_is_an_error(self) -> None:
        with self.assertRaises(GateError):
            load_baseline(Path(tempfile.gettempdir()) / "missing-baseline.json")
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "baseline.json"
        path.write_text("{", encoding="utf-8")
        with self.assertRaises(GateError):
            load_baseline(path)
        path.write_text(json.dumps({"schema": BASELINE_SCHEMA, "task": "toy_arithmetic"}), encoding="utf-8")
        with self.assertRaises(GateError):
            load_baseline(path)
        skewed = _baseline()
        skewed["metrics"] = {"accuracy": True}
        with self.assertRaises(GateError):
            evaluate(_score(1.0), skewed)
        empty = _baseline()
        empty["metrics"] = {}
        with self.assertRaises(GateError):
            evaluate(_score(1.0), empty)


if __name__ == "__main__":
    unittest.main()
