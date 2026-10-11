# inspect-eval-gate-lab

Personal lab for an eval regression gate. A stdlib scorer grades a five-question arithmetic fixture, and a gate compares that score with `baseline/toy_arithmetic.json`. When accuracy drops, the gate exits 1.

This is a learning repo, honest about its size: one toy task, no model calls, no production harness. CI runs with no API keys.

## Inspect

[Inspect](https://inspect.aisi.org.uk/) is the open-source evaluation framework from the UK AI Security Institute (AISI). A task is three pieces:

- a **dataset** of samples (input and target)
- a **solver** that produces an answer for each sample
- a **scorer** that grades those answers

`inspect eval` runs one task and writes a log. An [eval set](https://inspect.aisi.org.uk/eval-sets.html) (`inspect eval-set`, or `eval_set()` in Python) runs many tasks, with retries and a log directory, until the suite finishes. The eval set records which tasks completed.

A **regression gate** is the decision after scoring. Take this run's metrics and fail when they fall below a baseline you already accepted. That is the check CI wants before a prompt, agent, or scorer change lands. An eval-set-gate is that pair: the eval set produces the scores, and the gate accepts or rejects them against the baseline.

Inspect's eval set gives you the run and the logs. This repo is the gate, shrunk so it can be tested with the Python standard library.

## What this repo gates

| Piece | Role |
| --- | --- |
| `fixtures/toy_arithmetic.json` | Five questions, the correct targets, and two lookup tables |
| `python -m lab score` | Exact-match accuracy for one agent |
| `baseline/toy_arithmetic.json` | Committed bar: working agent, accuracy 1.0, five samples |
| `python -m lab gate` | Exit 1 when the current score regresses |

The working table repeats every target, so it scores **1.0** and the gate passes. The broken table misses two rows, so accuracy falls to **0.6** and the gate fails:

| id | question | target | broken answer |
| --- | --- | --- | --- |
| `sub-7-3` | What is 7 - 3? | 4 | 3 |
| `div-15-3` | What is 15 / 3? | 5 | 3 |

CI scores and gates the working agent. Unit tests run the broken agent and expect exit 1.

Comparison rule, applied to every metric named in the baseline:

- a current value greater than or equal to the baseline passes (absolute tolerance `1e-9`)
- a lower value fails
- a different sample count (`n`) fails, including when accuracy stays 1.0
- metrics present only on the current run are ignored
- a metric the baseline names and the current run lacks fails

`score` exits 0 whenever it can grade. The gate is what fails the run. Exit 2 means the command could not evaluate (unknown agent, missing baseline, or invalid baseline JSON).

## Run

Python 3.11 or newer, from the repository root:

```bash
python -m unittest discover -s tests -v
python -m lab score
python -m lab gate
```

Negative control (the gate command exits 1):

```bash
python -m lab score --agent broken
python -m lab gate --agent broken
```

`--format json` prints the score report or the gate result as JSON. `python -m lab --help` lists the flags.

The scorer collapses whitespace and keeps case. `4` matches ` 4 `; it does not match `4.0`.

## Update the baseline

Change the fixture or the working agent on purpose, then review the new score and commit an updated `baseline/toy_arithmetic.json` in the same change. `tests/test_gate.py` checks that the committed file still matches the working agent, so a silent drop fails the tests. Lowering the numbers in the baseline is how you deliberately accept a worse score.

The baseline file is strict: the keys are `schema`, `task`, `n`, and `metrics`. A typo there is an error (exit 2), not a pass.

## Optional Inspect task

`evals/toy_arithmetic.py` is the same five questions in Inspect's task shape: `Sample` rows, a solver, `match(location="exact", ignore_case=False)`, registered with `@task`. CI does not install or import `inspect-ai`.

On a machine where you want to try Inspect:

```bash
uv add inspect-ai
uv run inspect eval evals/toy_arithmetic.py --model mockllm/model
```

`mockllm` ships with Inspect and needs no provider key. The solver writes the working lookup-table answer and does not call a model. Swap that solver for `generate()` and pass a provider model when you want a real completion. That path needs credentials and sits outside this CI gate.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the unit tests, `python -m lab score`, and `python -m lab gate` on CPython 3.11 and 3.12. The workflow installs nothing and does not read GitHub Actions secrets.

## Layout

```
fixtures/toy_arithmetic.json   exam and both lookup tables
baseline/toy_arithmetic.json   committed score bar
lab/                           scorer, gate, and CLI
evals/toy_arithmetic.py        optional Inspect task (not used in CI)
tests/                         unittest, no network and no API keys
```

## Limits

The agent is a lookup table. The metric is one accuracy number from exact string match. There is no epoch, no log viewer, and no model provider. The optional Inspect module documents the task shape for a local install; the gate CI runs is the stdlib command.

## License

[MIT](LICENSE).
