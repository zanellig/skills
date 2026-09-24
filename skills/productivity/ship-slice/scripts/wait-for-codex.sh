#!/usr/bin/env bash
# wait-for-codex.sh — poll a PR for a fresh Codex review response, then print it.
#
# Usage: wait-for-codex.sh <pr> [since_iso] [owner/repo]
#   <pr>        PR number.
#   [since_iso] Only count responses newer than this UTC ISO timestamp.
#               Default: 2 minutes ago (buffers against a race with your request).
#   [owner/repo] Default: current repo via `gh repo view`.
#
# Env: POLLS (default 30 sleeps), INTERVAL (default 60s per sleep).
# Exits 0 once Codex responds (printing the commits it read and the findings),
# 1 on timeout, 2 when a fresh eyes reaction shows a review still in flight,
# 3 when the repo or PR cannot be read, and 4 when Codex posted a notice
# instead of a review, which means the round never ran.
#
# Run this as a BACKGROUND command — it sleeps between polls.
set -euo pipefail

PR="${1:?usage: wait-for-codex.sh <pr> [since_iso] [owner/repo]}"
SINCE="${2:-$(date -u -d '-2 minutes' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
  || date -u -v-2M +%Y-%m-%dT%H:%M:%SZ)}"
if ! REPO="${3:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"; then
  echo "ERROR: cannot resolve the repo. Run inside it or pass owner/repo." >&2
  exit 3
fi
gh api "repos/$REPO/pulls/$PR" --jq .number >/dev/null 2>&1 || {
  echo "ERROR: cannot read $REPO#$PR. Check gh auth and the PR number." >&2
  exit 3
}
BOT="chatgpt-codex-connector[bot]"
POLLS="${POLLS:-30}"
INTERVAL="${INTERVAL:-60}"

line_count() {
  awk 'NF { count++ } END { print count + 0 }'
}

# Every genuine Codex response names the commit it read. A bot issue comment
# without that marker is a notice (usage limit, missing environment), not a
# review. $1 selects which of the two to return, $2 the field to emit.
bot_comments() {
  gh api --paginate "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\"
           and ((.body | test(\"Reviewed commit\")) == $1)) | .$2" 2>/dev/null || true
}

count_reactions() {
  local matches
  matches=$(gh api --paginate "repos/$REPO/issues/$PR/reactions" \
    --jq ".[] | select(.user.login==\"$BOT\" and .content==\"$1\" and .created_at > \"$SINCE\") | .id" \
    2>/dev/null || true)
  printf '%s\n' "$matches" | line_count
}

# The bot acknowledges a round with an eyes reaction on the PR, or on the
# comment that activated it. Only a comment from this round can carry one, so
# the scan starts at SINCE rather than walking the PR's whole history. Runs
# once after the wait expires, so the per comment lookup costs nothing during
# polling.
pending_on_comments() {
  local ids id
  ids=$(gh api --paginate "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.created_at >= \"$SINCE\") | .id" 2>/dev/null || true)
  for id in $ids; do
    gh api --paginate "repos/$REPO/issues/comments/$id/reactions" \
      --jq ".[] | select(.user.login==\"$BOT\" and .content==\"eyes\" and .created_at > \"$SINCE\") | .id" \
      2>/dev/null || true
  done
}

count_new() {
  local reviews comments inline matches
  matches=$(gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
    --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | .id" 2>/dev/null || true)
  reviews=$(printf '%s\n' "$matches" | line_count)
  matches=$(bot_comments true id)
  comments=$(printf '%s\n' "$matches" | line_count)
  matches=$(gh api --paginate "repos/$REPO/pulls/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | .id" 2>/dev/null || true)
  inline=$(printf '%s\n' "$matches" | line_count)
  echo $(( reviews + comments + inline ))
}

print_findings() {
  echo "=== Codex responded on $REPO#$PR (since $SINCE) ==="
  echo "--- Commits Codex read (compare against the SHA you pushed) ---"
  {
    gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
      --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | .commit_id" 2>/dev/null || true
    gh api --paginate "repos/$REPO/pulls/$PR/comments" \
      --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | .commit_id" 2>/dev/null || true
    bot_comments true body | { grep -io 'reviewed commit.*' || true; }
  } | sort -u
  echo "--- Review summaries (state / body) ---"
  gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
    --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | {state, submitted_at, body}" 2>/dev/null || true
  echo "--- Inline findings (id, path:line) ---"
  gh api --paginate "repos/$REPO/pulls/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | {id, path, line, body}" 2>/dev/null || true
  echo "--- Issue comments ---"
  bot_comments true body
  echo "--- Clean-review reactions ---"
  gh api --paginate "repos/$REPO/issues/$PR/reactions" \
    --jq ".[] | select(.user.login==\"$BOT\" and .content==\"+1\" and .created_at > \"$SINCE\") | {content, created_at}" 2>/dev/null || true
}

# Sleep before every check but the first, so a response that lands during the
# last sleep still gets classified.
for i in $(seq 0 "$POLLS"); do
  [ "$i" -eq 0 ] || sleep "$INTERVAL"
  if [ "$(count_new)" -gt 0 ]; then
    print_findings
    exit 0
  fi
  notice=$(bot_comments false body)
  if [ -n "$notice" ]; then
    echo "BLOCKED: Codex posted a notice instead of a review on $REPO#$PR (since $SINCE)"
    printf '%s\n' "$notice"
    exit 4
  fi
done

# A thumbs-up names no commit, so it only ends the round once the wait expires
# without a response that does.
if [ "$(count_reactions "+1")" -gt 0 ]; then
  print_findings
  echo "--- No reviewed commit named: re-request with the head SHA pinned ---"
  exit 0
fi

if [ "$(count_reactions "eyes")" -gt 0 ] || [ -n "$(pending_on_comments)" ]; then
  echo "PENDING: Codex review is in flight on $REPO#$PR (since $SINCE)"
  exit 2
fi

echo "TIMEOUT: no Codex response on $REPO#$PR after $((POLLS * INTERVAL))s (since $SINCE)"
exit 1
