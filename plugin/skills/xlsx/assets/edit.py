# /// script
# requires-python = ">=3.12"
# dependencies = ["openpyxl==3.1.5"]
# ///
"""
Edit template for one .xlsx or .xlsm workbook.

This is a template to copy and fill in, not a CLI to call directly. It owns
everything identical between edits (load mode, atomic save, reporting) and leaves
exactly one function to write: edit().

Usage:

    uv run --script edit.py <input.xlsx> <output.xlsx>

Both paths are required. An in-place edit passes the same path twice; the atomic
save through a sibling temporary file makes that safe.

Exit codes:
- 0: the edit ran and the output was written.
- 2: a usage or runtime error (edit() not filled in, input missing, bad
     extension). stderr carries one JSON document with "error" and "action".
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

SUPPORTED_SUFFIXES = (".xlsx", ".xlsm", ".xltx", ".xltm")
VBA_SUFFIXES = (".xlsm", ".xltm")


class EditError(Exception):
    """A usage or runtime error carrying an action for the caller to fix."""

    def __init__(self, message: str, action: str) -> None:
        super().__init__(message)
        self.action = action


def edit(workbook: Any) -> list[str]:
    """Apply the edit to ``workbook`` in place and return one line per change.

    Fill this in. Mutate the workbook and return a human-readable summary line for
    each change, for example::

        sheet = workbook["Sheet1"]
        sheet["B2"] = 42
        return [f"Sheet1!B2 = {sheet['B2'].value}"]

    Read cells with ``workbook[sheet_name][cell]``; formulas are preserved because
    the workbook is loaded with data_only=False.
    """
    raise NotImplementedError


def save_atomically(workbook: Any, output: Path) -> None:
    """Save to a sibling temporary file, then os.replace onto the destination.

    Staging in the destination directory keeps the replace atomic on the same
    filesystem, so an in-place edit (input path == output path) never leaves a
    half-written workbook if the save raises.
    """
    handle, staged = tempfile.mkstemp(dir=str(output.parent), suffix=output.suffix)
    os.close(handle)
    staged_path = Path(staged)
    try:
        workbook.save(staged)
        os.replace(staged, output)
    except BaseException:
        staged_path.unlink(missing_ok=True)
        raise


def run(input_arg: str, output_arg: str) -> int:
    source = Path(input_arg)
    output = Path(output_arg)

    if not source.exists():
        raise EditError(f"Input not found: {input_arg}", "Pass a path to an existing .xlsx or .xlsm workbook.")
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise EditError(
            f"Unsupported extension: {source.suffix or '(none)'}",
            "This template edits .xlsx and .xlsm (and .xltx/.xltm) workbooks only.",
        )

    # data_only=True would replace every formula with its last cached value on
    # save, permanently discarding the formulas. The edit path never sets it.
    workbook = load_workbook(
        str(source),
        data_only=False,
        keep_vba=source.suffix.lower() in VBA_SUFFIXES,
    )
    try:
        try:
            changes = edit(workbook)
        except NotImplementedError:
            raise EditError(
                "The edit() function is not filled in.",
                "Open this copy of edit.py and implement edit(workbook) before running it.",
            )
        if not isinstance(changes, list) or not all(isinstance(line, str) for line in changes):
            raise EditError(
                "edit() must return a list of summary strings.",
                "Return one string per change from edit(workbook), e.g. ['Sheet1!B2 = 42'].",
            )
        save_atomically(workbook, output)
    finally:
        workbook.close()

    print(json.dumps({"output": str(output), "changes": changes}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(
            json.dumps(
                {
                    "error": "Expected exactly two paths.",
                    "action": "Run: uv run --script edit.py <input.xlsx> <output.xlsx> (same path twice for in place).",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    try:
        return run(args[0], args[1])
    except EditError as error:
        print(json.dumps({"error": str(error), "action": error.action}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001 - surface runtime failures as exit 2 JSON, not a traceback
        print(
            json.dumps(
                {
                    "error": f"{type(error).__name__}: {error}",
                    "action": "The edit() function or the save failed; fix the edit logic or the output path and retry.",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
