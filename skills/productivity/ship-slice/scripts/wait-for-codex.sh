#!/usr/bin/env bash
# wait-for-codex.sh — poll a PR for a fresh Codex review response, then print it.
#
# Usage: wait-for-codex.sh <pr> <since_iso> [owner/repo]
#   <pr>        PR number.
#   <since_iso> UTC ISO timestamp captured just before the push or request.
#               Only responses newer than it count, which is what ties a
#               clean thumbs-up to that head.
#   [owner/repo] Default: current repo via `gh repo view`.
#
# Env: POLLS (default 15 sleeps), INTERVAL (default 60s per sleep).
# REQUIRE_COMMIT=1 ignores clean reactions when an earlier activation may
# still be running. Keep it enabled for the rest of a PR after any timeout.
# Exits 0 once Codex responds (printing the commits it read and the findings),
# once the review summary shows the PR head completed,
# or one poll after a clean-review thumbs-up,
# 1 on timeout, 2 when the summary or a fresh eyes reaction shows a review
# still in flight, 3 when the repo or PR cannot be read, and 4 when Codex
# posted a notice instead of a review, which means the round never ran.
#
# It sleeps between polls and prints only when it exits.
set -euo pipefail

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
  echo "ERROR: usage: wait-for-codex.sh <pr> <since_iso> [owner/repo]" >&2
  exit 3
fi
PR="$1"
SINCE="$2"
if ! REPO="${3:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"; then
  echo "ERROR: cannot resolve the repo. Run inside it or pass owner/repo." >&2
  exit 3
fi
if ! HEAD_SHA=$(gh api "repos/$REPO/pulls/$PR" --jq .head.sha 2>/dev/null) || [ -z "$HEAD_SHA" ]; then
  echo "ERROR: cannot read $REPO#$PR. Check gh auth and the PR number." >&2
  exit 3
fi
BOT="chatgpt-codex-connector[bot]"
SUMMARY="codex-pull-request-review-summary"
POLLS="${POLLS:-15}"
INTERVAL="${INTERVAL:-60}"
REQUIRE_COMMIT="${REQUIRE_COMMIT:-0}"
case "$REQUIRE_COMMIT" in
  0|1) ;;
  *) echo "ERROR: REQUIRE_COMMIT must be 0 or 1" >&2; exit 3 ;;
esac
if [ "$REQUIRE_COMMIT" -eq 1 ]; then
  echo "Waiting for a response naming the reviewed commit; clean reactions alone are ignored."
fi

line_count() {
  awk 'NF { count++ } END { print count + 0 }'
}

