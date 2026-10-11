"""Paths that belong to the checkout, not to the process working directory."""

from pathlib import Path


def repo_root() -> Path:
    """Directory that contains the ``lab`` package, fixture, and baseline."""

    return Path(__file__).resolve().parents[1]
