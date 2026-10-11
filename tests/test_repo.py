"""Repo metadata the CI job and the README depend on."""

from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

from lab import __version__
from lab.paths import repo_root


class RepoTests(unittest.TestCase):
    def test_pyproject_matches_the_package_and_ships_no_dependencies(self) -> None:
        text = _read("pyproject.toml")
        data = tomllib.loads(text)
        self.assertEqual(data["project"]["version"], __version__)
        self.assertEqual(data["project"]["dependencies"], [])
        self.assertEqual(data["project"]["requires-python"], ">=3.11")
        self.assertNotIn("inspect-ai", text)

    def test_workflow_runs_tests_score_and_gate_without_secrets(self) -> None:
        text = _read(".github/workflows/ci.yml")
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m lab score", text)
        self.assertIn("python -m lab gate", text)
        self.assertNotIn("secrets.", text)
        self.assertIsNone(
            re.search(r"(?i)\b(pip3?|uv)\s+(install|add|sync)\b", text)
        )

    def test_license_is_mit(self) -> None:
        text = _read("LICENSE")
        self.assertIn("MIT License", text)
        self.assertIn("Copyright (c) 2026 Lu Yupeng", text)

    def test_readme_explains_the_gate_and_the_inspect_opt_in(self) -> None:
        text = _read("README.md")
        for snippet in (
            "python -m lab score",
            "python -m lab gate",
            "baseline/toy_arithmetic.json",
            "uv add inspect-ai",
            "UK AI Security Institute",
            "eval set",
            "regression gate",
        ):
            self.assertIn(snippet, text)

    def test_lab_package_does_not_read_the_environment(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (repo_root() / "lab").rglob("*.py")
        )
        self.assertNotIn("os.environ", source)
        self.assertNotIn("getenv", source)


def _read(relative: str) -> str:
    return (repo_root() / Path(relative)).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
