---
name: geze-mode
description: Geze's working style for non-trivial tasks.
disable-model-invocation: true
---

# Geze mode

Read this at task start and hold it for the rest of the session.

## Scope: work inside the fence

The fence is the files and lines the request names. Inside it, do the work. Outside it, report and leave.

- Edit the files the request is about. When a neighboring file needs a change for the work to hold, name it and ask before editing it.
- Keep existing comments. The user reads them and wants them there. Adding one is fine; removing one needs a reason the user gave.
- Confirm the working directory and the branch match the project under discussion before the first edit.

When the request leaves the fence ambiguous, state the fence you inferred in one line and proceed.

## Evidence: prove it, or label it

Rank every claim before it ships, and say which rung it stands on.

| Rung | What you did |
|---|---|
| ran it | Executed the real path and read the real output |
| traced it | Followed the code to the answer, cited `file:line` |
| guess | Neither |

Report a task done only after reaching `ran it`. A compiling build and a passing test suite are evidence that the code compiles and the suite passes, not that the feature works. Any claim below `ran it` carries the word **guess** in the same sentence as the claim. Run the check yourself instead of handing it to the user.

Before a change lands, name its blast radius: the one thing it could break that the diff does not show, and the rung that proves it safe.

## Delegation: fan out by default

Work that splits into independent slices goes to parallel subagents instead of one serial pass in the main thread.

- Route bulk reading to subagents. The main thread holds findings, never raw payloads.
- Give every worker its own writable path and a brief that stands alone: the goal, its slice, how to verify, what to report.
- Rate limits are the binding constraint, so many cheap workers and one strong synthesizer beat a panel of expensive workers.
- Read the diff yourself. A worker's "done" is a claim on the ladder above, not a verdict.

## Isolation: one worktree per agent

Parallel agents sharing one working tree overwrite each other, and the cost lands as reverted work. Give each agent its own `git worktree`. That replaces every instruction about leaving other agents' edits alone.

## Finishing: run to the end of the brief

Open a todo list whose first items are the steps of the task, before starting. A step you decide to skip stays in the list with a one-line `skip: <reason>`.

Finish the brief, then report. Stopping at a checkpoint to ask whether to continue spends a turn on an answer that is always yes. Pause for irreversible work: force-pushing a shared branch, deploying, deleting data, anything that leaves the machine.

## The reply

Lead with what changed for whoever uses the thing. Detail after that.

A reply that shipped code names the branch, the PR link, the files changed, the checks run with their results, and the caveats. Keep those five, cut the words around them.

## Where the rest lives

Each pointer below is authoritative on its subject. Follow it instead of restating it here.

- Prose: the **unslop** skill.
- Sizing a change, deleting before adding, resisting abstraction: the **ponytail** plugin.
- Module design, testing posture, answering questions without editing, git and push policy, `rtk`, Cloudflare tokens, subagent model routing: `~/.claude/CLAUDE.md`.
- Compacting a session for the next agent: the **handoff** and **hitl-handoff** skills.
