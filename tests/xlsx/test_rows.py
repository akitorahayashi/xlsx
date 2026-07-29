from __future__ import annotations

import json

import pytest


def test_rows_without_header_are_arrays(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--range", "A1:C3")
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["fields"] is None
    assert doc["headerRow"] is None
    assert doc["backend"] == "calamine"
    assert doc["rows"][0] == ["Date", "Item", "Qty"]


def test_rows_with_header_are_objects_and_exclude_header(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--header-row", "1")
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["fields"] == ["Date", "Item", "Qty"]
    first = doc["rows"][0]
    assert first["Date"] == "2026-01-05"  # date rendered ISO-8601
    assert first["Item"] == "Widget"
    assert first["Qty"] == 3.0  # calamine reports numbers as floats
    # the header row itself is not part of the data
    assert all(row["Date"] != "Date" for row in doc["rows"])


def test_rows_omits_empty_rows_and_counts_them(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--header-row", "1")
    doc = json.loads(result.stdout)
    # rows 4 (formula with no cached value), 5, 6 are empty and omitted
    assert doc["emptyRowsOmitted"] == 3
    # the Total row keeps its top-left value; the merged tail is null
    total = doc["rows"][-1]
    assert total["Date"] == "Total"
    assert total["Item"] is None


def test_rows_keep_empty_rows_retains_them(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--range", "A4:C6", "--keep-empty-rows")
    assert result.returncode == 0
    doc = json.loads(result.stdout)
    assert doc["emptyRowsOmitted"] == 0
    assert doc["rowCount"] == 3
    assert doc["rows"] == [[None, None, None], [None, None, None], [None, None, None]]


def test_rows_max_rows_sets_truncated(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--header-row", "1", "--max-rows", "1")
    doc = json.loads(result.stdout)
    assert doc["rowCount"] == 1
    assert doc["truncated"] is True


def test_rows_max_rows_without_range_caps_output(run_script, probe_cli, workbook):
    # no --range: the lazy reader must still stop after the cap
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--max-rows", "2")
    assert result.returncode == 0
    doc = json.loads(result.stdout)
    assert doc["rowCount"] == 2
    assert doc["truncated"] is True


def test_rows_reads_sheet_not_starting_at_a1(run_script, probe_cli, feature_workbook):
    result = run_script(probe_cli, "rows", feature_workbook, "Offset", "--range", "C5:C5")
    assert result.returncode == 0
    doc = json.loads(result.stdout)
    assert doc["rows"] == [["only"]]


def test_rows_csv_shape_and_notes(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--header-row", "1", "--format", "csv")
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "Date,Item,Qty"
    assert lines[1] == "2026-01-05,Widget,3.0"
    assert "omitted" in result.stderr


def test_rows_tsv_shape(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--header-row", "1", "--format", "tsv")
    lines = result.stdout.splitlines()
    assert lines[0] == "Date\tItem\tQty"


@pytest.mark.parametrize(("fmt", "delimiter"), [("csv", ","), ("tsv", "\t")])
def test_rows_empty_result_writes_header_only(run_script, probe_cli, workbook, fmt, delimiter):
    # rows 5 and 6 are empty, so the header is the whole output
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--header-row", "1", "--range", "A5:C6", "--format", fmt)
    assert result.returncode == 1
    assert result.stdout.splitlines() == [delimiter.join(["Date", "Item", "Qty"])]


def test_rows_formulas_use_openpyxl_and_report_sources(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--formulas", "--range", "A1:C4")
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["backend"] == "openpyxl"
    # openpyxl keeps integer typing, unlike calamine
    assert doc["rows"][1][2] == 3
    assert doc["rows"][3][2] == "=SUM(C2:C3)"


def test_rows_formulas_with_header_row_names_fields(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Ledger", "--formulas", "--header-row", "1", "--range", "A1:C4")
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["backend"] == "openpyxl"
    assert doc["fields"] == ["Date", "Item", "Qty"]
    assert doc["headerRow"] == 1
    assert doc["rows"][0]["Qty"] == 3  # openpyxl keeps integer typing
    assert doc["rows"][-1]["Qty"] == "=SUM(C2:C3)"


def test_rows_no_data_exits_one(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "rows", workbook, "Empty")
    assert result.returncode == 1
    doc = json.loads(result.stdout)
    assert doc["rowCount"] == 0
