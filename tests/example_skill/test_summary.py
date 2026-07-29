from __future__ import annotations

import json


def test_summarizes_numbers_and_exits_zero(run_summarize):
    result = run_summarize(10, 6, 2)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["count"] == 3
    assert payload["sum"] == 18
    assert payload["min"] == 2
    assert payload["max"] == 10
    assert payload["mean"] == 6


def test_accepts_decimals_and_negatives(run_summarize):
    result = run_summarize("-1.5", "2.5")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["count"] == 2
    assert payload["sum"] == 1.0
    assert payload["min"] == -1.5
    assert payload["max"] == 2.5
    assert payload["mean"] == 0.5


def test_no_numbers_exits_one_with_hint(run_summarize):
    result = run_summarize()
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["count"] == 0
    assert "hint" in payload
