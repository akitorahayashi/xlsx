# xlsx

A GitHub-installable Agent Skills plugin whose single skill inspects, extracts
from, and edits `.xlsx` and `.xlsm` workbooks. The repository root is the
marketplace root for Claude Code and Codex, and the `plugin/` directory is the
plugin root for Claude Code, Antigravity CLI, and Codex.

The skill drives Python CLIs executed through `uv` as PEP 723 single-file
scripts, so a plugin user needs no virtualenv, no `pip install`, and no project
files in the repository they are working in.

## Structure

```text
xlsx/
├── .claude-plugin/
│   └── marketplace.json                 # Claude Code marketplace manifest
├── .agents/
│   └── plugins/
│       └── marketplace.json             # Codex marketplace manifest
├── plugin/
│   ├── skills/
│   │   └── xlsx/
│   │       ├── SKILL.md
│   │       ├── scripts/probe.py         # read-only CLI: overview / rows / find
│   │       └── assets/edit.py           # edit template to copy and fill
│   ├── .claude-plugin/plugin.json       # Claude Code manifest
│   ├── .codex-plugin/plugin.json        # Codex manifest
│   └── plugin.json                      # Antigravity CLI manifest
├── tests/                               # process-boundary tests
├── pyproject.toml                       # development tools only
├── Makefile                             # make test / fix / lint
├── uv.lock
├── .python-version
├── README.md
└── CONTRIBUTING.md
```

The marketplace manifests expose the plugin in this repository by pointing to
`./plugin`. They are installation indexes only; the plugin body is not duplicated
under a `plugins/` directory.

`plugin/skills/` is shared across all three clients. Each manifest carries only
that client's identity; the skill body is never duplicated. Component
directories (`skills/`, and later `hooks/`, `agents/`, `commands/`, `.mcp.json`)
live at the plugin root. Only `plugin.json` belongs inside `.claude-plugin/` and
`.codex-plugin/`.

## What each manifest requires

- Claude Code — skills under `plugin/skills/` are auto-discovered, so
  `.claude-plugin/plugin.json` needs no `skills` field. Metadata like `author`,
  `homepage`, `repository`, `license`, and `keywords` is optional.
- Codex — `.codex-plugin/plugin.json` declares `"skills": "./skills/"` and
  accepts the same optional metadata plus an `interface` block for
  install-surface presentation.
- Antigravity CLI — `plugin.json` is a closed schema: only `name` (required,
  `^[a-zA-Z0-9-_]+$`) and `description` are valid. Skills are discovered from
  `skills/`; do not add other fields.

## The skill

`plugin/skills/xlsx` reads and edits workbooks through two files:

- `scripts/probe.py` — a read-only CLI. `overview` reports the sheet and part
  inventory and formula presence per sheet; `rows` extracts a bounded window from
  one sheet; `find` searches cell values, or formula sources under `--formulas`.
- `assets/edit.py` — a template copied and filled with a single `edit(workbook)`
  function, then run with explicit input and output paths.

The read path selects a backend by what is asked for. Structure comes from the
standard-library `zipfile` plus python-calamine, row and value reads use
python-calamine, and formulas and editing use openpyxl. `SKILL.md` documents the
cost of each path and the value semantics of each backend.

## Runtime and development separation

The skill CLIs run through `uv run --script` as PEP 723 single-file scripts. Each
script declares its own `requires-python` and its dependencies with exact `==`
pins in a header comment:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["python-calamine==0.8.2", "openpyxl==3.1.5"]
# ///
```

uv resolves `requires-python` against its own managed interpreters, independently
of the `python3` a user happens to have on `PATH`, so the plugin does not depend
on the user's interpreter. The floor is Python 3.12.

The pins are exact on purpose. A resolved script environment is never re-resolved
on later runs, so a lower-bound specifier would silently fix a different version
per machine and per first-run date, and version churn would accumulate
permanently in the uv cache. Exact `==` pins fix both the behavior and the cache
growth.

The dependencies in `pyproject.toml` are development tools synced by uv into a
local `.venv`; they are never a runtime requirement. openpyxl and python-calamine
appear there solely so tests can build fixture workbooks. The `plugin/` directory
is the distributed plugin; development assets at the repository root do not enter
the installable artifact.

## Develop

Development uses [uv](https://docs.astral.sh/uv/). `make fix` applies formatting
and autofixes; `make lint` runs ruff and mypy; `make test` runs pytest. Run
`make fix` before `make lint`. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
full workflow and CLI contract.

## Validate

```bash
claude plugin validate .
claude plugin validate ./plugin
agy plugin validate ./plugin
```

## Install

The repository root is the marketplace root for GitHub distribution.

### Claude Code

```bash
claude plugin marketplace add akitorahayashi/xlsx
claude plugin install xlsx@xlsx
```

For local development, Claude Code can load the plugin root for the current
session with `claude --plugin-dir ./plugin`.

### Codex

```bash
codex plugin marketplace add akitorahayashi/xlsx
codex plugin add xlsx@xlsx
```

### Antigravity CLI

The `plugin/` directory holds both `plugin.json` and `skills/`, so Antigravity
can install it directly:

```bash
agy plugin install ./plugin
```