# Every genuine Codex response names the commit it read. A bot issue comment
# without that marker is a notice (usage limit, missing environment), not a
# review; the review summary also lacks it and is read by summary_row instead.
# $1 selects which of the two to return, $2 the field to emit. Fails when the
# query does, so each caller decides whether an unreadable answer matters.
bot_comments() {
  gh api --paginate "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\"
           and (.body | contains(\"$SUMMARY\") | not)
           and ((.body | test(\"Reviewed commit\")) == $1)) | .$2" 2>/dev/null
}

# Codex keeps one summary comment per PR and rewrites its code-review row as
# each review runs: "🔄 **Running** since <time>", then "✅ **Completed** <time>",
# next to the short SHA it reads. Prints "<status> <time> <sha>", or nothing
# when the PR has no summary, which leaves the other signals to decide.
# The backticks in the sed pattern match the literal ones around the SHA.
# shellcheck disable=SC2016
summary_row() {
  gh api --paginate "repos/$REPO/issues/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and (.body | contains(\"$SUMMARY\"))) | .body" 2>/dev/null |
    sed -nE 's/^\| 📝[^|]*\| [^*]*\*\*([A-Za-z]+)\*\*[^|]*datetime="([^"]+)"[^|]*\| `([0-9a-f]+)`.*/\1 \2 \3/p' |
    head -n 1 || true
}

# True when the last summary row read names the PR head with status $1.
summary_shows() {
  [ "$row_status" = "$1" ] && [ -n "$row_sha" ] && [[ "$HEAD_SHA" == "$row_sha"* ]]
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

# Fails when any query does: a completed summary means no findings only if
# every place a finding could appear was read.
count_new() {
  local reviews comments inline matches
  matches=$(gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
    --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | .id" 2>/dev/null) || return 1
  reviews=$(printf '%s\n' "$matches" | line_count)
  matches=$(bot_comments true id) || return 1
  comments=$(printf '%s\n' "$matches" | line_count)
  matches=$(gh api --paginate "repos/$REPO/pulls/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | .id" 2>/dev/null) || return 1
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
    { bot_comments true body || true; } | { grep -io 'reviewed commit.*' || true; }
  } | sort -u
  echo "--- Review summaries (state / body) ---"
  gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
    --jq ".[] | select(.user.login==\"$BOT\" and .submitted_at > \"$SINCE\") | {state, submitted_at, body}" 2>/dev/null || true
  echo "--- Inline findings (id, path:line) ---"
  gh api --paginate "repos/$REPO/pulls/$PR/comments" \
    --jq ".[] | select(.user.login==\"$BOT\" and .created_at > \"$SINCE\") | {id, path, line, body}" 2>/dev/null || true
  echo "--- Issue comments ---"
  bot_comments true body || true
  echo "--- Clean-review reactions ---"
  gh api --paginate "repos/$REPO/issues/$PR/reactions" \
    --jq ".[] | select(.user.login==\"$BOT\" and .content==\"+1\" and .created_at > \"$SINCE\") | {content, created_at}" 2>/dev/null || true
}

# A thumbs-up names no commit. The caller permits it only when no earlier
# activation can still add a reaction; freshness alone cannot establish that.
clean_thumbs_up() {
  print_findings
  echo "--- Clean: the thumbs-up covers the head pushed or requested at $SINCE ---"
  exit 0
}

# Sleep before every check but the first, so a response that lands during the
# last sleep still gets classified. A comment naming the commit lands within
# seconds of the thumbs-up when it comes at all, so one more poll waits for it.
thumbs_up=0
for i in $(seq 0 "$POLLS"); do
  [ "$i" -eq 0 ] || sleep "$INTERVAL"
  # Codex posts findings seconds before it marks the row Completed, so reading
  # the row first lets count_new see every finding of a completed review.
  read -r row_status row_at row_sha <<<"$(summary_row)"
  # An unreadable finding query yields no verdict; the next poll retries it.
  new=$(count_new) || continue
  if [ "$new" -gt 0 ]; then
    print_findings
    exit 0
  fi
  if summary_shows Completed && [[ "$row_at" > "$SINCE" ]]; then
    print_findings
    echo "--- Clean: the review summary shows $HEAD_SHA completed at $row_at ---"
    exit 0
  fi
  notice=$(bot_comments false body || true)
  if [ -n "$notice" ]; then
    echo "BLOCKED: Codex posted a notice instead of a review on $REPO#$PR (since $SINCE)"
    printf '%s\n' "$notice"
    exit 4
  fi
  [ "$thumbs_up" -eq 0 ] || clean_thumbs_up
  if [ "$REQUIRE_COMMIT" -eq 0 ] && [ "$(count_reactions "+1")" -gt 0 ]; then
    thumbs_up=1
  fi
done

[ "$thumbs_up" -eq 0 ] || clean_thumbs_up

if summary_shows Running; then
  echo "PENDING: Codex review is in flight on $REPO#$PR: the review summary shows $HEAD_SHA running since $row_at"
  exit 2
fi
if [ "$(count_reactions "eyes")" -gt 0 ] || [ -n "$(pending_on_comments)" ]; then
  echo "PENDING: Codex review is in flight on $REPO#$PR (since $SINCE)"
  exit 2
fi

echo "TIMEOUT: no Codex response on $REPO#$PR after $((POLLS * INTERVAL))s (since $SINCE)"
exit 1
