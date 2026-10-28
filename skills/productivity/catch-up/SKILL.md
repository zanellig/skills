---
name: catch-up
description: "Catch up on where work in this repo or directory stopped: finds the newest Claude Code and Codex sessions across all its worktrees, checks the live git and PR state, and ends with a continuation prompt. Use when the user asks where you left off, to check the last or latest session or thread (Claude or Codex), or to continue after a usage limit or a stopped session."
license: MIT
---

# Catch-up

Rebuild the state of interrupted work from session transcripts and the live repo, then hand the user a report and a continuation prompt. A catch-up is read-only: it reports and stops, and the user decides whether to resume.

## 1. Find the sessions

Run the bundled script from the working directory the user means (pass `--dir` for another one):

```sh
python3 -I <this skill's directory>/scripts/find_sessions.py
```

It lists the newest sessions per tool for the directory and every git worktree of its repo, newest first. Each entry has the last activity time, how it ended (agent replied, interrupted, hit a usage limit, waiting on the agent), delivery commands, PRs mentioned, the last user turns and the agent's last message. It already skips health-check pings, subagent transcripts and the calling session. `--limit N` widens the search; `--turns N` shows more user turns.

The **subject** is the session the user named (tool, title, or time), otherwise the newest listed one. Add any other session from the same day that worked on the same branch or PR. Done when you can name the subject sessions and what each was trying to do.

If the agent's last message doesn't say what remains, read the end of the subject transcript (the `transcript:` path) until it does.

## 2. Check the live state

Transcripts record claims; the repo records facts. For every branch, worktree and PR the subject sessions touched, check:

- `git status -sb` and `git log --oneline -5` in each worktree involved: uncommitted changes, commits not pushed, branch behind its base.
- `gh pr view <n> --json state,mergeable,reviewDecision,statusCheckRollup,url` for each PR mentioned: open, merged or closed, checks, unresolved review.
- Handoff files in `${TMPDIR:-/tmp}` newer than the session (`ls -t ${TMPDIR:-/tmp}/*handoff*`).

Where a transcript and the live state disagree, the live state wins; say so in the report. Done when every branch, worktree and PR from the subject sessions has a checked state.

## 3. Report

Use these four headings, in this order:

1. **Where things stand**: one short paragraph. What the work was, which session and tool did it, when it stopped and why.
2. **Last verified state**: facts from step 2, each with where it came from (live check or transcript).
3. **Unfinished**: the remaining steps in order, smallest first. Mark anything blocked on the user.
4. **Continuation prompt**: a fenced block the user can paste into a fresh session. It stands alone: repo path, branch or worktree, PR or issue, what is done, the next step, how to verify it, and the skills to use (for example `ship-slice` for a slice that still needs review rounds).

Then stop and let the user choose what to resume.
