# Agent Skills

A small collection of reusable agent skills.

## Quickstart

Install all skills:

```sh
bunx skills add zanellig/skills
```

Install selected skills:

```sh
bunx skills add zanellig/skills --skill bump --skill commit
```

Install from a local checkout:

```sh
bunx skills add ~/projects/skills --skill bump --skill commit --full-depth
```

## Reference

### Misc

- **[bump](./skills/misc/bump/SKILL.md)** — Create and push semver version tags.

### Productivity

- **[commit](./skills/productivity/commit/SKILL.md)** — Commit current changes with a descriptive message.
