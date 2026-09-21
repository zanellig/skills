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

3. **Commit and push.** Commit by scope with conventional-commit messages. Push with an **explicit remote and branch** — `git push origin <branch>`. A *bare* `git push` whose output is piped (e.g. `git push 2>&1 | tail`) can be swallowed by a shell wrapper: no output, exit 0, nothing on the remote. After any push that matters, verify it landed: `git ls-remote origin refs/heads/<branch>` must equal `git rev-parse HEAD`.

4. **Confirm the review trigger.** Codex activates reviews on one of three settings, set per account and overridable per repo: **On PR open**, **On every push**, or **Smart detect**. Which one is in force decides whether step 9 ever posts `@codex review`, and no API exposes it. When the repo's agents file already records it, use that. Otherwise ask the user, then write one line under a `Codex Code review settings` heading in `AGENTS.md` — or `CLAUDE.md` when the repo has no `AGENTS.md` — and tell the user you added it. Say nothing when it was already recorded. Nest the heading one level below an existing code-review section, otherwise add it at `##`:

   ```markdown
   ## Codex Code review settings

   Review trigger: Smart detect. A push activates the next round on its own; `@codex review` is for **On PR open** only.
   ```

5. **Open the PR.** Immediately before running `gh pr create`, capture `SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)`. Title it `Slice <id>: <summary>`. The body references the parent spec and the issues it closes. If an applicable policy opens the PR as a draft, creation does not activate review; capture a new `SINCE` immediately before the authorized transition to ready.

6. **Treat PR creation as round 1.** Opening the PR activates the initial review. Do not also comment `@codex review`; that activates a second review of the same commit and can return duplicate findings. If the PR already existed when this process began, inspect existing Codex activity and resume from the latest round for the current remote head. If no response exists yet, capture a timestamp that precedes the pending review activity and wait for its response without requesting another review.

7. **Wait for the response** (background command — it sleeps): `scripts/wait-for-codex.sh <n> "$SINCE"` prints the commits Codex read, the review body, inline findings (path:line), issue comments, and any clean-review 👍. Act on the exit code, and keep the same `SINCE` for every rerun within a round:

   | Exit | Meaning | Do |
   | --- | --- | --- |
   | 0 | A genuine response arrived. | Go to step 8. |
   | 1 | Timeout. A timeout is never zero findings. | Under **On PR open**, activate the next round (step 9). Under the other triggers the push already activated it, so rerun once, then hand off. |
   | 2 | A fresh 👀 means the review is in flight. | Rerun once. A second exit 2 means the reaction is stale, because the bot keeps it after a review finishes; treat that as exit 1. |
   | 3 | The repo or PR could not be read. | Repair `gh` auth or the arguments, then rerun. |
   | 4 | Codex posted a **notice** instead of a review (usage limit, missing environment). | Stop. Report the notice and hand off. |

   A notice means the round never ran, so the commit carries no review and the PR stays open. Requesting again reproduces the notice until the underlying limit clears.

8. **Address every finding, in its own thread.** Fix each actionable finding. Add or update tests when the finding changes observable behavior or exposes a meaningful regression risk; add a regression test where it earns its place, not once per finding. Answer each finding where it was raised — `gh api repos/<owner>/<repo>/pulls/<n>/comments/<id>/replies -f body="Fixed in <sha>: <what changed>"` — naming the fix commit, or the substantive reason the finding requires no code change. Then resolve the thread with the GraphQL `resolveReviewThread` mutation on its thread id — the step 10 query returns those ids alongside `isResolved`. **The bot reads a reply only when it is @-mentioned.** A plain reply is for the human record and for step 10's gate; `@codex` in the body summons an answer in-thread and spends a review against your usage limits. So fixes go in plain replies, and a finding you are declining to change gets its justification in front of Codex — either `@codex` in the thread, or the next review request in step 9.

9. **Loop.** Capture `AUTO_SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)`, then push fixes and verify the remote SHA as in step 3. Under **On every push** and **Smart detect** the push itself activates the round, so wait it out with the waiter from `AUTO_SINCE` (step 7); posting `@codex review` there spawns a second review session against your usage limits. Only **On PR open** leaves the round unactivated after the first review. To activate one, capture `SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)` and post one pinned comment: `gh pr comment <n> --body "@codex review the latest fixes on commit <sha>: <what each finding's fix did or why no code change is appropriate>."` Codex reviews the commit as of request time, so always pin the SHA. The same SHA may be reviewed again only when the new request contains a substantive justification for a finding that requires no code change. Stop when a round returns zero new actionable findings or three rounds have completed. Only a genuine Codex response completes a round. PR creation is round 1.

   **Check which commit was reviewed.** The waiter prints the commits Codex read. When one differs from the SHA you pushed, Codex reviewed a stale commit and that round covered none of your fixes: re-request with the SHA pinned. That re-request answers a round that never happened, so it is not a duplicate activation.

10. **CI green, threads closed.** `gh pr checks <n>`. Fix reds and re-push. Then confirm every Codex review thread is resolved, so the merge carries a fix or an answer for each finding:

   ```bash
   gh api graphql --paginate \
     -f query='query($o:String!,$r:String!,$n:Int!,$endCursor:String){repository(owner:$o,name:$r){pullRequest(number:$n){
       reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{id isResolved path}}}}}' \
     -f o=<owner> -f r=<repo> -F n=<n> \
     --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false) | "\(.id) \(.path)"'
   ```

11. **Merge.** `gh pr merge <n> --merge --delete-branch` (swap `--squash` if the repo prefers it).

12. **Close issues.** Close the slice issue and any umbrella/duplicate issues with a comment summarizing what was delivered and where (`gh issue close <n> --comment "..."`).

## Notes

- **One activation per round:** Opening the PR activates round 1. Each later round is activated by the push under **On every push** and **Smart detect**, and by one `@codex review` comment under **On PR open**. A fresh 👀 reaction means a round is already running, whether the waiter reports it (exit 2) or you spot it in `gh pr view`; let it resolve into a review, comment, or 👍. The bot leaves the reaction in place afterwards, so an 👀 that outlives a full wait is stale rather than pending — step 7 bounds how long to believe it. A second request re-reviews the same commit and burns usage limits on duplicate findings.
- Run `wait-for-codex.sh` as a background command; its `sleep` loop would otherwise block the turn.
- Codex may answer as a PR review, inline PR comments, an issue comment, or a 👍 reaction on the PR — the script checks those four. Filter by `user.login == "chatgpt-codex-connector[bot]"` and a `SINCE` timestamp. **Every genuine response names the commit it read** (`Reviewed commit: <sha>`); a bot comment without that marker is a notice.
- A 👍 lands on the PR itself, and GitHub keeps one reaction of each type per user, so a later clean round cannot always be seen there. The `Reviewed commit:` comment is the reliable clean-round signal.
- Requires the GitHub CLI (`gh`) authenticated for the repo, with the Codex GitHub app installed.
