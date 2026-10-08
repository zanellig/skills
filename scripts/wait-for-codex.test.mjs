import { expect, test } from "bun:test";
import { chmodSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = join(import.meta.dir, "../skills/productivity/ship-slice/scripts/wait-for-codex.sh");
const SINCE = "2026-08-15T22:11:52Z";

const HEAD = "abc1234567f00d";
const RESPONSE = "Codex Review: no major issues. **Reviewed commit:** abc1234567";
const NOTICE = "You have reached your Codex usage limits for code reviews.";

// The comment Codex keeps on each PR, rewritten as a review runs.
function summaryComment({ status, at = "2026-08-15T22:20:01.123456Z", sha = HEAD.slice(0, 7) }) {
  const state = status === "Running" ? "🔄 **Running** since" : `✅ **${status}**`;
  return `<!-- codex-pull-request-review-summary -->

## Codex Review Summary

| Review | Status | Commit | Review trigger |
| --- | --- | --- | --- |
| 📝 **Code Review** | ${state} <relative-time datetime="${at}">${at}</relative-time> | \`${sha}\` | New commits |`;
}

// Stubs `gh` so each query the waiter makes answers from one scenario. The bot
// issue-comment query splits on whether the body names a reviewed commit, so
// the stub matches the `== true` / `== false` jq the script builds.
function runWaiter({ review, inline, response, lateResponse, notice, lateNotice, thumbsUp, eyes, commentEyes, summary, requireCommit = false, prReadable = true, polls = 1, since = SINCE } = {}) {
  const bin = mkdtempSync(join(tmpdir(), "wait-for-codex-"));
  const gh = join(bin, "gh");
  const emit = (on, text) => (on ? `echo '${text}'` : ":");
  // A late answer shows up only after the waiter has slept once.
  const emitLate = (on, text) => (on ? `[ ! -e "${bin}/slept" ] || echo '${text}'` : ":");

  try {
    writeFileSync(
      gh,
      `#!/usr/bin/env bash
case "$*" in
  *reactions*) [[ "$*" == *--paginate* ]] || exit 9 ;;
  # The pending scan (the comments query with no author filter) must start at
  # SINCE rather than walking the PR's whole history.
  *issues/3/comments*".id"*) [[ "$*" == *user.login* || "$*" == *">="* ]] || exit 10 ;;
esac
case "$*" in
  *"pulls/3 "*) ${prReadable ? `echo ${HEAD}` : "exit 1"} ;;
  *pulls/3/reviews*) ${emit(review, '{"state":"COMMENTED","commit_id":"abc1234567"}')} ;;
  *pulls/3/comments*) ${emit(inline, '{"path":"a.ts","line":1,"commit_id":"def7654321"}')} ;;
  *issues/3/comments*"== true"*) ${emit(response, RESPONSE)}; ${emitLate(lateResponse, RESPONSE)} ;;
  # The summary names no reviewed commit, so it lands here unless excluded.
  *issues/3/comments*"== false"*) ${emit(notice, NOTICE)}; ${emitLate(lateNotice, NOTICE)}; [[ "$*" == *review-summary* ]] || ${emit(summary, summary && summaryComment(summary))} ;;
  *issues/3/comments*review-summary*) ${emit(summary, summary && summaryComment(summary))} ;;
  *issues/3/comments*) ${emit(commentEyes, "42")} ;;
  *issues/comments/42/reactions*) ${emit(commentEyes, "77")} ;;
  *issues/3/reactions*eyes*) ${emit(eyes, "77")} ;;
  *issues/3/reactions*"+1"*) ${emit(thumbsUp, '{"content":"+1","created_at":"2026-08-15T22:13:52Z"}')} ;;
esac
`,
    );
    chmodSync(gh, 0o755);
    writeFileSync(join(bin, "sleep"), `#!/usr/bin/env bash\necho >> "${bin}/slept"\n`);
    chmodSync(join(bin, "sleep"), 0o755);

    const result = Bun.spawnSync(["bash", SCRIPT, "3", since, "owner/repo"], {
      env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, POLLS: String(polls), INTERVAL: "0", REQUIRE_COMMIT: requireCommit ? "1" : "0" },
    });
    const slept = join(bin, "slept");
    result.sleeps = existsSync(slept) ? readFileSync(slept, "utf8").split("\n").length - 1 : 0;
    return result;
  } finally {
    rmSync(bin, { recursive: true, force: true });
  }
}

test("a fresh review completes a round and reports the commit Codex read", () => {
  const result = runWaiter({ review: true });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("Commits Codex read");
  expect(result.stdout.toString()).toContain("abc1234567");
});

test("a comment naming the reviewed commit completes a round", () => {
  const result = runWaiter({ response: true });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("Reviewed commit");
});

