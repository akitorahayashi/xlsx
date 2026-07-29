# skills-plugin-py

A template for one GitHub-installable Agent Skills plugin marketplace whose
skills are backed by Python scripts. The repository root is the marketplace root
for Claude Code and Codex, and the `plugin/` directory is the plugin root for
Claude Code, Antigravity CLI, and Codex. A shared `plugin/skills/` directory
supplies every client; each skill drives a standard-library Python CLI that
prints one JSON document.

## Structure

```text
skills-plugin-py/
├── .claude-plugin/
│   └── marketplace.json                 # Claude Code marketplace manifest
├── .agents/
│   └── plugins/
│       └── marketplace.json             # Codex marketplace manifest
├── plugin/
│   ├── skills/
│   │   └── example-skill/
│   │       ├── SKILL.md
│   │       └── scripts/summarize.py   # stdlib-only CLI, one JSON document, exit codes 0/1/2
│   ├── .claude-plugin/plugin.json     # Claude Code manifest
│   ├── .codex-plugin/plugin.json      # Codex manifest
│   └── plugin.json                     # Antigravity CLI manifest
├── tests/                              # process-boundary tests
├── pyproject.toml                      # development tools only
├── Makefile                            # make test / fix / lint
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

## The example skill

`plugin/skills/example-skill` demonstrates the conventions every skill in this template
follows. Its CLI takes a list of numbers as arguments and prints their count,
sum, min, max, and mean as one JSON document. It uses standard-library imports,
explicit validation with an actionable error, and exit codes 0 (result), 1 (no
numbers), and 2 (invalid input, reported as JSON on stderr with an `action`).

## Runtime and development separation

The skill CLIs run on the plugin user's own `python3` with no runtime dependency.
Every script under `plugin/skills/**/scripts/` imports only the standard library, and
the supported floor is Python 3.10. The dependencies in `pyproject.toml` are
development tools (pytest, ruff, mypy) synced by uv into a local `.venv`; they
are never runtime requirements.

The `plugin/` directory is the distributed plugin. Development assets remain at
the repository root and do not enter the installable artifact or add runtime
dependencies.

## Develop

Development uses [uv](https://docs.astral.sh/uv/). `make fix` applies formatting
and autofixes; `make lint` runs ruff and mypy; `make test` runs pytest. Run
`make fix` before `make lint`. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
full workflow and CLI contract.

## Customize

1. Rename the repository to your plugin name.
2. Rename `plugin/skills/example-skill/` to your skill's name and rewrite its
   `SKILL.md`. Replace its CLI under that skill's `scripts/` directory with your
   own, and add optional `references/` and `assets/` directories if the skill
   needs them.
3. Replace `example-plugin` with your plugin name (kebab-case) in the plugin
   manifests and marketplace manifests. Replace `skills-plugin-py` with your
   repository or marketplace name, and replace `your-name` in the Claude Code
   and Codex manifests.
4. Add more skills as sibling directories under `plugin/skills/`, and add tests under
   `tests/`. Group related skills in one plugin rather than splitting one plugin
   per skill.
5. Validate before distributing:

   ```bash
   claude plugin validate .
   claude plugin validate ./plugin
   agy plugin validate ./plugin
   ```

## Install

The repository root is the marketplace root for GitHub distribution. Replace
`owner/skills-plugin-py` with the published repository.

### Claude Code

Claude Code installs the plugin from this repository's marketplace:

```bash
claude plugin marketplace add owner/skills-plugin-py
claude plugin install example-plugin@skills-plugin-py
```

For local development, Claude Code can load the plugin root for the current
session with `claude --plugin-dir ./plugin`.

### Codex

Codex installs the plugin from this repository's marketplace:

```bash
codex plugin marketplace add owner/skills-plugin-py
codex plugin add example-plugin@skills-plugin-py
```

### Antigravity CLI

The `plugin/` directory holds both `plugin.json` and `skills/`, so Antigravity
can install it directly:

```bash
agy plugin install ./plugin
```
