"""Consistency of the plugin identity duplicated across the manifests.

Each client reads its own manifest, so the name, description, and version are
written out by hand several times. README documents that they share one identity
and nothing enforced it, so a partial edit drifted silently.

This is the one test that is not a skill script's process boundary. It asserts
only that the carriers agree with each other, never what the values should be:
the drift is the defect, and the identity itself is the maintainer's to choose.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

PLUGIN = ROOT / "plugin/plugin.json"
CLAUDE_PLUGIN = ROOT / "plugin/.claude-plugin/plugin.json"
CODEX_PLUGIN = ROOT / "plugin/.codex-plugin/plugin.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin/marketplace.json"
AGENTS_MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _plugin_entry(marketplace: Path) -> dict[str, Any]:
    entries = _load(marketplace)["plugins"]
    assert len(entries) == 1, f"{marketplace.name} lists {len(entries)} plugins"
    return entries[0]


def test_every_manifest_names_the_same_plugin():
    names = {
        "plugin.json": _load(PLUGIN)["name"],
        "claude plugin": _load(CLAUDE_PLUGIN)["name"],
        "codex plugin": _load(CODEX_PLUGIN)["name"],
        "claude marketplace": _load(CLAUDE_MARKETPLACE)["name"],
        "claude marketplace entry": _plugin_entry(CLAUDE_MARKETPLACE)["name"],
        "agents marketplace": _load(AGENTS_MARKETPLACE)["name"],
        "agents marketplace entry": _plugin_entry(AGENTS_MARKETPLACE)["name"],
    }
    assert len(set(names.values())) == 1, names


def test_the_plugin_description_is_identical_wherever_it_appears():
    # the marketplace's own top-level description describes the marketplace, not
    # the plugin, and is deliberately different text
    descriptions = {
        "plugin.json": _load(PLUGIN)["description"],
        "claude plugin": _load(CLAUDE_PLUGIN)["description"],
        "codex plugin": _load(CODEX_PLUGIN)["description"],
        "claude marketplace entry": _plugin_entry(CLAUDE_MARKETPLACE)["description"],
    }
    assert len(set(descriptions.values())) == 1, descriptions


def test_the_client_manifests_agree_on_the_version():
    # the marketplace manifests carry no version; only these two do
    versions = {
        "claude plugin": _load(CLAUDE_PLUGIN)["version"],
        "codex plugin": _load(CODEX_PLUGIN)["version"],
    }
    assert len(set(versions.values())) == 1, versions
