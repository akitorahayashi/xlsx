---
name: xlsx
description: Inspect, extract from, and edit .xlsx and .xlsm workbooks — enumerate sheets and parts, read bounded row windows, search cell values or formula sources, and apply cell edits that preserve formulas. Use when a task involves reading, searching, or modifying an Excel workbook.
compatibility: Requires the uv CLI (https://docs.astral.sh/uv/). The first run of each script resolves and downloads its pinned dependencies, which needs network access; later runs use the uv cache and run offline.
---

# xlsx

Two files drive this skill, both run through `uv run --script`:

- [scripts/probe.py](scripts/probe.py) — a read-only CLI with `overview`, `rows`, and `find`.
- [assets/edit.py](assets/edit.py) — a template to copy and fill for a cell edit.

## Model

The scripts are uv PEP 723 single-file scripts. Each declares its own
`requires-python` and its dependencies with exact `==` pins in a header comment,
so uv resolves them against its own managed interpreter. No virtualenv and no
project file is created in the user's repository.

Paths are resolved relative to this `SKILL.md`, not the shell working directory.
Both files run through `uv run --quiet --script <path>`, never by executing the
file directly. `--quiet` keeps uv's first-run dependency-install progress off the
script's stderr, so the stderr JSON contract holds even on the first invocation:

```bash
uv run --quiet --script <skill-dir>/scripts/probe.py overview workbook.xlsx
```

Every subcommand prints one JSON document on stdout. Exit codes: 0 a result was
produced; 1 the request was valid but empty (`find` with no match, `rows` with no
data rows); 2 a usage or runtime error, with one JSON document carrying `error`
and an actionable `action` on stderr.

## Cost

The read path selects a backend by what is asked for, because the cost gap is one
to two orders of magnitude. These are measured on a 237MB workbook (21 sheets,
largest sheet 191MB of XML, 1.45M formula cells):

| Path | Backend | Cost on that workbook |
| ---- | ------- | --------------------- |
| `overview` | stdlib zipfile + calamine | ~1s, no openpyxl load |
| `rows` / `find` (values) | python-calamine | 1–2s for a full scan |
| `rows --formulas` / `find --formulas` | openpyxl | tens of seconds, GBs of RAM |

The rule that follows: for `rows`, never reach for `--formulas` on a large sheet
without a `--range` bound. A whole-sheet openpyxl load of a 128k-row formula sheet
costs tens of seconds and gigabytes; the same window under `--range A1:L50` is
instant. `find` has no range bound, so `find --formulas` is inherently a full
openpyxl scan; bound its cost with `--sheet` to one sheet and `--max-matches` to
stop early, and prefer default (calamine) `find` unless formula sources are the
target.

## Inspection first

Locate before extracting. Run `overview` for the sheet and part inventory, then
`find` to locate a value or header, then `rows` with a `--range` to extract a
bounded window. A full sheet is never dumped to answer a location question.

## Reading rows

```bash
probe.py rows <file> <sheet> [--range A1:F200] [--header-row N] [--max-rows N]
                             [--keep-empty-rows] [--formulas] [--format json|csv|tsv]
```

- Without `--header-row`, `rows` holds arrays and `fields` is null. With it, the
  named row supplies field names, that row is excluded from the data, and rows
  become objects.
- `--range` bounds the extraction in A1 notation and is what keeps a large sheet
  affordable.
- Fully empty rows are omitted and counted in `emptyRowsOmitted`, because the used
  range inflates from stray formatting; `--keep-empty-rows` retains them so
  positions stay aligned. `--max-rows` caps rows and sets `truncated`. For `csv`
  and `tsv`, omission and truncation are reported as notes on stderr.
- `--max-rows` and `--max-matches` take a positive integer. Zero and negative
  values are usage errors, not an empty result.
- The `backend` field names what produced the values, because the two backends
  differ in typing. calamine reports every number as a float (`3.0`, not `3`) and
  an empty cell as null; openpyxl keeps integer typing. Under both, an empty cell
  is null in JSON and empty in CSV/TSV, dates and datetimes and times are ISO-8601
  strings, and durations are seconds. A merged range holds its value in the
  top-left cell only.

## Formulas and cached values

A default read returns the value the spreadsheet application cached at its last
save. `--formulas` switches `rows` and `find` to openpyxl and returns the formula
sources (`=SUM(...)`) at openpyxl cost. `overview` reports formula presence per
sheet in `hasFormulas` without paying that cost. A workbook that a spreadsheet
application has never saved carries no cached values, so a default value read of
its formula cells returns null; read such cells with `--formulas`. An edit through
`edit.py` strips cached values the same way (see Preservation limits).

## Editing

`edit.py` is a template to copy and fill, not a CLI to call in place:

1. Make a working directory with `mktemp -d` and copy the template into it.
2. Fill the single `edit(workbook) -> list[str]` function; return one summary line
   per change. The workbook loads with `data_only=False`, so formulas survive.
3. Run it with explicit input and output paths (the same path twice edits in
   place; the save is atomic through a sibling temporary file):

   ```bash
   uv run --quiet --script <dir>/edit.py input.xlsx output.xlsx
   ```

4. Verify the result with `probe.py`, not with the script's own summary: read back
   the changed cells and confirm formulas and merged ranges survived.

An unfilled template exits 2 with an action.

## Preservation limits

openpyxl models workbook parts only partially, so a load-and-save cycle drops or
alters the parts it does not model. Measured on a 237MB workbook by comparing the
part inventory and cell reads before and after an in-place single-cell edit (the
edit itself took 33s and 1.5GB of RAM):

- Cached formula values are stripped. openpyxl reads formula sources, not the
  cached values, and writes the formulas back with no cached value. After an edit
  a default value read (`rows`, `find`) of every formula cell returns null, and
  the sheet's used range collapses to the non-formula cells; the formula sources
  survive and stay readable with `--formulas`. A spreadsheet application recomputes
  and re-caches the values on its next save. This is the largest effect on a
  formula-heavy workbook.
- Dropped entirely: the drawing parts, the VML drawing, the legacy comments part,
  and the threaded comments part.
- Pivot table definitions survive, but their pivot caches are reduced, so a
  surviving pivot table is not guaranteed to refresh.
- Preserved: literal cell values, formula sources, merged ranges, and sheet
  visibility.

Edit a workbook that carries formulas whose cached values are read downstream,
pivot tables, drawings, or comments only when losing those is acceptable. Verify
the specific parts and cells you care about with `overview` and `rows` after the
edit, and reopen the result in a spreadsheet application when cached formula
values are needed.

## Pivot output sheets

Pivot table output sheets carry no cell data; both backends read them as empty,
and the computed pivot results are not readable through either backend. `overview`
reports such sheets as `empty: true`.

## Temporary artifacts

Copies, intermediate workbooks, and filled templates live under a `mktemp -d`
directory removed on exit, including on failure. The user's original workbook is
never written in place unless that is the explicit request.
