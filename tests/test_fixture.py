"""The committed exam is five questions and two lookup tables."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lab.fixture import (
    AGENTS,
    FIXTURE_PATH,
    SAMPLES,
    TASK_NAME,
    FixtureError,
    answer_for,
    load_fixture,
)


class FixtureTests(unittest.TestCase):
    def test_committed_exam_has_five_questions(self) -> None:
        self.assertEqual(len(SAMPLES), 5)
        self.assertEqual(TASK_NAME, "toy_arithmetic")
        self.assertEqual([sample.id for sample in SAMPLES], [
            "add-2-2",
            "sub-7-3",
            "mul-6-3",
            "div-15-3",
            "add-10-5",
        ])
        self.assertEqual(len({sample.id for sample in SAMPLES}), 5)
        self.assertEqual(len({sample.question for sample in SAMPLES}), 5)

    def test_working_table_matches_every_target(self) -> None:
        for sample in SAMPLES:
            self.assertEqual(sample.answers["working"], sample.target)
            self.assertEqual(answer_for("working", sample.question), sample.target)

    def test_broken_table_misses_two_rows(self) -> None:
        misses = [
            sample.id
            for sample in SAMPLES
            if sample.answers["broken"] != sample.target
        ]
        self.assertEqual(misses, ["sub-7-3", "div-15-3"])
        by_id = {sample.id: sample for sample in SAMPLES}
        self.assertEqual(by_id["sub-7-3"].answers["broken"], "3")
        self.assertEqual(by_id["div-15-3"].answers["broken"], "3")

    def test_unknown_question_is_blank(self) -> None:
        self.assertEqual(answer_for("working", "What is 1 + 1?"), "")

    def test_unknown_agent_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            answer_for("missing", SAMPLES[0].question)

    def test_agents_are_the_two_tables(self) -> None:
        self.assertEqual(AGENTS, ("working", "broken"))

    def test_loader_rejects_a_short_exam(self) -> None:
        path = self._write({"task": TASK_NAME, "samples": []})
        with self.assertRaises(FixtureError):
            load_fixture(path)

    def test_loader_rejects_a_missing_agent(self) -> None:
        row = {
            "id": "add-2-2",
            "question": "What is 2 + 2?",
            "target": "4",
            "answers": {"working": "4"},
        }
        path = self._write({"task": TASK_NAME, "samples": [row]})
        with self.assertRaises(FixtureError):
            load_fixture(path)

    def test_loader_rejects_duplicate_ids(self) -> None:
        row = {
            "id": "add-2-2",
            "question": "What is 2 + 2?",
            "target": "4",
            "answers": {"working": "4", "broken": "4"},
        }
        other = {
            "id": "add-2-2",
            "question": "What is 3 + 3?",
            "target": "6",
            "answers": {"working": "6", "broken": "6"},
        }
        path = self._write({"task": TASK_NAME, "samples": [row, other]})
        with self.assertRaises(FixtureError):
            load_fixture(path)

    def test_committed_file_is_the_one_the_package_loads(self) -> None:
        self.assertEqual(FIXTURE_PATH.name, "toy_arithmetic.json")
        self.assertEqual(load_fixture(FIXTURE_PATH), SAMPLES)

    def _write(self, payload: object) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "toy_arithmetic.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()
