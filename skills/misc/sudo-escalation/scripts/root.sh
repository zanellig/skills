#!/bin/sh
# Run a command as root via pkexec, then append one JSON line to the change log.
# Usage: root.sh <why> <undo|-> <cmd> [args...]
set -u
[ $# -ge 3 ] || { echo "usage: root.sh <why> <undo|-> <cmd> [args...]" >&2; exit 2; }
why=$1 undo=$2
shift 2

pkexec "$@"
rc=$?

if [ -n "${CODEX_THREAD_ID:-}" ]; then harness=codex session=$CODEX_THREAD_ID
elif [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then harness=claude session=$CLAUDE_CODE_SESSION_ID
else harness=unknown session=
fi

dir=${XDG_STATE_HOME:-$HOME/.local/state}/sudo-escalation
mkdir -p "$dir"
jq -nc --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg harness "$harness" --arg session "$session" \
  --arg cwd "$PWD" --argjson exit "$rc" --arg why "$why" --arg undo "$undo" '{
    ts: $ts, harness: $harness, session: (if $session == "" then null else $session end),
    cwd: $cwd, cmd: $ARGS.positional, exit: $exit, why: $why,
    undo: (if $undo == "-" or $undo == "" then null else $undo end)
  }' --args -- "$@" >> "$dir/log.jsonl"
exit "$rc"
