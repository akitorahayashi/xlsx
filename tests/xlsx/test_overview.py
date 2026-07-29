from __future__ import annotations

import json


def test_overview_reports_structure(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "overview", workbook)
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)

    sheets = {sheet["name"]: sheet for sheet in doc["sheets"]}
    assert [sheet["name"] for sheet in doc["sheets"]] == ["Ledger", "Empty", "Hidden"]

    ledger = sheets["Ledger"]
    assert ledger["visible"] is True
    assert ledger["empty"] is False
    assert ledger["rows"] == 7
    assert ledger["columns"] == 3
    assert ledger["usedRange"] == "A1:C7"
    assert ledger["mergedRanges"] == ["A7:B7"]
    assert ledger["hasFormulas"] is True

    assert sheets["Empty"]["empty"] is True
    assert sheets["Empty"]["usedRange"] is None
    assert sheets["Empty"]["hasFormulas"] is False

    assert sheets["Hidden"]["visible"] is False
    assert sheets["Hidden"]["empty"] is False


def test_overview_counts_parts(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "overview", workbook)
    doc = json.loads(result.stdout)
    parts = doc["parts"]
    assert parts["charts"] == 1
    assert set(parts) == {"pivotTables", "charts", "images", "comments", "threadedComments"}


def test_overview_traverses_empty_sheet_without_panic(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "overview", workbook)
    assert result.returncode == 0
    assert "PanicException" not in result.stderr


def test_overview_counts_legacy_comment_directory_layout(run_script, probe_cli, feature_workbook):
    # openpyxl stores legacy comments under xl/comments/comment1.xml
    result = run_script(probe_cli, "overview", feature_workbook)
    doc = json.loads(result.stdout)
    assert doc["parts"]["comments"] == 1


def test_overview_data_validation_is_not_a_formula(run_script, probe_cli, feature_workbook):
    result = run_script(probe_cli, "overview", feature_workbook)
    sheets = {sheet["name"]: sheet for sheet in json.loads(result.stdout)["sheets"]}
    # a list validation carries <formula1> but no cell formula
    assert sheets["Validated"]["hasFormulas"] is False
    assert sheets["Commented"]["hasFormulas"] is False


def test_overview_used_range_reflects_starting_cell(run_script, probe_cli, feature_workbook):
    result = run_script(probe_cli, "overview", feature_workbook)
    offset = next(s for s in json.loads(result.stdout)["sheets"] if s["name"] == "Offset")
    assert offset["usedRange"] == "C5:C5"
    assert offset["rows"] == 1
    assert offset["columns"] == 1
