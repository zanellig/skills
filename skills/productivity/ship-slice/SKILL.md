---
name: ship-slice
description: Drive a slice from implementation through Codex review rounds to a merged PR. Use when implementing a slice/issue that must pass @codex review before merge, when the user says "ship", "work the slice", "get this through review", or when addressing Codex review findings on a PR.
argument-hint: "slice issue number or handoff path"
disable-model-invocation: true
---

# Ship Slice

The loop that carries a vertical slice from implementation through Codex review, fixes, and a follow-up review to a merged PR. A **slice** is a thin, end-to-end piece of a larger spec or PRD that ships on its own. Reviews come from the GitHub bot `chatgpt-codex-connector[bot]`, which shows as `chatgpt-codex-connector` in `gh pr view` JSON.

## Process

1. **Load the work.** Read the slice issue (`gh issue view <n>`) and its parent spec or PRD. If handed a handoff doc path, read that first. Confirm acceptance criteria before touching code.

2. **Implement to acceptance criteria, with tests.** Every behavior change gets a test. Run the project's test/check suite and make it green. Format before committing.

3. **Commit and push.** Commit by scope with conventional-commit messages. Push with an explicit remote and branch, `git push origin <branch>`. After any push that matters, verify it landed: `git ls-remote origin refs/heads/<branch>` must equal `git rev-parse HEAD`.

4. **Open the PR.** Immediately before running `gh pr create`, capture `SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)`. Title it `Slice <id>: <summary>`. The body references the parent spec and the issues it closes. If a policy opens the PR as a draft, creation does not activate review. Capture a new `SINCE` immediately before the authorized transition to ready.

5. **Treat PR creation as round 1.** Opening the PR activates the initial review. Do not also comment `@codex review`; that activates a second review of the same commit and can return duplicate findings. If the PR already existed when this process began, inspect existing Codex activity and resume from the latest round for the current remote head. If no response exists yet, capture a timestamp that precedes the pending review activity, then wait for its response without requesting another review.

6. **Wait for the response.** Run this as a background command, because it sleeps. `scripts/wait-for-codex.sh <n> "$SINCE"` prints the review body, inline findings (path:line), issue comments, or a clean-review `+1` reaction once Codex responds. It exits 0 on a response, 1 when no response or pending signal appeared, and 2 when a fresh `eyes` reaction shows a review is still in flight. A timeout is never zero findings. On exit 2, rerun the waiter with the same `SINCE`. Reuse that timestamp rather than capturing a new one, and wait for the pending review instead of requesting another.

7. **Address every finding.** Fix each actionable finding. Add or update tests when the finding changes observable behavior or exposes a meaningful regression risk. A finding that needs no code change needs a substantive written justification in the next review request.

8. **Loop.** Capture `AUTO_SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)`, then push fixes and verify the remote SHA as in step 3. Smart Trigger may or may not review new commits on its own, so run a bounded waiter from `AUTO_SINCE` before activating the next round by hand. A response completes the round. Exit 2 means an automatic review is pending, so rerun with the same timestamp. On exit 1, capture `SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)` and post one pinned comment: `gh pr comment <n> --body "@codex review the latest fixes on commit <sha>: <what each finding's fix did or why no code change is appropriate>."` Codex reviews the commit as of request time, so always pin the SHA. Request a re-review of the same SHA only when the new request carries a substantive justification for a finding that needs no code change. Stop when a round returns zero new actionable findings, or when three rounds have completed. Only a received Codex response completes a round, including a clean-review `+1` reaction. PR creation is round 1.

9. **CI green.** `gh pr checks <n>`. Fix reds and re-push before merging.

10. **Merge.** `gh pr merge <n> --merge --delete-branch` (swap `--squash` if the repo prefers it).

11. **Close issues.** Close the slice issue and any umbrella or duplicate issues with a comment summarizing what was delivered and where (`gh issue close <n> --comment "..."`).

## Notes

- **One activation per round.** Opening the PR activates round 1, and one `@codex review` comment activates each later round. A round stays pending while the bot's `eyes` reaction stands, whether the waiter reports it (exit 2) or you spot it in `gh pr view`. Wait for that reaction to resolve into a review, a comment, or a `+1`. A second request re-reviews the same commit and burns usage limits on duplicate findings.
- Run `wait-for-codex.sh` as a background command. Its `sleep` loop would otherwise block the turn.
- Codex may answer as a PR review, a PR issue-comment, inline PR comments, or a `+1` reaction on the PR or on the review-request comment. The script checks all five. Filter by `user.login == "chatgpt-codex-connector[bot]"` and a `SINCE` timestamp.
- Requires the GitHub CLI (`gh`) authenticated for the repo, with the Codex GitHub app installed.
