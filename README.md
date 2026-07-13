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
- **[ship-slice](./skills/productivity/ship-slice/SKILL.md)** — Drive a slice through Codex review rounds to a merged PR.

### Web

- **[tanstack-nonblocking-loaders](./skills/web/tanstack-nonblocking-loaders/SKILL.md)** — Instant navigations in TanStack Start via non-blocking loaders that warm the React Query cache.
