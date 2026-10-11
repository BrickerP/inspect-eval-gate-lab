"""``python -m lab`` exit codes. Scoring succeeds; the gate fails the drop."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lab.paths import repo_root


class CliTests(unittest.TestCase):
    def test_score_working_agent(self) -> None:
        result = _run("score")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("agent: working", result.stdout)
        self.assertIn("accuracy: 1.000000 (5/5)", result.stdout)
        self.assertIn("ok   add-2-2", result.stdout)

    def test_score_json(self) -> None:
        result = _run("score", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema"], "lab.score.v1")
        self.assertEqual(payload["metrics"]["accuracy"], 1.0)
        self.assertEqual(len(payload["samples"]), 5)

    def test_score_broken_agent_still_exits_zero(self) -> None:
        result = _run("score", "--agent", "broken")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("accuracy: 0.600000 (3/5)", result.stdout)
        self.assertIn("miss sub-7-3", result.stdout)
        self.assertIn("miss div-15-3", result.stdout)

    def test_gate_passes_for_the_working_agent(self) -> None:
        result = _run("gate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("pass toy_arithmetic agent=working\n"))
        self.assertIn("accuracy 1.000000 >= baseline 1.000000", result.stdout)

    def test_gate_fails_for_the_broken_agent(self) -> None:
        result = _run("gate", "--agent", "broken")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.startswith("fail toy_arithmetic agent=broken\n"))
        self.assertIn("accuracy 0.600000 < baseline 1.000000", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_gate_json_reports_the_failure(self) -> None:
        result = _run("gate", "--agent", "broken", "--format", "json")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema"], "lab.gate.v1")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["failures"], ["accuracy 0.600000 < baseline 1.000000"])

    def test_missing_command_and_unknown_agent_exit_two(self) -> None:
        bare = _run()
        self.assertEqual(bare.returncode, 2)
        unknown = _run("score", "--agent", "other")
        self.assertEqual(unknown.returncode, 2)

    def test_missing_baseline_exits_two(self) -> None:
        missing = Path(tempfile.gettempdir()) / "lab-missing-baseline.json"
        result = _run("gate", "--baseline", str(missing))
        self.assertEqual(result.returncode, 2)
        self.assertIn("baseline not found", result.stderr)

    def test_help_exits_zero(self) -> None:
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("python -m lab gate --agent broken", result.stdout)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "lab", *args],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )


if __name__ == "__main__":
    unittest.main()
