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
# Exits 0 once Codex responds (printing findings), 1 on timeout, or 2 when a
# fresh eyes reaction shows that a review is still in flight after polling.
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

line_count() {
  awk 'NF { count++ } END { print count + 0 }'
}

comment_reactions() {
  local content="$1" id
  gh api --paginate "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.created_at >= \"$SINCE\") | .id" 2>/dev/null | while read -r id; do
      [ -n "$id" ] || continue
      gh api --paginate "repos/$REPO/issues/comments/$id/reactions" \
        --jq ".[] | select(.user.login==\"$BOT\" and .content==\"$content\" and .created_at > \"$SINCE\") | {content, created_at}" 2>/dev/null || true
    done
}

count_reactions() {
  local content="$1" matches pr_reactions comment_reaction_count
  matches=$(gh api --paginate "repos/$REPO/issues/$PR/reactions" \
    --jq ".[] | select(.user.login==\"$BOT\" and .content==\"$content\" and .created_at > \"$SINCE\") | .id" 2>/dev/null || true)
  pr_reactions=$(printf '%s\n' "$matches" | line_count)
  comment_reaction_count=$(comment_reactions "$content" | wc -l | tr -d ' ')
  echo $(( pr_reactions + comment_reaction_count ))
}

count_new() {
  local reviews comments inline reactions matches
  matches=$(gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
    --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | .id" 2>/dev/null || true)
  reviews=$(printf '%s\n' "$matches" | line_count)
  matches=$(gh api --paginate "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | .id" 2>/dev/null || true)
  comments=$(printf '%s\n' "$matches" | line_count)
  matches=$(gh api --paginate "repos/$REPO/pulls/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | .id" 2>/dev/null || true)
  inline=$(printf '%s\n' "$matches" | line_count)
  reactions=$(count_reactions "+1")
  echo $(( reviews + comments + inline + reactions ))
}

print_findings() {
  echo "=== Codex responded on $REPO#$PR (since $SINCE) ==="
  echo "--- Review summaries (state / body) ---"
  gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
    --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | {state, submitted_at, body}" 2>/dev/null || true
  echo "--- Inline findings (path:line) ---"
  gh api --paginate "repos/$REPO/pulls/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | {path, line, body}" 2>/dev/null || true
  echo "--- Issue comments ---"
  gh api --paginate "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | {created_at, body}" 2>/dev/null || true
  echo "--- Clean-review reactions ---"
  gh api --paginate "repos/$REPO/issues/$PR/reactions" \
    --jq ".[] | select(.user.login==\"$BOT\" and .content==\"+1\" and .created_at > \"$SINCE\") | {content, created_at}" 2>/dev/null || true
  comment_reactions "+1"
}

for _ in $(seq 1 "$POLLS"); do
  if [ "$(count_new)" -gt 0 ]; then
    print_findings
    exit 0
  fi
  sleep "$INTERVAL"
done

if [ "$(count_reactions "eyes")" -gt 0 ]; then
  echo "PENDING: Codex review is in flight on $REPO#$PR (since $SINCE)"
  exit 2
fi

echo "TIMEOUT: no Codex response on $REPO#$PR after $((POLLS * INTERVAL))s (since $SINCE)"
exit 1
