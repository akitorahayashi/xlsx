from __future__ import annotations

import json

import pytest


@pytest.mark.parametrize("bad", ["abc", "1.2.3", "", "ten", "3,000"])
def test_non_numeric_argument_exits_two_with_action(run_summarize, bad):
    result = run_summarize("10", bad)
    assert result.returncode == 2
    payload = json.loads(result.stderr)
    assert "error" in payload
    assert payload["action"]
