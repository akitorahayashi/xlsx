"""Shared fixtures for the xlsx skill tests.

Tests assert the process boundary only: exit code, the stdout JSON, the stderr
JSON, and files written. Each skill script runs through `uv run --script` exactly
as the skill invokes it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "plugin/skills/xlsx/scripts/probe.py"
EDIT = ROOT / "plugin/skills/xlsx/assets/edit.py"


@pytest.fixture
def run_script():
    """Run a PEP 723 skill script through uv and return the completed process.

    The timeout is generous enough for an openpyxl path over a generated fixture.
    """

    def _run(script: Path, *args: object) -> subprocess.CompletedProcess[str]:
        # --quiet keeps uv's first-run "Installed ..." progress off the script's
        # stderr, so the stderr JSON contract holds even when the env is cold.
        argv = ["uv", "run", "--quiet", "--script", str(script), *[str(arg) for arg in args]]
        return subprocess.run(argv, capture_output=True, text=True, timeout=180)

    return _run


@pytest.fixture
def probe_cli() -> Path:
    return PROBE


@pytest.fixture
def edit_cli() -> Path:
    return EDIT
