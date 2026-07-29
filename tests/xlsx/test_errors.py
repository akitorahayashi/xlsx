from __future__ import annotations

import json


def _assert_exit_two(result):
    assert result.returncode == 2
    assert result.stdout == ""
    payload = json.loads(result.stderr)
    assert payload["error"]
    assert payload["action"]
    return payload


def test_missing_file(run_script, probe_cli, tmp_path):
    result = run_script(probe_cli, "overview", tmp_path / "nope.xlsx")
    _assert_exit_two(result)


def test_unsupported_extension(run_script, probe_cli, tmp_path):
    other = tmp_path / "data.txt"
    other.write_text("not a workbook")
    result = run_script(probe_cli, "overview", other)
    _assert_exit_two(result)


def test_unknown_sheet_lists_available_names(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Nope")
    payload = _assert_exit_two(result)
    assert "Ledger" in payload["action"]


def test_invalid_range(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--range", "ZZ")
    _assert_exit_two(result)


def test_invalid_regex(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "[unclosed", "--regex")
    _assert_exit_two(result)


def test_header_row_outside_sheet(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--header-row", "999")
    _assert_exit_two(result)


def test_empty_header_cell(run_script, probe_cli, header_workbook):
    result = run_script(probe_cli, "rows", header_workbook, "EmptyHdr", "--header-row", "1")
    _assert_exit_two(result)


def test_duplicate_header_name(run_script, probe_cli, header_workbook):
    result = run_script(probe_cli, "rows", header_workbook, "DupHdr", "--header-row", "1")
    _assert_exit_two(result)


def test_missing_positional_argument_is_json(run_script, probe_cli):
    result = run_script(probe_cli, "rows")  # sheet argument missing
    _assert_exit_two(result)


def test_malformed_integer_argument_is_json(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--max-rows", "notanint")
    _assert_exit_two(result)


def test_invalid_choice_argument_is_json(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--format", "yaml")
    _assert_exit_two(result)
