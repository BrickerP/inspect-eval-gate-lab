"""Compare a score report to the committed baseline.

A regression is a drop in any baseline metric, or a change in sample
count. Equality and improvements pass. Metric values use an absolute
tolerance of 1e-9 so JSON round-trips of fifths stay stable.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from lab.paths import repo_root

BASELINE_SCHEMA = "lab.baseline.v1"
GATE_SCHEMA = "lab.gate.v1"
TOLERANCE = 1e-9
DEFAULT_BASELINE = repo_root() / "baseline" / "toy_arithmetic.json"
_BASELINE_KEYS = {"schema", "task", "n", "metrics"}


class GateError(ValueError):
    """The baseline or the score report cannot be compared."""


@dataclass(frozen=True)
class GateResult:
    ok: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]


def load_baseline(path: Path = DEFAULT_BASELINE) -> dict[str, object]:
    """Read a baseline file. Raises ``GateError`` when it is not usable."""

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise GateError(f"baseline not found: {path}") from exc
    except OSError as exc:
        raise GateError(f"could not read baseline {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GateError(f"baseline is not JSON: {path}: {exc}") from exc
    _validate_baseline(data)
    return data


def evaluate(current: Mapping[str, object], baseline: Mapping[str, object]) -> GateResult:
    """Return the regression decision for one score report."""

    _validate_baseline(baseline)
    task = _text(current.get("task"), "score task")
    count = _count(current.get("n"), "score n")
    metrics = _metrics(current.get("metrics"), "score metrics")
    base_task = _text(baseline.get("task"), "baseline task")
    base_count = _count(baseline.get("n"), "baseline n")
    base_metrics = _metrics(baseline.get("metrics"), "baseline metrics")

    checks: list[str] = []
    failures: list[str] = []
    if task == base_task:
        checks.append(f"task {task}")
    else:
        failures.append(f"task {task} != baseline {base_task}")
    if count == base_count:
        checks.append(f"sample count {count}")
    else:
        failures.append(f"sample count {count} != baseline {base_count}")
    for name, base_value in base_metrics.items():
        if name not in metrics:
            failures.append(f"missing metric {name}")
            continue
        current_value = metrics[name]
        if (base_value - current_value) > TOLERANCE:
            failures.append(f"{name} {current_value:.6f} < baseline {base_value:.6f}")
        else:
            checks.append(f"{name} {current_value:.6f} >= baseline {base_value:.6f}")
    return GateResult(ok=not failures, checks=tuple(checks), failures=tuple(failures))


def format_result(agent: str, result: GateResult, task: str) -> str:
    """Plain-text gate log, ending with a newline."""

    status = "pass" if result.ok else "fail"
    body = result.checks if result.ok else result.failures
    lines = [f"{status} {task} agent={agent}"]
    lines.extend(f"  {line}" for line in body)
    return "\n".join(lines) + "\n"


def dump_result(agent: str, result: GateResult, task: str) -> str:
    """JSON gate result, ending with a newline."""

    payload = {
        "schema": GATE_SCHEMA,
        "ok": result.ok,
        "task": task,
        "agent": agent,
        "checks": list(result.checks),
        "failures": list(result.failures),
    }
    return json.dumps(payload, indent=2) + "\n"


def _validate_baseline(data: object) -> None:
    if not isinstance(data, dict):
        raise GateError("baseline must be a JSON object")
    if set(data) != _BASELINE_KEYS:
        raise GateError(
            "baseline keys must be exactly schema, task, n, and metrics"
        )
    if data.get("schema") != BASELINE_SCHEMA:
        raise GateError(f"baseline schema must be {BASELINE_SCHEMA!r}")
    _text(data.get("task"), "baseline task")
    _count(data.get("n"), "baseline n")
    _metrics(data.get("metrics"), "baseline metrics")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a non-empty string")
    return value


def _count(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GateError(f"{label} must be an integer")
    if value <= 0:
        raise GateError(f"{label} must be positive")
    return value


def _metrics(value: object, label: str) -> dict[str, float]:
    if not isinstance(value, dict) or not value:
        raise GateError(f"{label} must be a non-empty object")
    parsed: dict[str, float] = {}
    for name, raw in value.items():
        if not isinstance(name, str) or not name.strip():
            raise GateError(f"{label} names must be non-empty strings")
        parsed[name] = _number(raw, f"{label}.{name}")
    return parsed


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GateError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise GateError(f"{label} must be finite")
    return number
