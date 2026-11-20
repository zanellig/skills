---
name: python-development
description: Python toolchain with uv, Ruff, basedpyright, pytest, and pydantic-settings. Use when creating a Python project, adding dependencies, or setting up linting, type checking, tests, settings, or commit hooks.
license: MIT
---

# Python development

Use uv for dependencies and environments, Ruff for linting and formatting,
basedpyright for static types, pytest for tests, and pydantic-settings for
application configuration in new Python projects.

In an existing project, use the tools it already has. Switch existing tool
choices to this stack only when the user asks. The sections below apply to tools
already in use or that the user has asked to set up.

For FastAPI applications read [references/fastapi.md](references/fastapi.md).

## Dependencies and execution

- Manage project dependencies in `pyproject.toml` with `uv add` and
  `uv add --dev`. Keep Ruff, basedpyright, and pytest in the development group;
  pydantic-settings is a runtime dependency when application settings are needed.
- Commit `uv.lock`. Use `uv run` for project commands and tests so they use the
  project environment. Use `uv sync --locked` in CI to reject a stale lockfile.
- Declare the supported Python range in `requires-python`. Use `uv python pin`
  to select a compatible development interpreter in `.python-version`, and run
  CI against the supported versions. Reuse existing source layout.

## Linting and formatting

- Configure Ruff in `pyproject.toml`. Preserve existing rule choices and enable
  its `I` rules for import sorting, using `extend-select` when adding to an
  existing ruleset. Ruff covers isort's role in this stack.
- Use `uv run ruff check --fix .` and `uv run ruff format .` when applying
  fixes. Review the changes; apply unsafe fixes only after checking their effect.
- Leave Ruff's `target-version` unset so normal config discovery infers it from
  `requires-python`. If a configuration file is passed via `--config`, inference
  is disabled; set a target matching the minimum supported version in that case.

## Static types

- Configure `[tool.basedpyright]` in `pyproject.toml`, or reuse the project's
  existing basedpyright configuration. Set `pythonVersion` explicitly to the
  minimum supported Python version and include source and test paths.
  For new projects use `typeCheckingMode = "standard"`; preserve existing
  strictness in established projects. Resolve imports against the uv project
  environment. Unlike Ruff, basedpyright defaults to the current interpreter's
  version rather than reading `requires-python`.
- Run `uv run basedpyright`. Prefer correcting types and narrowing optional
  values to suppressions. Keep any necessary exclusions or suppressions narrow
  and explain them. Report pre-existing diagnostics separately instead of
  weakening checks to make the command pass.

## Tests and settings

- Write and run tests with pytest through `uv run pytest`. Reuse existing
  fixtures and discovery conventions; run focused tests while iterating.
- Use `pydantic_settings.BaseSettings` for environment-based application
  configuration. Define typed fields and validation in a settings model rather
  than scattering environment reads throughout application code.
- Make `.env` loading explicit when used. Let tests supply settings or override
  environment variables without depending on a developer's local `.env` file.

## Optional commit hooks

If prek is already configured, use its existing hooks. Otherwise finish the
requested work, then offer prek in the final report. Leave it uninstalled and
its configuration and Git hooks unchanged until the user accepts, unless the
user has already requested or accepted its setup.

If accepted, run `uv add --dev prek`. Reuse the existing hook configuration and
preserve unrelated hooks. For new Python hooks use `repo: local` and
`language: system` so hooks and CI use the versions in `uv.lock`:

- Ruff lint entry: `uv run --no-sync ruff check --fix`.
- Ruff format entry: `uv run --no-sync ruff format`, after the lint hook.
- Type-check entry: `uv run --no-sync basedpyright`, with `pass_filenames: false`
  and `always_run: true` to check the configured project even for config changes.

Use `types_or: [python, pyi]` for the Ruff hooks. Sync the project environment
with `uv sync --locked` after dependency changes and before running hooks on a
fresh checkout, since `--no-sync` uses the existing environment. Verify with
`uv run prek run --all-files` before enabling hooks with `uv run prek install`.

## Completion

For toolchain setup, record these commands in the existing contributor guide,
or in the README's development section if there is no guide. Add them to the
existing CI. If there is no CI, create it when CI setup is part of the requested
work; otherwise report that CI is absent.

```sh
uv sync --locked
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync basedpyright
uv run --no-sync pytest
```

If checks need optional dependencies or non-default groups, select the required
`--extra <name>` or `--group <name>` on `uv sync --locked` locally and in CI.
Use `--all-extras` only when all extras are needed and compatible.

Setup is complete when the commands pass locally, the documented commands match
the configuration, and CI runs the same checks where configured. Report any
failed or unrun checks and any missing CI integration. For scoped changes, run
the relevant existing checks.
