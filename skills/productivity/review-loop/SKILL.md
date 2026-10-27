---
name: review-loop
description: Review the current change with a fresh reviewer in this harness, fix what holds up, and repeat until it approves. Local only, no PR.
argument-hint: "[base] [rounds]"
disable-model-invocation: true
license: MIT
---

# Review loop

The local version of ship-slice's review rounds. The reviewer is a subagent in the harness running this skill, not a GitHub bot or another provider's model. Nothing leaves the machine: do not push, open a PR, or comment on GitHub.

## 1. Pin the change

The base defaults to `git merge-base HEAD origin/HEAD`; rounds default to 3. State the intent and what is out of scope in one or two sentences each. Run the checks that cover the change and note any that were already failing. Record `git diff --shortstat <base>`.

## 2. Review

Spawn one read-only subagent with no conversation history, on your own model. Brief it with:

```
Review only. Do not edit files, commit, or start subagents.
Repo: <abs path>  Base: <sha>
Intent: <intent>  Out of scope: <scope>  Checks: <results>
Read `git diff <base>` and `git status --short`, including untracked files, and the code around the change.
Look for bugs, broken callers, and mismatches with the intent. Skip style unless it hides a bug.
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

Report the rounds, findings fixed, disputed, and declined, the follow-ups, and the diff size before and after. Leave the fixes uncommitted unless the user asked for a commit.
