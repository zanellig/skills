---
name: hitl-handoff
description: Post a standardized human-in-the-loop handoff comment on a PR or issue when agent work is finished but acceptance criteria still depend on a human. Use when a slice / scoped issue is moving to HITL — `ready-for-human` label, Cloudflare/AWS/Vercel dashboard work, account-bound resource creation, DNS, secrets, manual verification, anything an agent cannot do. The comment uses a fixed four-section format (context line, numbered steps with exact commands and `Refs:` citations into local skills or ADRs, verification checklist, merge signal) so the next human knows exactly what to do without re-reading the conversation.
argument-hint: "<pr-or-issue-number>"
---

# HITL handoff

When agent work for a slice or scoped issue is complete but acceptance criteria still need a human, post a comment in this exact format. The reader is a human who is not in the conversation and does not want to skim the diff to find their TODO list.

## When to use

- A slice/issue is labeled `ready-for-human` (see `docs/agents/triage-labels.md`)
- Remaining work is dashboard-only (Cloudflare / Vercel / Supabase / Resend UI)
- Remaining work needs cloud account access, secrets, DNS, or domain mapping
- Remaining work is manual verification — curl, browser check, inbox check

## Where to post

If a PR is open for the work, comment on the PR (`gh pr comment <n> --body ...`). Otherwise comment on the parent issue (`gh issue comment <n> --body ...`). See `docs/agents/issue-tracker.md` for `gh` conventions in this repo.

## Format

```md
## Human handoff — <scoped name> remaining acceptance criteria

<one-line context: which issue, why HITL>

### 1. <action verb + object>

<one-sentence rationale>

` ``bash
<exact command>
` ``

Refs: <skill path or ADR path>:<section or line>

### 2. ...

(repeat for each remaining acceptance criterion)

### Verification checklist

- [ ] <observable check 1>
- [ ] <observable check 2>
- [ ] ...

<one-line merge/close signal: "Once all N boxes are checked, this PR can merge / the issue can close">
```

## Sourcing commands

Commands in the bash blocks must be cited. Pull them from one of:

- `.claude/skills/<name>/SKILL.md` or its `references/*.md`
- `docs/adr/<NNNN>-*.md`
- `CONTEXT.md`
- A doc fetched in this turn (record the URL in `Refs:`)

If you do not have a source, do not invent the command — fetch it first (`context7-mcp`, `WebFetch`, or `cloudflare-docs` search) and then cite that source. Hallucinated CLI flags or dashboard paths are the failure mode this skill exists to prevent.

## Tone

- Concise. One sentence of rationale per section, then the command.
- Imperative ("Run...", "Add...", "Replace...") — not narrative.
- No filler ("Now you'll want to..."), no apologies, no recap of agent work.
- Verification checklist items must be observable — `curl -sI URL`, `gh pr checks`, a row in a dashboard, etc.

## Checklist before posting

- [ ] Every numbered section has a `Refs:` line citing a local file or fetched URL
- [ ] Every bash block is copy-pasteable as-is (no `<PLACEHOLDER>` left unexplained)
- [ ] The verification checklist contains observable checks, not "looks good"
- [ ] The comment is shorter than the PR diff

See [EXAMPLES.md](EXAMPLES.md) for a full worked example.
