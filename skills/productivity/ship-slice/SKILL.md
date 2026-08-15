---
name: ship-slice
description: Drive a slice from implementation through Codex review rounds to a merged PR. Use when implementing a slice/issue that must pass @codex review before merge, when the user says "ship", "work the slice", "get this through review", or when addressing Codex review findings on a PR.
argument-hint: "slice issue number or handoff path"
disable-model-invocation: true
---

# Ship Slice

The implement -> Codex review -> fixes -> follow-up review -> merge loop for a vertical slice. A **slice** is a thin,
end-to-end piece of a larger spec/PRD that ships on its own. Reviews come from the GitHub bot `chatgpt-codex-connector[bot]` (shows as `chatgpt-codex-connector` in `gh pr view` JSON).

## Process

1. **Load the work.** Read the slice issue (`gh issue view <n>`) and its parent spec/PRD. If handed a handoff doc path, read that first. Confirm acceptance criteria before touching code.

2. **Implement to acceptance criteria, with tests.** Every behavior change gets a test. Run the project's test/check suite and make it green. Format before committing.

3. **Commit and push.** Commit by scope with conventional-commit messages. Push with an **explicit remote and branch** — `git push origin <branch>`. A *bare* `git push` whose output is piped (e.g. `git push 2>&1 | tail`) is silently dropped by the rtk layer — no output, exit 0 — even without typing the `rtk` prefix (verified 2026-07-20; it cost PR #43 two commits). After any push that matters, verify it landed: `git ls-remote origin refs/heads/<branch>` must equal `git rev-parse HEAD`.

4. **Open the PR as a draft.** Use `gh pr create --draft`. Title `Slice <id>: <summary>`. Body references the parent spec and the issues it closes. Codex ignores draft PRs — do not request review while the PR is a draft.

5. **Activate round 1 by marking ready.** After the last implementation commit is pushed and verified, capture `SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)`, then run `gh pr ready <n>`. The Draft -> Ready transition is the review request. Do not also comment `@codex review`; that activates a second review of the same commit and can return duplicate findings. If the PR was already ready when this process began, do not activate another review. Inspect existing Codex activity and resume from the latest round for the current remote head. If no response exists yet, capture `SINCE` and wait for the pending response.

6. **Wait for the response** (background command — it sleeps): `scripts/wait-for-codex.sh <n> "$SINCE"` prints the review body, inline findings (path:line), and issue comments once Codex responds. Exits 0 on response, 1 on timeout. A timeout means no answer yet, never zero findings: re-run the waiter with the same `SINCE`; do not recapture the timestamp or request another review.

7. **Address every finding.** Fix each actionable finding. Add or update tests when the finding changes observable behavior or exposes a meaningful regression risk; do not add a regression test mechanically for every finding. A finding that appropriately requires no code change needs a substantive written justification in the next review request.

8. **Loop.** Push fixes and verify the remote SHA as in step 3. Immediately before activating the next round, capture `SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)`, then post one pinned comment: `gh pr comment <n> --body "@codex review the latest fixes on commit <sha>: <what each finding's fix did or why no code change is appropriate>."` Codex reviews the commit as of request time, so always pin the SHA. Do not duplicate a pending request. The same SHA may be reviewed again only when the new request contains a substantive justification for a finding that requires no code change. Stop when a round returns zero new actionable findings or three rounds have completed. Only a received Codex response completes a round; a timeout does not. The ready-for-review round is round 1.

9. **CI green.** `gh pr checks <n>`. Fix reds and re-push before merging.

10. **Merge.** `gh pr merge <n> --merge --delete-branch` (swap `--squash` if the repo prefers it).

11. **Close issues.** Close the slice issue and any umbrella/duplicate issues with a comment summarizing what was delivered and where (`gh issue close <n> --comment "..."`).

## Notes

- **One activation per round:** Draft -> Ready activates round 1; one `@codex review` comment activates each later round. Never use both for the same round.
- Run `wait-for-codex.sh` as a background command; its `sleep` loop would otherwise block the turn.
- Codex may answer as a PR review, a PR issue-comment, OR inline PR comments — the script checks all three. Filter by `user.login == "chatgpt-codex-connector[bot]"` and a `SINCE` timestamp.
- Requires the GitHub CLI (`gh`) authenticated for the repo, with the Codex GitHub app installed.
