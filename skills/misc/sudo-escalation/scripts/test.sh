#!/bin/sh
# Check root.sh against a stub pkexec and a temporary state dir. Never calls the real pkexec.
set -eu
root=$(dirname "$0")/root.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/bin"
# shellcheck disable=SC2016 # the stub's $1 must stay literal
printf '#!/bin/sh\ntouch "$XDG_STATE_HOME.ran"\n[ "$1" = false ] && exit 3\nexit 0\n' > "$tmp/bin/pkexec"
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

# The log is private: 700 dir, 600 file, even under umask 022 and for an existing 644 log.
[ "$(stat -c %a "$tmp/state/sudo-escalation")" = 700 ]
[ "$(stat -c %a "$log")" = 600 ]
chmod 755 "$tmp/state/sudo-escalation"; chmod 644 "$log"
(umask 022; sh "$root" "again" "-" true)
[ "$(stat -c %a "$tmp/state/sudo-escalation")" = 700 ]
[ "$(stat -c %a "$log")" = 600 ]

# Nothing runs as root when the log can't be written: unwritable state dir, or no jq.
touch "$tmp/file"
XDG_STATE_HOME="$tmp/file" sh "$root" "x" "-" true 2> /dev/null && exit 1
[ ! -e "$tmp/file.ran" ]
mkdir "$tmp/nojq"
for t in sh date mkdir chmod touch flock; do ln -s "$(command -v "$t")" "$tmp/nojq/$t"; done
ln -s "$tmp/bin/pkexec" "$tmp/nojq/pkexec"
XDG_STATE_HOME="$tmp/nojq-state" PATH="$tmp/nojq" sh "$root" "x" "-" true 2> /dev/null && exit 1
[ ! -e "$tmp/nojq-state.ran" ]

# Concurrent writers with long arguments never interleave records.
long=$(head -c 100000 /dev/zero | tr '\0' x)
export XDG_STATE_HOME="$tmp/conc"
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sh "$root" "w$i" "-" echo "$long" & done
wait
[ "$(jq -c . "$tmp/conc/sudo-escalation/log.jsonl" | wc -l)" -eq 20 ]
echo ok
