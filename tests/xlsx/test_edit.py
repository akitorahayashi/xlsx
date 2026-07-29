from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path

import pytest

SENTINEL = "    raise NotImplementedError"
NO_CHANGES = "    return []"
VBA_PART = "xl/vbaProject.bin"


def _fill(edit_cli: Path, tmp_path: Path, body: str, name: str = "edit_filled.py") -> Path:
    """Copy the template and replace its unfilled edit() body, as the skill does."""
    filled = tmp_path / name
    filled.write_text(edit_cli.read_text().replace(SENTINEL, body))
    return filled


def _assert_exit_two(result):
    assert result.returncode == 2
    assert result.stdout == ""
    payload = json.loads(result.stderr)
    assert payload["error"]
    assert payload["action"]
    return payload


def test_unfilled_template_exits_two(run_script, edit_cli, workbook, tmp_path):
    result = run_script(edit_cli, workbook, tmp_path / "out.xlsx")
    _assert_exit_two(result)


@pytest.mark.parametrize("count", [0, 1, 3])
def test_wrong_argument_count_exits_two(run_script, edit_cli, workbook, tmp_path, count):
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    paths = [workbook, tmp_path / "out.xlsx", tmp_path / "extra.xlsx"][:count]
    result = run_script(filled, *paths)
    _assert_exit_two(result)


def test_missing_input_exits_two(run_script, edit_cli, tmp_path):
    # the template is filled, so only the missing input can produce exit 2
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    output = tmp_path / "out.xlsx"
    result = run_script(filled, tmp_path / "nope.xlsx", output)
    _assert_exit_two(result)
    assert not output.exists()


@pytest.mark.parametrize("suffix", [".txt", ".xls"])
def test_unsupported_extension_exits_two(run_script, edit_cli, workbook, tmp_path, suffix):
    # .xls carries a real workbook body, so rejection is by suffix and not by
    # content: the suffix set is the whole contract, and probe.py shares it
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    other = tmp_path / f"data{suffix}"
    shutil.copy(workbook, other)
    result = run_script(filled, other, other)
    _assert_exit_two(result)


@pytest.mark.parametrize("out_name", ["out.xlsm", "out.xls", "out"])
def test_output_extension_must_match_the_input(run_script, edit_cli, workbook, tmp_path, out_name):
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    output = tmp_path / out_name
    result = run_script(filled, workbook, output)
    _assert_exit_two(result)
    assert not output.exists()


def test_macro_input_cannot_be_written_to_a_plain_extension(run_script, edit_cli, macro_workbook, tmp_path):
    """Otherwise the VBA part travels into a file named .xlsx (keep_vba is decided
    from the input), so the package would contradict its own extension."""
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    output = tmp_path / "converted.xlsx"
    result = run_script(filled, macro_workbook, output)
    _assert_exit_two(result)
    assert not output.exists()


def test_edit_runtime_error_is_json_and_leaves_no_output(run_script, edit_cli, workbook, tmp_path):
    boom = _fill(edit_cli, tmp_path, '    raise ValueError("boom")', name="edit_boom.py")
    output = tmp_path / "out.xlsx"

    result = run_script(boom, workbook, output)
    _assert_exit_two(result)
    assert not output.exists()  # the staged temp file is cleaned up, nothing half-written


def test_filled_edit_round_trip(run_script, edit_cli, probe_cli, workbook, tmp_path):
    filled = _fill(
        edit_cli,
        tmp_path,
        "    sheet = workbook['Ledger']\n    sheet['C2'] = 99\n    return [f\"Ledger!C2 = {sheet['C2'].value}\"]",
    )

    target = tmp_path / "target.xlsx"
    shutil.copy(workbook, target)

    edited = run_script(filled, target, target)
    assert edited.returncode == 0, edited.stderr
    report = json.loads(edited.stdout)
    assert report["changes"] == ["Ledger!C2 = 99"]

    # verify through probe.py, not the script's own summary
    check = run_script(probe_cli, "rows", target, "Ledger", "--formulas", "--range", "A1:C7")
    assert check.returncode == 0, check.stderr
    rows = json.loads(check.stdout)["rows"]
    assert rows[1][2] == 99  # the change landed
    assert rows[3][2] == "=SUM(C2:C3)"  # existing formula survived

    overview = run_script(probe_cli, "overview", target)
    ledger = next(s for s in json.loads(overview.stdout)["sheets"] if s["name"] == "Ledger")
    assert ledger["mergedRanges"] == ["A7:B7"]  # merged range survived


def test_in_place_edit_preserves_permission_mode(run_script, edit_cli, workbook, tmp_path):
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    target = tmp_path / "target.xlsx"
    shutil.copy(workbook, target)
    target.chmod(0o664)

    result = run_script(filled, target, target)
    assert result.returncode == 0, result.stderr
    assert target.stat().st_mode & 0o777 == 0o664


def test_fresh_output_mode_follows_the_umask(run_script, edit_cli, workbook, tmp_path):
    # the mode is asserted against an explicit umask: 0o666 & ~0o022 == 0o644
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    output = tmp_path / "fresh.xlsx"

    previous = os.umask(0o022)
    try:
        result = run_script(filled, workbook, output)
    finally:
        os.umask(previous)

    assert result.returncode == 0, result.stderr
    assert output.stat().st_mode & 0o777 == 0o644


def test_macro_edit_preserves_vba_project(run_script, edit_cli, macro_workbook, tmp_path):
    """An in-place .xlsm edit leaves xl/vbaProject.bin byte-identical (keep_vba)."""
    filled = _fill(edit_cli, tmp_path, "    workbook['Macro']['A1'] = 2\n    return ['Macro!A1 = 2']")

    with zipfile.ZipFile(macro_workbook) as archive:
        before = archive.read(VBA_PART)

    edited = run_script(filled, macro_workbook, macro_workbook)
    assert edited.returncode == 0, edited.stderr

    with zipfile.ZipFile(macro_workbook) as archive:
        assert VBA_PART in archive.namelist()
        assert archive.read(VBA_PART) == before
