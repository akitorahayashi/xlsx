from __future__ import annotations

import json
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


def test_unsupported_extension_exits_two(run_script, edit_cli, tmp_path):
    filled = _fill(edit_cli, tmp_path, NO_CHANGES)
    other = tmp_path / "data.txt"
    other.write_text("not a workbook")
    result = run_script(filled, other, tmp_path / "out.txt")
    _assert_exit_two(result)


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
