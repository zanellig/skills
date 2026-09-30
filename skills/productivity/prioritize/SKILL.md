---
name: prioritize
description: Pick the most important open PR or issue to work on next and say why.
argument-hint: "[scope: labels, milestone, PR or issue numbers, states]"
disable-model-invocation: true
---

# Prioritize

Choose one next unit of work in the current project: continue an open PR or start an issue. With no arguments, compare all open PRs and issues. Recommend the next action; invoking this skill alone leaves code and tracker state unchanged.

Use the label strings from `docs/agents/triage-labels.md`. When that file is missing, use the canonical names `ready-for-agent` and `ready-for-human`.

## Process

1. **Build the pool.** Read open issues and PRs independently, including untriaged issues and PRs without linked issues:

   ```sh
   gh issue list --state open --limit 1000 \
     --json number,title,url,labels,body,createdAt,assignees,milestone,blockedBy,blocking
   gh pr list --state open --limit 1000 \
     --json number,title,url,labels,body,createdAt,assignees,milestone,isDraft,closingIssuesReferences
   ```

   When either list returns exactly the limit, double it and rerun until it returns fewer. Use equivalent tracker tools when `gh` is unavailable.

   Group a PR and its linked issues as one deliverable. Also check body references for relationships missing from closing links. Keep independent PRs in the pool. Readiness labels describe the next action, rather than determine importance.

   By default, leave work assigned to someone other than the user to its owner. User-specified scope overrides the default. Keep blocked work visible to identify its prerequisites; recommend a next action that can make progress. An issue blocker counts only while its state is `OPEN`, including body references such as `Blocked by #n`. For stacked PRs, verify that the prerequisite merged or its required changes otherwise landed.

   The pool is complete when it covers the requested scope and related prerequisites.

2. **Rank by importance.** Read briefs and discussions for the contenders. Weigh the user's current goal, urgency, severity and impact, work unblocked directly or transitively across all open issues, and deadlines. Identify the highest-priority issue even when it needs triage. Recency, age, readiness labels, and small scope are secondary signals; explain any departure from explicit project priorities.

3. **Prefer finishing valuable work.** Among work of comparable importance, prefer continuing the most important actionable PR, using remaining effort to break ties. Resume the existing PR rather than recommend duplicate implementation. An urgent issue can outrank every open PR. If finishing a PR first enables or briefly precedes the highest-priority issue, justify the delay and name that issue as next. Recommend one PR, then reassess priorities; unrelated open PRs are not a prerequisite queue.

4. **Verify the pick.** For a PR, inspect its current diff, acceptance criteria, checks, review threads, conflicts, and dependencies. Name what remains before merge; green checks alone do not establish completion. For an issue, search the code by domain concept to see whether its brief or body is already satisfied. When triage or a human decision is needed, name that as the first action. Drop completed work from the recommendation and verify the next candidate. The step is done when one PR or issue has a concrete next action and evidence for its priority.

5. **Recommend.** Reply concisely in this shape, then end the turn:

   ```md
   Next: PR or issue #42, title and link.
   Why: the deciding facts, including why it outranks the strongest alternative.
   Start: the first concrete action and who can take it.
   Then: the highest-priority issue to start promptly after this PR, if different.

   Skipped: relevant blockers, other owners, or already completed work.
   ```

When nothing can progress within scope, say what prevents it and name the decision or prerequisite needed.
