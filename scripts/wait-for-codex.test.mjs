import { expect, test } from "bun:test";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = join(import.meta.dir, "../skills/productivity/ship-slice/scripts/wait-for-codex.sh");
const SINCE = "2026-08-15T22:11:52Z";

function runWaiter(prReactionCount, commentReactionCount = 0, pendingCount = 0) {
  const bin = mkdtempSync(join(tmpdir(), "wait-for-codex-"));
  const gh = join(bin, "gh");

  try {
    writeFileSync(
      gh,
      `#!/usr/bin/env bash
case "$*" in
  *reactions*) [[ "$*" == *--paginate* && "$*" != *--slurp* ]] || exit 9 ;;
  *issues/3/comments*".id"*) [[ "$*" == *">="* ]] || exit 10 ;;
esac
case "$*" in
  *issues/comments/42/reactions*) ${commentReactionCount > 0 ? `echo '{"content":"+1","created_at":"2026-08-15T22:13:52Z"}'` : ":"} ;;
  *issues/3/comments*".id"*) echo 42 ;;
  *issues/3/reactions*eyes*".id"*) ${pendingCount > 0 ? "echo 77" : ":"} ;;
  *issues/3/reactions*+1*".id"*) ${prReactionCount > 0 ? "echo 77" : ":"} ;;
  *issues/3/reactions*+1*) ${prReactionCount > 0 ? `echo '{"content":"+1","created_at":"2026-08-15T22:13:52Z"}'` : ":"} ;;
  *"length"*) echo 0 ;;
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

test("a fresh Codex thumbs-up reaction completes a clean review", () => {
  const result = runWaiter(1);

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("Clean-review reactions");
  expect(result.stdout.toString()).toContain('"content":"+1"');
});

test("no fresh Codex response still times out", () => {
  const result = runWaiter(0);

  expect(result.exitCode).toBe(1);
  expect(result.stdout.toString()).toContain("TIMEOUT: no Codex response");
});

test("a fresh Codex thumbs-up on a review request completes a clean review", () => {
  const result = runWaiter(0, 1);

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain('"content":"+1"');
});

test("a fresh eyes reaction reports an in-flight review after the wait expires", () => {
  const result = runWaiter(0, 0, 1);

  expect(result.exitCode).toBe(2);
  expect(result.stdout.toString()).toContain("PENDING: Codex review is in flight");
});
