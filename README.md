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

See [skills/README.md](./skills/README.md) for the full list, generated from each skill's frontmatter:

```sh
bun scripts/gen-reference.mjs
```
