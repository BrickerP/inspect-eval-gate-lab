"""Optional Inspect AI task for the same five arithmetic questions.

CI does not install or import inspect-ai. This module is the local opt-in:
it shows the Inspect task shape (dataset, solver, scorer, ``@task``) and
can be executed once Inspect is installed.

From the repository root:

    uv add inspect-ai
    uv run inspect eval evals/toy_arithmetic.py --model mockllm/model

``mockllm`` ships with Inspect and needs no provider credentials. The solver
writes the working lookup-table answer and does not call the model. Replace
it with ``generate()`` from ``inspect_ai.solver`` and pass a provider model
when you want a real completion; that path needs credentials and is outside
the CI gate.

Inspect is the evaluation framework from the UK AI Security Institute:
https://inspect.aisi.org.uk/
"""

from __future__ import annotations

import sys
from pathlib import Path

# ``inspect eval <file>`` puts this directory on sys.path, not the repo root.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from inspect_ai import Task, task
    from inspect_ai.dataset import Sample
    from inspect_ai.model import ModelOutput
    from inspect_ai.scorer import match
    from inspect_ai.solver import Generate, TaskState, solver
except ImportError as exc:
    raise ImportError(
        "inspect-ai is optional and is not installed. "
        "From the repo root, run: uv add inspect-ai"
    ) from exc

from lab.fixture import SAMPLES, answer_for


@solver
def lookup_working():
    """Write the working agent's lookup answer. Does not call a model."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        del generate  # lookup answers are not model completions
        state.output = ModelOutput.from_content(
            model="lookup-working",
            content=answer_for("working", state.input_text),
        )
        return state

    return solve


@task
def toy_arithmetic() -> Task:
    """Five arithmetic questions, graded by exact string match."""

    return Task(
        dataset=[
            Sample(id=sample.id, input=sample.question, target=sample.target)
            for sample in SAMPLES
        ],
        solver=lookup_working(),
        # ignore_case=False matches the stdlib scorer, which keeps case.
        # Both scorers collapse whitespace. Neither treats 4 and 4.0 as equal.
        scorer=match(location="exact", ignore_case=False),
    )
