"""The optional Inspect module stays documentation until a local install."""

from __future__ import annotations

import ast
import unittest

from lab.paths import repo_root


class OptionalEvalTests(unittest.TestCase):
    def test_task_file_parses_and_documents_the_opt_in(self) -> None:
        path = repo_root() / "evals" / "toy_arithmetic.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIn("uv add inspect-ai", source)
        self.assertIn("mockllm/model", source)
        imported = " ".join(_imported(tree))
        self.assertIn("inspect_ai", imported)
        self.assertIn("lab.fixture", imported)
        decorators = _decorator_names(tree)
        self.assertIn("task", decorators)
        self.assertIn("solver", decorators)


def _imported(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def _decorator_names(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            name = decorator
            if isinstance(name, ast.Call):
                name = name.func
            if isinstance(name, ast.Name):
                found.add(name.id)
    return found


if __name__ == "__main__":
    unittest.main()
