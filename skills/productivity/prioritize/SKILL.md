---
name: prioritize
description: Pick the one triaged issue to work on next and say why.
argument-hint: "[narrowing or widening: labels, milestone, issue numbers, states]"
disable-model-invocation: true
---

# Prioritize

Read the triaged issues on the project issue tracker and decide which one the user works on next. The answer is one issue, not a menu. You should only read the tracker of the project the user is working on. Labels, comments, and issue state stay as they are.

Use the label strings from `docs/agents/triage-labels.md`. When that file is missing, use the canonical names `ready-for-agent` and `ready-for-human`.

## Process

1. **Build the pool.** The default pool is the open issues under the two labels:

   ```sh
   gh issue list --state open --label <label> --limit 1000 \
     --json number,title,labels,body,createdAt,assignees,milestone,blockedBy,blocking,closedByPullRequestsReferences
   ```

   When a label returns exactly the limit, double it and rerun until it returns fewer.

   It leaves out issues assigned to someone other than the user and issues with an open blocker (a `blockedBy` entry or a `Blocked by #n` line in the body). Issues with an open PR in `closedByPullRequestsReferences` stay in: that PR is started work. For each one, read what the PR still needs to merge:

   ```sh
   gh pr view <n> --json isDraft,mergeable,reviewDecision,statusCheckRollup,latestReviews
   ```

   The user can narrow the pool, for example to a label, a milestone, or a list of issues. They can also widen it, for example to `needs-triage` issues, blocked ones, or ones assigned to someone else. Their scope replaces the default wherever the two conflict. The step is done when the pool matches that scope.

2. **Map the critical path.** For each issue in the pool, count the open issues it unblocks, directly or transitively, searching all open issues, not only the pool. The step is done when every issue has a count.

3. **Rank.** Weigh the pool against these factors. The list gives their default order of importance. Depart from that order when the facts of this repo argue for it, and name the reason in the recommendation.
   1. The goal the user stated for this session.
   2. A bug that loses data, opens a security hole, or breaks a core user flow.
   3. An open PR, weighted by how little it still needs: finishing started work closes an issue sooner than starting new work.
   4. The longer critical path: the higher unblock count.
   5. The milestone with the nearest due date.
   6. `ready-for-agent` over `ready-for-human`, since an agent can run it AFK while the user works on something else.
   7. The smaller scope, judged from the brief or the issue body.
   8. The oldest issue.

4. **Verify the pick.** For an issue with an open PR, list what stands between the PR and merge: failing checks, unresolved review comments, conflicts, unmet acceptance criteria. For any other issue, check that the code does not already do what its brief, or its body when it has no brief, asks for (search by domain concept, as `/triage` does). If the work is done, note it, drop the issue, and verify the next one. The step is done when one issue passes.

5. **Recommend.** Reply in this shape, then end the turn and let the user decide whether to start:

   ```md
   **Next: #42 Title** (`ready-for-agent`)
   Why: what decided it, with the fact behind it ("unblocks #50, #51, #57").
   Start: the first concrete move, such as "finish PR #61: fix the failing e2e check", the file to open, or "hand it to an agent".
   Then: the issue this one clears the way for, when it unblocks something important.

   Runner-ups:
   - #38 Title: why it lost.
   - #45 Title: why it lost.

   Skipped: 3 blocked, 1 assigned to someone else, 1 already done.
   ```

When the pool is empty, say so, list what the scope left out, and point the user to `/triage`.
