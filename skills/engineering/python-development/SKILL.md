---
name: python-development
description: Set up and use uv, Ruff, Basedpyright, pytest, and pydantic-settings when creating or maintaining Python projects.
license: MIT
---

# Python development

Use uv for dependencies and environments, Ruff for linting and formatting,
Basedpyright for static types, pytest for tests, and pydantic-settings for
application configuration. Configure missing tools during project setup; keep
tool migrations within the scope of the requested work in existing projects.

For FastAPI applications read [references/fastapi.md](references/fastapi.md).

## Dependencies and execution

- Manage project dependencies in `pyproject.toml` with `uv add` and
  `uv add --dev`. Keep Ruff, Basedpyright, and pytest in the development group;
  pydantic-settings is a runtime dependency when application settings are needed.
- Commit `uv.lock`. Use `uv run` for project commands and tests so they use the
  project environment. Use `uv sync --locked` in CI to reject a stale lockfile.
- Align the Python version used locally and in CI with the project's supported
  versions. Reuse existing configuration and source layout.

## Linting and formatting

- Configure Ruff in `pyproject.toml`. Preserve existing rule choices and enable
  its `I` rules for import sorting, using `extend-select` when adding to an
  existing ruleset. Ruff covers isort's role in this stack.
- Use `uv run ruff check --fix .` and `uv run ruff format .` when applying
  fixes. Review the changes; apply unsafe fixes only after checking their effect.
- Match Ruff's target Python version to the minimum supported Python version.

## Static types

- Configure `[tool.basedpyright]` in `pyproject.toml`, or reuse the project's
  existing Basedpyright configuration. Set the supported Python version,
  checked source and test paths, and an explicit type-checking mode. Preserve
  existing strictness and resolve imports against the uv project environment.
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

If prek is already configured, use its existing hooks. Otherwise ask the user
whether to add prek before installing it, writing its configuration, or enabling
Git hooks. Continue the rest of the work while that choice is pending; an
unanswered question leaves prek uninstalled.

If accepted, manage prek with uv, reuse any `.pre-commit-config.yaml`, and run
Ruff's lint fixes before formatting. Keep type checking against the complete
configured project rather than only the staged filenames. Preserve existing
hooks and verify the configuration with `uv run prek run --all-files` before
enabling it with `uv run prek install`.

## Completion

For toolchain setup, document and wire these checks into the existing CI:

```sh
uv sync --locked
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync basedpyright
uv run --no-sync pytest
```

Install the runtime dependencies needed by type checking and tests, not just the
development group. For scoped changes, run the relevant checks and report any
remaining failures or checks that could not run.
