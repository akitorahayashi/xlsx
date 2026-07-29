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
