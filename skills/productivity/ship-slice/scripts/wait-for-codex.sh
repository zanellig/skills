#!/usr/bin/env bash
# wait-for-codex.sh — poll a PR for a fresh Codex review response, then print it.
#
# Usage: wait-for-codex.sh <pr> [since_iso] [owner/repo]
#   <pr>        PR number.
#   [since_iso] Only count responses newer than this UTC ISO timestamp.
#               Default: 2 minutes ago (buffers against a race with your request).
#   [owner/repo] Default: current repo via `gh repo view`.
#
# Env: POLLS (default 30 iterations), INTERVAL (default 60s between polls).
# Exits 0 once Codex responds (printing findings), 1 on timeout.
#
# Run this as a BACKGROUND command — it sleeps between polls.
set -euo pipefail

PR="${1:?usage: wait-for-codex.sh <pr> [since_iso] [owner/repo]}"
SINCE="${2:-$(date -u -d '-2 minutes' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
  || date -u -v-2M +%Y-%m-%dT%H:%M:%SZ)}"
REPO="${3:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
BOT="chatgpt-codex-connector[bot]"
POLLS="${POLLS:-30}"
INTERVAL="${INTERVAL:-60}"

count_new() {
  local reviews comments inline
  reviews=$(gh api "repos/$REPO/pulls/$PR/reviews" \
    --jq "[.[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\")] | length" 2>/dev/null || echo 0)
  comments=$(gh api "repos/$REPO/issues/$PR/comments" \
    --jq "[.[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\")] | length" 2>/dev/null || echo 0)
  inline=$(gh api "repos/$REPO/pulls/$PR/comments" \
    --jq "[.[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\")] | length" 2>/dev/null || echo 0)
  echo $(( reviews + comments + inline ))
}

print_findings() {
  echo "=== Codex responded on $REPO#$PR (since $SINCE) ==="
  echo "--- Review summaries (state / body) ---"
  gh api "repos/$REPO/pulls/$PR/reviews" \
    --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | {state, submitted_at, body}" 2>/dev/null || true
  echo "--- Inline findings (path:line) ---"
  gh api "repos/$REPO/pulls/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | {path, line, body}" 2>/dev/null || true
  echo "--- Issue comments ---"
  gh api "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | {created_at, body}" 2>/dev/null || true
}

for _ in $(seq 1 "$POLLS"); do
  if [ "$(count_new)" -gt 0 ]; then
    print_findings
    exit 0
  fi
  sleep "$INTERVAL"
done

echo "TIMEOUT: no Codex response on $REPO#$PR after $((POLLS * INTERVAL))s (since $SINCE)"
exit 1