test("a thumbs-up alone completes a clean round one poll later", () => {
  const result = runWaiter({ thumbsUp: true, polls: 5 });

  expect(result.exitCode).toBe(0);
  expect(result.sleeps).toBe(1);
  expect(result.stdout.toString()).toContain("Clean: the thumbs-up covers the head");
});

test("a thumbs-up keeps the wait open for the comment naming the reviewed commit", () => {
  const result = runWaiter({ thumbsUp: true, lateResponse: true });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("abc1234567");
  expect(result.stdout.toString()).not.toContain("Clean: the thumbs-up");
});

test("a late thumbs-up cannot complete a later round after a timeout", () => {
  expect(runWaiter().exitCode).toBe(1);
  // A delayed response can satisfy a retry while another activation remains
  // in flight. That activation's reaction must not cover the next head.
  expect(runWaiter({ review: true, requireCommit: true }).exitCode).toBe(0);
  const result = runWaiter({ thumbsUp: true, requireCommit: true });

  expect(result.exitCode).toBe(1);
  expect(result.stdout.toString()).not.toContain("Clean: the thumbs-up");
});

test("requiring a commit still accepts a named response after a thumbs-up", () => {
  const result = runWaiter({ thumbsUp: true, lateResponse: true, requireCommit: true });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("abc1234567");
  expect(result.stdout.toString()).not.toContain("Clean: the thumbs-up");
});

test("a notice blocks the round instead of completing it", () => {
  const result = runWaiter({ notice: true });

  expect(result.exitCode).toBe(4);
  expect(result.stdout.toString()).toContain("BLOCKED: Codex posted a notice");
  expect(result.stdout.toString()).toContain("usage limits");
});

test("a notice that lands during the last sleep still blocks the round", () => {
  const result = runWaiter({ lateNotice: true });

  expect(result.exitCode).toBe(4);
});

test("a review still completes the round when a notice is also present", () => {
  const result = runWaiter({ review: true, notice: true });

  expect(result.exitCode).toBe(0);
});

test("no fresh Codex response still times out", () => {
  const result = runWaiter();

  expect(result.exitCode).toBe(1);
  expect(result.stdout.toString()).toContain("TIMEOUT: no Codex response");
});

test("an inline-only response reports the commit that finding was raised against", () => {
  const result = runWaiter({ inline: true });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("def7654321");
});

test("a fresh eyes reaction reports an in-flight review after the wait expires", () => {
  const result = runWaiter({ eyes: true });

  expect(result.exitCode).toBe(2);
  expect(result.stdout.toString()).toContain("PENDING: Codex review is in flight");
});

test("an eyes reaction on the activating comment also reports an in-flight review", () => {
  const result = runWaiter({ commentEyes: true });

  expect(result.exitCode).toBe(2);
  expect(result.stdout.toString()).toContain("PENDING: Codex review is in flight");
});

test("a completed review summary naming the head is a clean round, even when a commit is required", () => {
  const result = runWaiter({ summary: { status: "Completed" }, requireCommit: true });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain(`Clean: the review summary shows ${HEAD} completed`);
});

test("findings outrank the completed summary that follows them", () => {
  const result = runWaiter({ review: true, summary: { status: "Completed" } });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("abc1234567");
  expect(result.stdout.toString()).not.toContain("Clean: the review summary");
});

test("a summary from another commit or an earlier round leaves the round open", () => {
  expect(runWaiter({ summary: { status: "Completed", sha: "0123456" } }).exitCode).toBe(1);
  expect(runWaiter({ summary: { status: "Completed", at: "2026-08-15T22:00:00.5Z" } }).exitCode).toBe(1);
});

test("a running summary is an in-flight review, not a notice", () => {
  const result = runWaiter({ summary: { status: "Running" } });

  expect(result.exitCode).toBe(2);
  expect(result.stdout.toString()).toContain(`review summary shows ${HEAD} running`);
});

test("an unknown summary status leaves the other signals to decide", () => {
  expect(runWaiter({ summary: { status: "Cancelled" }, thumbsUp: true, polls: 5 }).exitCode).toBe(0);
  expect(runWaiter({ summary: { status: "Cancelled" } }).exitCode).toBe(1);
});

test("a missing since timestamp is an error, so a stale thumbs-up cannot pass as clean", () => {
  const result = runWaiter({ thumbsUp: true, since: "" });

  expect(result.exitCode).toBe(3);
  expect(result.stderr.toString()).toContain("<since_iso>");
});

test("an unreadable PR is an error, not a timeout", () => {
  const result = runWaiter({ prReadable: false });

  expect(result.exitCode).toBe(3);
  expect(result.stderr.toString()).toContain("cannot read owner/repo#3");
});
