"""Exact-match accuracy for the toy arithmetic fixture.

Whitespace is collapsed before comparison. Case is preserved. ``4`` and
``4.0`` are different answers: this scorer does not interpret numbers.
"""

from __future__ import annotations

import json
from typing import Mapping

from lab.fixture import SAMPLES, TASK_NAME, answer_for

SCHEMA = "lab.score.v1"
_ACCURACY_DIGITS = 6


def canonical(text: str) -> str:
    """Collapse whitespace the way the scorer compares answers."""

    return " ".join(text.split())


def grade(agent: str) -> dict[str, object]:
    """Score one built-in agent against the committed fixture."""

    answers = {sample.question: answer_for(agent, sample.question) for sample in SAMPLES}
    return grade_answers(agent, answers)


def grade_answers(agent: str, answers: Mapping[str, object]) -> dict[str, object]:
    """Score an explicit question-to-answer table.

    ``answers`` overrides the fixture table so tests can probe matching
    rules without editing ``fixtures/toy_arithmetic.json``.
    """

    if not SAMPLES:
        raise ValueError("fixture has no samples")
    rows: list[dict[str, object]] = []
    correct = 0
    for sample in SAMPLES:
        output = answers.get(sample.question, "")
        if not isinstance(output, str):
            raise TypeError(
                f"answer for {sample.question!r} must be str, "
                f"got {type(output).__name__}"
            )
        expected = canonical(sample.target)
        got = canonical(output)
        matched = bool(expected) and got == expected
        if matched:
            correct += 1
        rows.append(
            {
                "id": sample.id,
                "question": sample.question,
                "target": sample.target,
                "output": output,
                "correct": matched,
            }
        )
    total = len(SAMPLES)
    return {
        "schema": SCHEMA,
        "task": TASK_NAME,
        "agent": agent,
        "n": total,
        "correct": correct,
        "metrics": {"accuracy": round(correct / total, _ACCURACY_DIGITS)},
        "samples": rows,
    }


def format_report(report: Mapping[str, object]) -> str:
    """Plain-text score log, ending with a newline."""

    metrics = report["metrics"]
    if not isinstance(metrics, dict):
        raise TypeError("report metrics must be an object")
    accuracy = metrics["accuracy"]
    samples = report["samples"]
    if not isinstance(samples, list):
        raise TypeError("report samples must be a list")
    lines = [
        f"task: {report['task']}",
        f"agent: {report['agent']}",
        f"accuracy: {accuracy:.6f} ({report['correct']}/{report['n']})",
    ]
    for row in samples:
        if not isinstance(row, dict):
            raise TypeError("sample row must be an object")
        status = "ok" if row["correct"] else "miss"
        lines.append(
            f"{status:<4} {row['id']}  {row['question']}  "
            f"target={row['target']}  output={row['output']}"
        )
    return "\n".join(lines) + "\n"


def dump_report(report: Mapping[str, object]) -> str:
    """JSON score report, ending with a newline."""

    return json.dumps(report, indent=2) + "\n"
