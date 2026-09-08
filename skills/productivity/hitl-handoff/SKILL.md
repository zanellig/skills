---
name: hitl-handoff
description: Post a handoff comment on a PR or issue when agent work is done but acceptance criteria still need a human. Use when a slice or issue is labeled `ready-for-human`, when the remaining work needs account access or a provider dashboard, or when the remaining work is manual verification.
argument-hint: "<pr-or-issue-number>"
---

# HITL handoff

Agent work on a slice or issue is finished, but some acceptance criteria still need a human. Post a comment that hands them a TODO list they can run without reading the diff or the conversation.

## Process

1. **Derive what is left.** Read the issue's acceptance criteria (`gh issue view <n>`). Sort every criterion into one of two buckets: shipped in this work, or still needs a human. Only the second bucket goes in the comment, and each criterion in it becomes one numbered section.

2. **Source every command.** Each bash block cites where its command came from: a local skill file, an ADR, the repo's `CONTEXT.md`, or a doc fetched this turn (cite the URL). When you have no source, fetch one first (`context7-mcp`, `WebFetch`, or a docs search), then cite it. Hallucinated CLI flags and dashboard paths are the failure mode this skill exists to prevent.

3. **Post it.** Comment on the PR when one is open (`gh pr comment <n> --body ...`), otherwise on the parent issue (`gh issue comment <n> --body ...`). Run the checklist below first.

## Format

Four parts in this order: a context line, one numbered section per remaining criterion, a verification checklist, a merge signal. One sentence of rationale per section, then the command, in imperative voice: Run, Add, Replace.

````md
## Human handoff: Slice 1 remaining acceptance criteria

Three criteria on #20 need Cloudflare account access. Run these from the repo root.

### 1. Provision D1, R2, and KV, then replace the placeholders

`wrangler.jsonc` ships with placeholder IDs that the deploy rejects.

```bash
bunx wrangler d1 create mail-cogni-ar
bunx wrangler r2 bucket create mail-cogni-ar-blobs
bunx wrangler kv namespace create KV
```

Paste each printed ID over `REPLACE_WITH_D1_ID` and `REPLACE_WITH_KV_NAMESPACE_ID` in `apps/web/wrangler.jsonc`.

Refs: `.claude/skills/wrangler/SKILL.md`, `d1 create` (line 383), `r2 bucket create` (line 337), `kv namespace create` (line 288)

### 2. Deploy the Worker and map `mail.cogni.ar`

The custom domain is a dashboard-only step.

```bash
cd apps/web && bunx wrangler deploy
```

Then: **Workers & Pages → mail-cogni-ar → Settings → Domains** → add `mail.cogni.ar`.

Refs: `.claude/skills/wrangler/SKILL.md`, section "Quick reference: core commands"

### Verification checklist

- [ ] `bunx wrangler deployments list` shows the new deployment
- [ ] `curl -sI https://mail.cogni.ar/ | head -1` returns `HTTP/2 200`
- [ ] `bunx wrangler email routing dns get cogni.ar` reports records present

Once all three boxes are checked, this PR can merge.
````

## Checklist before posting

- [ ] Every criterion in the "needs a human" bucket has a numbered section
- [ ] Every numbered section has a `Refs:` line citing a local file or a URL fetched this turn
- [ ] Every bash block is copy-pasteable as-is, with any placeholder explained in the text around it
- [ ] Every verification item is observable: a command with a checkable output, or a named row in a dashboard
