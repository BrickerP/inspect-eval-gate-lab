"""Toy arithmetic exam: five questions and two lookup-table agents.

The working table repeats each target, so a correct grader scores 1.0.
The broken table changes two answers, so accuracy drops and the gate fails.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from lab.paths import repo_root

TASK_NAME = "toy_arithmetic"
AGENTS = ("working", "broken")
FIXTURE_PATH = repo_root() / "fixtures" / "toy_arithmetic.json"


class FixtureError(ValueError):
    """The toy fixture JSON is missing or does not match the lab schema."""


@dataclass(frozen=True)
class Sample:
    id: str
    question: str
    target: str
    answers: Mapping[str, str]


def load_fixture(path: Path = FIXTURE_PATH) -> tuple[Sample, ...]:
    """Load the exam. Raises ``FixtureError`` when the file is not usable."""

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FixtureError(f"fixture not found: {path}") from exc
    except OSError as exc:
        raise FixtureError(f"could not read fixture {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FixtureError(f"fixture is not JSON: {path}: {exc}") from exc
    return _validate(data)


def _validate(data: object) -> tuple[Sample, ...]:
    if not isinstance(data, dict):
        raise FixtureError("fixture must be a JSON object")
    extra = set(data) - {"task", "samples"}
    missing = {"task", "samples"} - set(data)
    if extra or missing:
        raise FixtureError(
            "fixture keys must be exactly task and samples, "
            f"missing {sorted(missing)}, extra {sorted(extra)}"
        )
    if data["task"] != TASK_NAME:
        raise FixtureError(f"fixture task must be {TASK_NAME!r}")
    rows = data["samples"]
    if not isinstance(rows, list) or not rows:
        raise FixtureError("fixture samples must be a non-empty list")

    samples: list[Sample] = []
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    for index, row in enumerate(rows):
        samples.append(_sample(index, row, seen_ids, seen_questions))
    return tuple(samples)


def _sample(
    index: int,
    row: object,
    seen_ids: set[str],
    seen_questions: set[str],
) -> Sample:
    label = f"samples[{index}]"
    if not isinstance(row, dict):
        raise FixtureError(f"{label} must be an object")
    extra = set(row) - {"id", "question", "target", "answers"}
    missing = {"id", "question", "target", "answers"} - set(row)
    if extra or missing:
        raise FixtureError(
            f"{label} keys must be exactly id, question, target, answers"
        )
    sample_id = _text(row["id"], f"{label}.id")
    question = _text(row["question"], f"{label}.question")
    target = _text(row["target"], f"{label}.target")
    if sample_id in seen_ids:
        raise FixtureError(f"duplicate sample id {sample_id!r}")
    if question in seen_questions:
        raise FixtureError(f"duplicate question {question!r}")
    seen_ids.add(sample_id)
    seen_questions.add(question)
    answers = _answers(row["answers"], sample_id)
    return Sample(id=sample_id, question=question, target=target, answers=answers)


def _answers(value: object, sample_id: str) -> Mapping[str, str]:
    label = f"sample {sample_id!r} answers"
    if not isinstance(value, dict):
        raise FixtureError(f"{label} must be an object")
    if set(value) != set(AGENTS):
        raise FixtureError(f"{label} must be exactly {list(AGENTS)}")
    answers: dict[str, str] = {}
    for agent in AGENTS:
        answer = value[agent]
        if not isinstance(answer, str):
            raise FixtureError(f"{label}.{agent} must be a string")
        answers[agent] = answer
    return MappingProxyType(answers)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FixtureError(f"{label} must be a non-empty string")
    return value


SAMPLES: tuple[Sample, ...] = load_fixture()
_BY_QUESTION = {sample.question: sample for sample in SAMPLES}


def answer_for(agent: str, question: str) -> str:
    """Return one lookup-table answer. Unknown questions score as blank."""

    if agent not in AGENTS:
        known = ", ".join(AGENTS)
        raise ValueError(f"unknown agent {agent!r}; expected one of {known}")
    sample = _BY_QUESTION.get(question)
    if sample is None:
        return ""
    return sample.answers[agent]
