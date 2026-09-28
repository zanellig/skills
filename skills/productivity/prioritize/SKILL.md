---
name: prioritize
description: Pick the one triaged issue to work on next and say why.
argument-hint: "[narrowing or widening: labels, milestone, issue numbers, states]"
disable-model-invocation: true
---

# Prioritize

Read the triaged issues on the project issue tracker and decide which one the user works on next. The answer is one issue, not a menu. This skill only reads the tracker. Labels, comments, and issue state stay as they are.

Use the label strings from `docs/agents/triage-labels.md`. When that file is missing, use the canonical names `ready-for-agent` and `ready-for-human`.

## Process

1. **Build the pool.** The default pool is the open issues under the two labels:

   ```sh
   gh issue list --state open --label <label> --limit 200 \
     --json number,title,labels,body,createdAt,assignees,milestone,blockedBy,blocking,closedByPullRequestsReferences
   ```

   It leaves out issues with work in flight (an open PR in `closedByPullRequestsReferences`, or an assignee other than the user) and issues with an open blocker (a `blockedBy` entry or a `Blocked by #n` line in the body). The user can narrow the pool, for example to a label, a milestone, or a list of issues. They can also widen it, for example to `needs-triage` issues or to blocked and in-flight ones. Their scope replaces the default wherever the two conflict. The step is done when the pool matches that scope.

2. **Map the critical path.** For each issue in the pool, count the open issues it unblocks, directly or transitively, searching all open issues, not only the pool. The step is done when every issue has a count.

3. **Rank.** Weigh the pool against these factors. The list gives their default order of importance. Depart from that order when the facts of this repo argue for it, and name the reason in the recommendation.
   1. The goal the user stated for this session.
   2. A bug that loses data, opens a security hole, or breaks a core user flow.
   3. The longer critical path: the higher unblock count.
   4. The milestone with the nearest due date.
   5. `ready-for-agent` over `ready-for-human`, since an agent can run it AFK while the user works on something else.
   6. The smaller scope, judged from the brief or the issue body.
   7. The oldest issue.

4. **Verify the pick.** Check the top issue's brief, or its body when it has no brief, against the code. The files, functions, and behaviors it names must still exist, and the code must not already do what it asks (search by domain concept, as `/triage` does). If the issue is stale or the work is done, note it, drop the issue, and verify the next one. The step is done when one issue passes.

5. **Recommend.** Reply in this shape, then end the turn and let the user decide whether to start:

   ```md
   **Next: #42 Title** (`ready-for-agent`)
   Why: what decided it, with the fact behind it ("unblocks #50, #51, #57").
   Start: the first concrete move, such as the file to open or "hand it to an agent".

   Runner-ups:
   - #38 Title: why it lost.
   - #45 Title: why it lost.

   Skipped: 3 blocked, 1 with an open PR, 1 stale brief.
   ```

When the pool is empty, say so, list what the scope left out, and suggest widening it or running `/triage`.
