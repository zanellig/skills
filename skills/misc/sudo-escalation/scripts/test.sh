#!/bin/sh
# Check root.sh against a stub pkexec and a temporary state dir. Never calls the real pkexec.
set -eu
root=$(dirname "$0")/root.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/bin"
# shellcheck disable=SC2016 # the stub's $1 must stay literal
printf '#!/bin/sh\n[ "$1" = false ] && exit 3\nexit 0\n' > "$tmp/bin/pkexec"
chmod +x "$tmp/bin/pkexec"
export PATH="$tmp/bin:$PATH" XDG_STATE_HOME="$tmp/state"
unset CODEX_THREAD_ID CLAUDE_CODE_SESSION_ID
CLAUDE_CODE_SESSION_ID=abc sh "$root" "update" "-" pacman -Syu --noconfirm
sh "$root" "fails" "undo it" false || [ $? -eq 3 ]
log=$tmp/state/sudo-escalation/log.jsonl
[ "$(wc -l < "$log")" -eq 2 ]
jq -e -s '.[0] | .harness == "claude" and .session == "abc" and .exit == 0 and .undo == null
  and .cmd == ["pacman","-Syu","--noconfirm"] and .why == "update"' "$log" > /dev/null
jq -e -s '.[1] | .harness == "unknown" and .session == null and .exit == 3 and .undo == "undo it"' "$log" > /dev/null
echo ok
