import { expect, test } from "bun:test";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = join(import.meta.dir, "../skills/productivity/ship-slice/scripts/wait-for-codex.sh");
const SINCE = "2026-08-15T22:11:52Z";

const RESPONSE = "Codex Review: no major issues. **Reviewed commit:** abc1234567";
const NOTICE = "You have reached your Codex usage limits for code reviews.";

// Stubs `gh` so each query the waiter makes answers from one scenario. The bot
// issue-comment query splits on whether the body names a reviewed commit, so
// the stub matches the `== true` / `== false` jq the script builds.
function runWaiter({ review, inline, response, notice, thumbsUp, eyes, commentEyes, prReadable = true } = {}) {
  const bin = mkdtempSync(join(tmpdir(), "wait-for-codex-"));
  const gh = join(bin, "gh");
  const emit = (on, text) => (on ? `echo '${text}'` : ":");

  try {
    writeFileSync(
      gh,
      `#!/usr/bin/env bash
case "$*" in
  *reactions*) [[ "$*" == *--paginate* ]] || exit 9 ;;
esac
case "$*" in
  *"pulls/3 "*) ${prReadable ? "echo 3" : "exit 1"} ;;
  *pulls/3/reviews*) ${emit(review, '{"state":"COMMENTED","commit_id":"abc1234567"}')} ;;
  *pulls/3/comments*) ${emit(inline, '{"path":"a.ts","line":1,"commit_id":"def7654321"}')} ;;
  *issues/3/comments*"== true"*) ${emit(response, RESPONSE)} ;;
  *issues/3/comments*"== false"*) ${emit(notice, NOTICE)} ;;
  *issues/3/comments*) ${emit(commentEyes, "42")} ;;
  *issues/comments/42/reactions*) ${emit(commentEyes, "77")} ;;
  *issues/3/reactions*eyes*) ${emit(eyes, "77")} ;;
  *issues/3/reactions*"+1"*) ${emit(thumbsUp, '{"content":"+1","created_at":"2026-08-15T22:13:52Z"}')} ;;
esac
`,
    );
    chmodSync(gh, 0o755);

    return Bun.spawnSync(["bash", SCRIPT, "3", SINCE, "owner/repo"], {
      env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, POLLS: "1", INTERVAL: "0" },
    });
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

test("a fresh Codex thumbs-up reaction completes a clean review", () => {
  const result = runWaiter({ thumbsUp: true });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("Clean-review reactions");
});

test("a notice blocks the round instead of completing it", () => {
  const result = runWaiter({ notice: true });

  expect(result.exitCode).toBe(4);
  expect(result.stdout.toString()).toContain("BLOCKED: Codex posted a notice");
  expect(result.stdout.toString()).toContain("usage limits");
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

test("an unreadable PR is an error, not a timeout", () => {
  const result = runWaiter({ prReadable: false });

  expect(result.exitCode).toBe(3);
  expect(result.stderr.toString()).toContain("cannot read owner/repo#3");
});
