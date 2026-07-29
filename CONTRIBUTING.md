# Contributing

A multi-client Agent Skills plugin whose skill is backed by Python scripts.
User-facing documentation is in [README.md](README.md); this guide covers the
development workflow.

## Runtime contract

The skill CLIs run through `uv run --script` as PEP 723 single-file scripts. Each
script under `plugin/skills/**/scripts/` and `plugin/skills/**/assets/` declares
its own `requires-python` and its dependencies with exact `==` pins in a header
comment. The runtime dependency of the plugin is uv itself, not a preinstalled
interpreter or package set.

uv resolves `requires-python` against its own managed interpreters, independently
of the user's `python3`. The floor is Python 3.12.

Pins are exact. A resolved script environment is never re-resolved on later runs,
so a lower-bound specifier would silently fix a different version per machine and
per first-run date, and version churn would accumulate permanently in the uv
cache. Declare `==` versions, never bare or lower-bound specifiers.

## Environment

Development uses [uv](https://docs.astral.sh/uv/). `.python-version` pins the
development interpreter to 3.12. `uv run` syncs the `dev` dependency group from
`uv.lock` automatically, so no separate install step is needed.

The `pyproject.toml` dependencies are development tools (pytest, ruff, mypy) plus
openpyxl and python-calamine. openpyxl and python-calamine are present only so
tests can build fixture workbooks in the development virtualenv; they are not a
runtime requirement of the plugin, whose scripts declare their own dependencies
inline.

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
functions split by concern. Skill tests assert a script's process boundary (exit
code, the stdout and stderr JSON, any written files), not internal functions.

- `tests/conftest.py` provides a runner that invokes a skill script through
  `uv run --script <path> <args...>` and returns the completed process.
- `tests/xlsx/` builds its own fixture workbooks with openpyxl into `tmp_path`,
  so no test depends on any external workbook, and covers `overview`, `rows`,
  `find`, the error surface, and the `edit.py` round trip.
- `tests/test_manifests.py` asserts that the plugin identity duplicated across
  the manifests stays consistent. It is the one test that is not a process
  boundary, because each client reads its own manifest and nothing else catches a
  partial edit.

Enumerate matrix cases with `@pytest.mark.parametrize`, and keep any temporary
state in `tmp_path`. Tests assert behavior observable at the CLI boundary and do
not fix internal composition.

## CLI contract

Each skill script prints one compact JSON document on stdout, except
`rows --format csv|tsv`, which prints delimited text with its notes on stderr.
Exit codes are meaningful: 0 for a produced result, 1 for a valid request with an
empty result (`find` with no match, `rows` with no data rows), and 2 for a usage
or runtime error. On exit 2, the script prints JSON to stderr carrying an `action`
describing what the user should fix.

## Distribution boundary

The repository root is the marketplace root for Claude Code and Codex. The
marketplace manifests at `.claude-plugin/marketplace.json` and
`.agents/plugins/marketplace.json` point to `./plugin`.

The `plugin/` directory is the plugin root. Component directories such as
`skills/` live beside the plugin manifests `.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json`, and `plugin.json`; clients do not load components
nested inside either client-manifest directory. Development assets at the
repository root support development and do not enter the installable plugin.
