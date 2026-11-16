---
name: review-loop
description: Review the current change with a fresh reviewer, fix what holds up, and repeat until it approves.
argument-hint: "[rounds] [model...]"
disable-model-invocation: true
license: MIT
---

# Review loop

The local version of ship-slice's review rounds.

## 1. Pin the change

A leading number in the arguments sets the rounds, default 3. Any other arguments are models or the user's instructions. Unless the user names a base, run `git fetch origin` and take the first that resolves:

- An open PR for the branch: `git merge-base HEAD origin/<baseRefName>`, with `baseRefName` from `gh pr view --json baseRefName`.
- `git merge-base HEAD origin/HEAD`, or `origin/<default branch>` when `origin/HEAD` is unset.
- No remote: `HEAD`, which covers uncommitted changes only.

State the intent and what is out of scope in one or two sentences each. Run the checks that cover the change and fix what the change breaks before the first review; note any that were already failing. Record `git diff --shortstat <base>`.

## 2. Review

Spawn one read-only subagent with a fresh context. Use the first model the user names; each later round takes the next one, wrapping around the list. If they name none, use another provider's default model through the harness's delegation tool, so the reviewer doesn't share your blind spots. If the harness can't reach another provider, use your own model and say so in the final report.

Set the reviewer's reasoning effort explicitly, because the delegation default can be `low`. Use `high`, or `xhigh` for the final round and for security, concurrency, or large changes. `low` and `medium` read the diff without running any code, so their approval proves little; use them only when the user asks.

Brief it with:

```
You're the reviewer agent for this set of changes.
Make a read-only review. Do not edit files, commit, or start subagents.
Repo: <abs path>  Base: <sha>
Intent: <intent>  Out of scope: <scope>  Checks: <results>
Read `git diff <base>` and `git status --short`, including untracked files, and the code around the change.
Look for bugs, broken callers, security issues, performance regressions, and mismatches with the intent. Skip style unless it hides one of these.
Flag code, tests, or guards the intent does not need.
Grade each finding:
  blocker: the intended case is wrong
  should: a real bug callers will hit within the intent
  nit: everything else, including other paths, rare cases, and small costs
Reply:
VERDICT: APPROVE or CHANGES
R1 [blocker|should|nit] <file>:<line> <claim>. Fix: <suggestion>
```

Keep the ids stable across rounds. Do not edit the change while the reviewer runs.

## 3. Answer the findings

Check each finding against the code yourself and regrade it; a label from the reviewer is a claim. Then:

- **Blocker or should you agree with**: make the smallest fix. Prefer deleting or narrowing code over a new guard, cache, helper, or option.
- **Disagree**: write why, with evidence (`file:line`, a test, command output).
- **Nit or out of scope**: decline in one line and list it as a follow-up.

Rerun the checks and `git diff --shortstat <base>`. If review grew the diff, cut first. Keep a ledger of each id as fixed, disputed, or declined.

## 4. Next round

Run another round while rounds remain and a blocker or should is open, or a fix changed behavior since the last approval. Spawn a fresh reviewer with the same brief, plus the ledger and the change since the last round, and ask it to mark each old id resolved or still open, and to review only open ids and changed code.

## 5. Stop

Stop when step 4 calls for no further round: no blocker or should is open after your regrading and the reviewer has seen every behavior change, or the rounds ran out. A `CHANGES` verdict holding only declined nits ends here too. An item still disputed after two replies goes to the user, with each side in two or three lines. Running out of rounds is not approval.

Report the rounds, findings fixed, disputed, and declined, the follow-ups, and the diff size before and after.
