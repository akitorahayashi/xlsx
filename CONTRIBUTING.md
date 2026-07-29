# Contributing

This repository is a template for a multi-client Agent Skills plugin whose skills
are backed by Python scripts. User-facing documentation is in
[README.md](README.md); this guide covers the development workflow.

## Runtime constraint

The skill CLIs run on the plugin user's own `python3`. Dependencies are the
standard library only. No third-party import enters
`plugin/skills/**/scripts/`. The dependencies declared in `pyproject.toml` are
development tools and never ship as a runtime requirement.

The supported runtime floor is Python 3.10 (`requires-python`). Python 3.9 has
reached end of life, and ruff and mypy target `py310`, so scripts may use
language features up to 3.10.

## Environment

Development uses [uv](https://docs.astral.sh/uv/). `.python-version` pins the
development interpreter to 3.12, which affects only the uv-managed `.venv`, not
the runtime of an installed plugin. `uv run` syncs the `dev` dependency group
from `uv.lock` automatically, so no separate install step is needed.

## Tasks

The `Makefile` collects the common commands.

- `make test` runs the test suite with pytest.
- `make fix` applies ruff formatting and autofixes.
- `make lint` runs ruff format in check mode, ruff check, and mypy.

`make fix` is the pass to run before committing; `make lint` is the verification
pass. Run `make fix` before `make lint`.

## Code style

Formatting and linting are handled by ruff. Type checking is handled by mypy over
the plugin skills and `tests`. Scripts are fully type-annotated, and mypy is
expected to report no problems.

Avoid silent fallbacks. Configuration and runtime problems surface as explicit
errors carrying a user-actionable `action`, not a degraded result.

## Tests

Tests live outside the skills, at the repository root under `tests/`, as pytest
functions split by skill into directories. They assert each CLI's process
boundary (exit code, the stdout and stderr JSON, any written files), not internal
functions.

- `tests/conftest.py` provides a subprocess runner that invokes a skill CLI with
  the given arguments.
- `tests/example_skill/` verifies the example CLI by concern: `test_summary.py`
  covers the reported shape and the empty-result path, and `test_errors.py`
  covers non-numeric arguments.

Enumerate matrix cases with `@pytest.mark.parametrize`, and keep any temporary
state in `tmp_path`. Tests assert behavior observable at the CLI boundary and do
not fix internal composition.

## CLI contract

Each skill CLI prints one JSON document on stdout and uses meaningful exit codes.
The convention across the template is exit 0 for an affirmative or successful
result, 1 for a valid request with a negative or empty result, and 2 for a
configuration or runtime error. On exit 2, the CLI prints JSON to stderr carrying
an `action` describing what the user should fix.

The example CLI, `plugin/skills/example-skill/scripts/summarize.py`, takes a list of
numbers as arguments and reports their count, sum, min, max, and mean.

## Distribution boundary

The repository root is the marketplace root for Claude Code and Codex. The
marketplace manifests at `.claude-plugin/marketplace.json` and
`.agents/plugins/marketplace.json` point to `./plugin`.

The `plugin/` directory is the plugin root. Component directories such as
`skills/` live beside the plugin manifests `.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json`, and `plugin.json`; clients do not load components
nested inside either client-manifest directory. Development assets at the
repository root support template authors and do not enter the installable
plugin.
