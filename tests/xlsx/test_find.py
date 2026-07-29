from __future__ import annotations

import json


def test_find_substring_default(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "Widget")
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["backend"] == "calamine"
    assert doc["matchCount"] == 1
    assert doc["matches"][0] == {"sheet": "Ledger", "cell": "B2", "value": "Widget"}


def test_find_is_case_insensitive_by_default(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "widget")
    doc = json.loads(result.stdout)
    assert doc["matchCount"] == 1


def test_find_case_sensitive_misses(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "widget", "--case-sensitive")
    assert result.returncode == 1
    doc = json.loads(result.stdout)
    assert doc["matchCount"] == 0


def test_find_regex(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "W.dget", "--regex")
    doc = json.loads(result.stdout)
    assert doc["matchCount"] == 1
    assert doc["matches"][0]["cell"] == "B2"


def test_find_restricted_to_sheet(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "secret", "--sheet", "Ledger")
    assert result.returncode == 1  # 'secret' lives on Hidden, not Ledger
    doc = json.loads(result.stdout)
    assert doc["matchCount"] == 0


def test_find_max_matches_truncates(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "e", "--max-matches", "1")
    doc = json.loads(result.stdout)
    assert doc["matchCount"] == 1
    assert doc["truncated"] is True


def test_find_formulas_searches_sources(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "SUM", "--formulas")
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["backend"] == "openpyxl"
    assert doc["matchCount"] == 1
    assert doc["matches"][0] == {"sheet": "Ledger", "cell": "C4", "value": "=SUM(C2:C3)"}


def test_find_no_match_exits_one(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "ZZZNOMATCH")
    assert result.returncode == 1
    doc = json.loads(result.stdout)
    assert doc["matchCount"] == 0
    assert doc["truncated"] is False


def test_find_traverses_empty_sheet_without_panic(run_script, probe_cli, workbook):
    result = run_script(probe_cli, "find", workbook, "ZZZNOMATCH")
    assert "PanicException" not in result.stderr
