---
name: prioritize
description: Pick the one triaged issue to work on next and say why.
argument-hint: "[label, milestone, or issue numbers to narrow the pool]"
disable-model-invocation: true
---

# Prioritize

Read the triaged issues on the project issue tracker and decide which one the user works on next. The answer is one issue, not a menu. This skill only reads the tracker. Labels, comments, and issue state stay as they are.

Use the label strings from `docs/agents/triage-labels.md`. When that file is missing, use the canonical names `ready-for-agent` and `ready-for-human`.

## Process

1. **Build the pool.** List open issues under each of the two labels:

   ```sh
   gh issue list --state open --label <label> --limit 200 \
     --json number,title,labels,body,createdAt,assignees,milestone,blockedBy,blocking,closedByPullRequestsReferences
   ```

   Drop an issue with work in flight: an open PR in `closedByPullRequestsReferences`, or an assignee other than the user. Apply any narrowing the user gave. The step is done when every remaining issue is one the user could start today.

2. **Map the critical path.** An issue's blockers are its `blockedBy` entries plus any `Blocked by #n` line in its body. Drop issues with an open blocker. For each survivor, count the open issues it unblocks, directly or transitively, searching all open issues, not only the pool. The step is done when every survivor has a count.

3. **Rank.** Walk these rules in order. The first rule that separates two issues decides between them.
   1. The goal the user stated for this session, if any.
   2. A bug that loses data, opens a security hole, or breaks a core user flow.
   3. The longer critical path: the higher unblock count.
   4. The milestone with the nearest due date.
   5. `ready-for-agent` over `ready-for-human`, since an agent can run it AFK while the user works on something else.
   6. The smaller scope, judged from the brief's acceptance criteria.
   7. The oldest issue.

4. **Verify the pick.** Check the top issue's brief against the code. The files, functions, and behaviors it names must still exist, and the code must not already do what it asks (search by domain concept, as `/triage` does). If the brief is stale or the work is done, note it, drop the issue, and verify the next one. The step is done when one issue passes.

5. **Recommend.** Reply in this shape, then end the turn and let the user decide whether to start:

   ```md
   **Next: #42 Title** (`ready-for-agent`)
   Why: the rule that decided it, with the fact behind it ("unblocks #50, #51, #57").
   Start: the first concrete move, such as the file to open or "hand it to an agent".

   Runner-ups:
   - #38 Title: the rule it lost on.
   - #45 Title: the rule it lost on.

   Skipped: 3 blocked, 1 with an open PR, 1 stale brief.
   ```

When the pool is empty, say so and point the user to `/triage`.
