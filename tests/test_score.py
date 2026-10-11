"""Accuracy for the working agent, the broken agent, and match rules."""

from __future__ import annotations

import unittest

from lab.fixture import SAMPLES
from lab.score import SCHEMA, canonical, grade, grade_answers


class ScoreTests(unittest.TestCase):
    def test_working_agent_scores_one(self) -> None:
        report = grade("working")
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["task"], "toy_arithmetic")
        self.assertEqual(report["agent"], "working")
        self.assertEqual(report["n"], 5)
        self.assertEqual(report["correct"], 5)
        self.assertEqual(report["metrics"], {"accuracy": 1.0})
        samples = report["samples"]
        self.assertIsInstance(samples, list)
        assert isinstance(samples, list)
        self.assertTrue(all(row["correct"] for row in samples))

    def test_broken_agent_drops_to_three_of_five(self) -> None:
        report = grade("broken")
        self.assertEqual(report["correct"], 3)
        self.assertEqual(report["n"], 5)
        self.assertEqual(report["metrics"], {"accuracy": 0.6})
        samples = report["samples"]
        assert isinstance(samples, list)
        missed = [row["id"] for row in samples if not row["correct"]]
        self.assertEqual(missed, ["sub-7-3", "div-15-3"])

    def test_whitespace_matches_and_a_different_token_does_not(self) -> None:
        self.assertEqual(canonical("  4\n"), "4")
        self.assertEqual(canonical("Ab"), "Ab")
        self.assertNotEqual(canonical("Ab"), "ab")
        padded = grade_answers("working", _answers(lambda target: f"  {target} \n"))
        self.assertEqual(padded["metrics"], {"accuracy": 1.0})
        drifted = grade_answers(
            "working",
            _answers(lambda target: "4.0" if target == "4" else target),
        )
        self.assertEqual(drifted["correct"], 3)
        metrics = drifted["metrics"]
        self.assertIsInstance(metrics, dict)
        assert isinstance(metrics, dict)
        self.assertLess(metrics["accuracy"], 1.0)

    def test_blank_and_non_numeric_text_are_wrong(self) -> None:
        blank = grade_answers("working", {})
        self.assertEqual(blank["correct"], 0)
        self.assertEqual(blank["metrics"], {"accuracy": 0.0})
        word = grade_answers("working", {"What is 2 + 2?": "Four"})
        first = word["samples"][0]
        self.assertIsInstance(first, dict)
        assert isinstance(first, dict)
        self.assertFalse(first["correct"])
        self.assertEqual(first["output"], "Four")

    def test_non_string_answer_is_a_type_error(self) -> None:
        with self.assertRaises(TypeError):
            grade_answers("working", {"What is 2 + 2?": 4})


def _answers(transform):
    return {sample.question: transform(sample.target) for sample in SAMPLES}


if __name__ == "__main__":
    unittest.main()
