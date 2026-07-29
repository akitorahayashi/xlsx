from __future__ import annotations

import json
import shutil


def test_unfilled_template_exits_two(run_script, edit_cli, workbook, tmp_path):
    result = run_script(edit_cli, workbook, tmp_path / "out.xlsx")
    assert result.returncode == 2
    payload = json.loads(result.stderr)
    assert payload["action"]


def test_edit_runtime_error_is_json_and_leaves_no_output(run_script, edit_cli, workbook, tmp_path):
    boom = tmp_path / "edit_boom.py"
    boom.write_text(edit_cli.read_text().replace("    raise NotImplementedError", '    raise ValueError("boom")'))
    output = tmp_path / "out.xlsx"

    result = run_script(boom, workbook, output)
    assert result.returncode == 2
    assert result.stdout == ""
    payload = json.loads(result.stderr)
    assert payload["action"]
    assert not output.exists()  # the staged temp file is cleaned up, nothing half-written


def test_filled_edit_round_trip(run_script, edit_cli, probe_cli, workbook, tmp_path):
    filled = tmp_path / "edit_filled.py"
    source = edit_cli.read_text().replace(
        "    raise NotImplementedError",
        "    sheet = workbook['Ledger']\n    sheet['C2'] = 99\n    return [f\"Ledger!C2 = {sheet['C2'].value}\"]",
    )
    filled.write_text(source)

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
