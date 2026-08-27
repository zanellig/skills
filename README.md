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

The same command updates generated skill-reference sections in existing category and subcategory `README.md` files. It preserves content outside the generated markers and does not create new category READMEs.

You should not need to run it by hand. Enable the pre-commit hook once per clone and it regenerates and stages the reference on every commit:

```sh
git config core.hooksPath .githooks
```

CI runs `bun scripts/gen-reference.mjs --check` and fails if the committed reference is stale, so this stays a backstop rather than the thing you rely on.
