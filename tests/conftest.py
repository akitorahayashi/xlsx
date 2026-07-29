"""Shared fixtures for the example skill CLI tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SUMMARIZE_CLI = ROOT / "plugin/skills/example-skill/scripts/summarize.py"


@pytest.fixture
def run_summarize():
    """Run the example CLI as a subprocess with the given values as arguments."""

    def _run(*values):
        argv = [sys.executable, str(SUMMARIZE_CLI), *[str(value) for value in values]]
        return subprocess.run(argv, capture_output=True, text=True, timeout=30)

    return _run
