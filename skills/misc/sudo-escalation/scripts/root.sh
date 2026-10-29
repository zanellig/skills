#!/bin/sh
# Run a command as root via pkexec, then append one JSON line to the change log.
# Usage: root.sh <why> <undo|-> <cmd> [args...]
set -u
[ $# -ge 3 ] || { echo "usage: root.sh <why> <undo|-> <cmd> [args...]" >&2; exit 2; }
why=$1 undo=$2
shift 2

# Check the log is writable before anything runs as root. Private: commands may carry secrets.
dir=${XDG_STATE_HOME:-$HOME/.local/state}/sudo-escalation
log=$dir/log.jsonl
umask 077
if ! command -v jq > /dev/null || ! command -v flock > /dev/null \
  || ! mkdir -p "$dir" || ! chmod 700 "$dir" || ! touch "$log" || ! chmod 600 "$log"; then
  echo "root.sh: cannot write $log (needs jq, flock); nothing ran" >&2
  exit 1
fi

pkexec "$@"
rc=$?

if [ -n "${CODEX_THREAD_ID:-}" ]; then harness=codex session=$CODEX_THREAD_ID
elif [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then harness=claude session=$CLAUDE_CODE_SESSION_ID
else harness=unknown session=
fi

rec=$(jq -nc --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg harness "$harness" --arg session "$session" \
  --arg cwd "$PWD" --argjson exit "$rc" --arg why "$why" --arg undo "$undo" '{
    ts: $ts, harness: $harness, session: (if $session == "" then null else $session end),
    cwd: $cwd, cmd: $ARGS.positional, exit: $exit, why: $why,
    undo: (if $undo == "-" or $undo == "" then null else $undo end)
  }' --args -- "$@") \
  && { flock 9 && printf '%s\n' "$rec" >&9; } 9>> "$log" \
  || echo "root.sh: the command ran (exit $rc) but was not logged; do not rerun it" >&2
exit "$rc"
