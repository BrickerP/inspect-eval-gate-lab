"""Command line for ``python -m lab score`` and ``python -m lab gate``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab.fixture import AGENTS, TASK_NAME, FixtureError
from lab.gate import (
    DEFAULT_BASELINE,
    GateError,
    dump_result,
    evaluate,
    format_result,
    load_baseline,
)
from lab.score import dump_report, format_report, grade

_EPILOG = """\
examples:
  python -m lab score
  python -m lab gate
  python -m lab gate --agent broken
"""


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "score":
            return _score(args.agent, args.format)
        if args.command == "gate":
            return _gate(args.agent, args.format, args.baseline)
    except (FixtureError, GateError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command {args.command}")
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m lab",
        description=(
            "Score the toy arithmetic lookup table and gate it against "
            "the committed baseline."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    score = sub.add_parser("score", help="print accuracy for one agent")
    gate = sub.add_parser("gate", help="fail with exit 1 on a score regression")
    for command in (score, gate):
        command.add_argument(
            "--agent",
            choices=AGENTS,
            default="working",
            help="lookup-table agent (default: working)",
        )
        command.add_argument(
            "--format",
            choices=("text", "json"),
            default="text",
            help="output format (default: text)",
        )
    gate.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help=f"baseline JSON (default: {DEFAULT_BASELINE})",
    )
    return parser


def _score(agent: str, output_format: str) -> int:
    report = grade(agent)
    rendered = dump_report(report) if output_format == "json" else format_report(report)
    sys.stdout.write(rendered)
    return 0


def _gate(agent: str, output_format: str, baseline_path: Path) -> int:
    report = grade(agent)
    result = evaluate(report, load_baseline(baseline_path))
    rendered = (
        dump_result(agent, result, TASK_NAME)
        if output_format == "json"
        else format_result(agent, result, TASK_NAME)
    )
    sys.stdout.write(rendered)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
