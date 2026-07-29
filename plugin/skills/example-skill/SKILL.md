---
name: example-skill
description: Use this skill when the user asks to summarize a list of numbers, for example the count, sum, min, max, and mean. This is the template's example skill; replace it with your own.
---

# Example Skill

Summarize a list of numbers and report the totals. This is the example skill
shipped with the template. Rename the directory, rewrite this file, and replace
the CLI with your own.

Files are referenced by path relative to this skill directory. Do not assume the
shell working directory is this directory.

- [scripts/summarize.py](scripts/summarize.py) — the CLI. Prints one JSON document.

## Run

```bash
python3 <skill-dir>/scripts/summarize.py 10 6 2
```

Pass the numbers to summarize as arguments. Decimals and negative numbers are
accepted.

## Read the result

The CLI prints one JSON document to stdout with `count`, `sum`, `min`, `max`, and
`mean`. Exit codes:

- 0: summarized at least one number.
- 1: no numbers were given; the result carries a `hint`.
- 2: an argument was not a number. stderr carries JSON with an `error` and an
  actionable `action`. Relay the action to the user and stop.

## Report

Answer with the totals directly. For an empty result, relay the hint. For an
error, relay the action.
