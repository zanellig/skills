---
name: ship-slice
description: Drive a slice from implementation through Codex review rounds to a merged PR. Use when implementing a slice/issue that must pass @codex review before merge, when the user says "ship", "work the slice", "get this through review", or when addressing Codex review findings on a PR.
argument-hint: "slice issue number or handoff path"
---

# Ship Slice

The implement -> `@codex` review -> merge loop for a vertical slice. A **slice** is a thin,
end-to-end piece of a larger spec/PRD that ships on its own. Reviews come from the GitHub bot `chatgpt-codex-connector[bot]` (shows as `chatgpt-codex-connector` in `gh pr view` JSON).

## Process

1. **Load the work.** Read the slice issue (`gh issue view <n>`) and its parent spec/PRD. If handed a handoff doc path, read that first. Confirm acceptance criteria before touching code.

2. **Implement to acceptance criteria, with tests.** Every behavior change gets a test. Run the project's test/check suite and make it green. Format before committing.

3. **Commit and push.** Commit by scope with clear messages. After pushing, confirm the remote head actually moved — `git rev-parse HEAD` should equal `git rev-parse @{u}`. (Some git wrappers silently drop pushes; Codex reviews whatever is really on the remote.)

4. **Open the PR.** Title `Slice <id>: <summary>`. Body references the parent spec and the issues it closes. Draft PRs are fine; mark ready before requesting review: `gh pr ready <n>`.

5. **Request review.** `gh pr comment <n> --body "@codex review"`. For re-requests, always pin the commit: `... --body "@codex review the latest fixes on commit <sha>: <what each finding's fix did>, each with a regression test (<N> tests green)."` Codex reviews the commit as of request time, so an unpinned re-request can review a stale commit.

6. **Wait for the response** (background command — it sleeps): `scripts/wait-for-codex.sh <n>` prints the review body, inline findings (path:line), and issue comments once Codex responds. Exits 0 on response, 1 on timeout. Capture `SINCE` yourself and pass it if you want to avoid the default 2-minute lookback: `wait-for-codex.sh <n> "$SINCE"`.

7. **Address every finding.** Fix each one and add a regression test per finding. Do not hand-wave a finding away without either a code change or a written justification in the re-request comment.

8. **Loop** until a round returns zero new actionable findings (a review that approves or says no issues) or **three** review passes were completed. Then continue.

9. **CI green.** `gh pr checks <n>`. Fix reds and re-push before merging.

10. **Merge.** `gh pr merge <n> --merge --delete-branch` (swap `--squash` if the repo prefers it).

11. **Close issues.** Close the slice issue and any umbrella/duplicate issues with a comment summarizing what was delivered and where (`gh issue close <n> --comment "..."`).

## Notes

- Run `wait-for-codex.sh` as a background command; its `sleep` loop would otherwise block the turn.
- Codex may answer as a PR review, a PR issue-comment, OR inline PR comments — the script checks all three. Filter by `user.login == "chatgpt-codex-connector[bot]"` and a `SINCE` timestamp.
- Requires the GitHub CLI (`gh`) authenticated for the repo, with the Codex GitHub app installed.
