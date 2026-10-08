---
name: ship-slice
description: Implement a vertical slice, complete Codex review rounds, and merge the PR.
argument-hint: "<slice issue or handoff path> [passes]"
disable-model-invocation: true
---

# Ship slice

Requires authenticated `gh` access and the Codex GitHub app installed.

## Process

1. **Load the work.** Read the handoff first if supplied, then the slice issue and parent spec/PRD. Establish acceptance criteria before coding. The second argument sets the review pass count, default 3. Read the repo's recorded review trigger; use a repo override or an account setting matching `gh api user -q .login`. For a missing, unscoped, or different-account setting, follow [review-trigger setup](references/workflow-details.md#review-trigger-setup).

2. **Implement and open the PR.** Implement to acceptance criteria. Every behavior change gets a test. Run the project's tests/checks, format, and commit by scope with conventional-commit messages, including any review-setting update. Push the implementation before opening the PR. Every push uses an explicit remote and branch, such as `git push origin <branch>`; verify `git ls-remote origin refs/heads/<branch>` equals `git rev-parse HEAD`. Title the PR `Slice <id>: <summary>`; reference the parent spec and name the issues it closes with closing keywords. Use "Codex" without an `@` in the body. Apply the activation rules below when creating the PR or making an authorized draft-to-ready transition. For an existing PR, resume its latest round for the remote head; if pending, choose a `SINCE` preceding that activity and wait.

3. **Complete review rounds.** Activate and wait according to the tables below. Triage each finding before changing code:

   - **Code-evident**: the cited lines are wrong with no runtime assumption. Confirm by reading them, then fix.
   - **Behavior-dependent**: the claim rests on runtime, data shape, config, environment, concurrency, or external services. Reproduce it first with a test, script, or command that goes red on the claim; it is confirmed once red, and the reproduction becomes its regression test. For several such findings, follow [delegated validation](references/workflow-details.md#delegated-validation).

   A claim that holds only "probably" or "usually" is behavior-dependent. Weigh each confirmed finding's impact against the acceptance criteria, current scope, and documented product direction. Fix or file confirmed, relevant findings; explain the rest in their threads. Add or update tests for observable behavior changes or meaningful regression risks.

   Answer every finding in its own thread with the fix commit and change, or the substantive reason for no code change. For behavior-dependent findings, name the reproduction or what failed to reproduce; the thread already anchors the cited lines. Use [thread operations](references/workflow-details.md#thread-operations) to reply and resolve bot-opened threads. Hand human-opened threads to the user and stop. Keep replies plain; the bot reads them only when @-mentioned, and a mention starts an in-thread task that spends Codex usage. Escalate with `@codex` only when a later round repeats a declined finding.

   Commit and push fixes using the push checks in step 2, then continue until Codex reports a clean round or the pass count is spent. After the last pass's fixes, obtain a review of the resulting head using the same activation rules. This final review consumes no pass and its findings do not block merge. Validate its findings as above; collect validated, relevant ones in one follow-up issue with links to their threads, then reply with the issue link and resolve those threads. The user can continue with `/ship-slice #<issue> <passes>`.

4. **Verify and merge.** Require green CI, the current head reviewed under the response criteria below, and all review threads resolved. Route any CI fixes through step 3, since a new head needs review. Check with `gh pr checks <n>` and the thread query in [thread operations](references/workflow-details.md#thread-operations). Merge with `gh pr merge <n> --merge --delete-branch --match-head-commit <sha>`, passing the head the review covered so GitHub refuses the merge if the PR moved since; use `--squash` if the repo prefers it.

5. **Close the work.** Check issue states after merge. Summarize delivery and its location on each issue, linking any follow-up issue. Close those still open, including umbrella and duplicate issues; comment on those GitHub already closed.

## Review activation

Use one normal activation per round. A recovery request after a timeout can overlap a slow review; use the commit requirement below so its late reaction cannot cover a newer head. Duplicate requests spend usage limits. Immediately before the activating event, capture `SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)`; keep it for every wait rerun in that round.

| Event | Activation |
| --- | --- |
| New PR opened for review | Creation activates round 1. |
| Draft PR | The authorized ready transition activates round 1. |
| Fix push under On every push or Smart detect | The push activates the round. Wait before considering a request. |
| Fix push under On PR open | Post the pinned request below after pushing. |
| All findings declined, with no fix commit to push | Post one pinned request containing the justifications. |
| Smart detect skipped a push, or a task summary arrived instead of a review | Post one pinned request. |
| Response names a stale commit | Re-request pinned to the current head. The intended round never happened. |

A pinned request uses a fresh `SINCE` and the verified remote head:

```bash
gh pr comment <n> --body "@codex review the latest fixes on commit <sha>: <fixes or substantive reasons for no code change>."
```

For declined findings, include the justification in an On PR open request; under On every push or Smart detect, keep it in the plain thread reply unless the all-declined row applies. Re-review a SHA with a completed, identifiable review only with a new substantive justification for a finding requiring no code change.

## Review response

Use `REQUIRE_COMMIT=0` for a new PR with one activation. On a resumed PR, use `REQUIRE_COMMIT=1` unless its history proves every earlier activation finished before the current one began. After any timeout or stale response, keep `REQUIRE_COMMIT=1` for the rest of the PR, including CI-fix waits. In this mode, reactions alone provide no head coverage; require a response or review summary naming the reviewed commit, or leave the PR open and hand off for commit verification.

Wait on `REQUIRE_COMMIT="$REQUIRE_COMMIT" scripts/wait-for-codex.sh <n> "$SINCE"` as one blocking wait: it polls GitHub itself and prints only when it exits, so its exit is the next thing you act on. In Claude Code, run it with `run_in_background`. In Codex, run it from one `exec` cell as in [blocking wait in Codex](references/workflow-details.md#blocking-wait-in-codex). Use its printed review, findings, comment ids, and reviewed commits.

| Exit | Action |
| --- | --- |
| 0: response | Confirm head coverage below, then address findings or accept a clean round. |
| 1: timeout | Enable the commit requirement before any retry or push. On PR open: activate the next round with a pinned request. On every push: rerun once, then hand off. Smart detect push round: request a pinned review; the automatic review may still be running. A timeout provides no clean-review evidence. |
| 2: pending | The review summary shows the head running, or a fresh 👀 remains. Rerun once, then handle a second exit 2 as exit 1. Use the same bound for directly observed 👀; its age does not prove an activation ended. |
| 3: unreadable repo/PR | Repair `gh` authentication or arguments, then rerun. |
| 4: notice | Report usage-limit or missing-environment notices, keep the PR open, and hand off until the cause clears. For a task summary, use the task-summary activation instead. |

Head coverage requires the waiter to list the current SHA among the reviewed commits, report the review summary's clean completion of it, or report a clean 👍 with `REQUIRE_COMMIT=0` for the head pushed or requested at `SINCE`. A 👍 names no commit; the waiter handles its attribution. A stale response enables the commit requirement before the stale-commit activation. Push a new head only after the current wait returns a response covering that head or a notice; a timeout does not resolve an activation.

Only a genuine response covering the intended head completes a pass; notices and tasks consume none. A clean round is Codex's `Didn't find any major issues` comment naming that SHA, the waiter's clean review summary for that SHA, or its clean 👍 with `REQUIRE_COMMIT=0`, regardless of fixes or declined findings. On a PR without a review summary, a later clean round may add no fresh 👍, since GitHub retains one reaction per user and type; use the timeout rules when that happens.

Before changing a Codex behavior claim, consult the documented sources in [references/README.md](references/README.md).
