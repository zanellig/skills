import { expect, test } from "bun:test";
import { summarize } from "./gen-reference.mjs";

test("keeps the first sentence, drops trigger text", () => {
  expect(summarize("Create and push semver version tags. Use when tagging a commit.")).toBe(
    "Create and push semver version tags.",
  );
});

test("keeps a description that is a single sentence", () => {
  const only = "Restate the last message in plain human language, with no jargon.";
  expect(summarize(only)).toBe(only);
});

test("does not break on abbreviations", () => {
  expect(summarize("Deploy to a CDN, e.g. Cloudflare Pages. Use when shipping.")).toBe(
    "Deploy to a CDN, e.g. Cloudflare Pages.",
  );
  expect(summarize("Compare a repo vs. Google's style guide. Use when reviewing.")).toBe(
    "Compare a repo vs. Google's style guide.",
  );
  expect(summarize("Ship it, i.e. Merge the branch. Use when done.")).toBe("Ship it, i.e. Merge the branch.");
  expect(summarize("Ask Dr. Smith to review. Use when unsure.")).toBe("Ask Dr. Smith to review.");
});

test("an all-caps acronym still ends a sentence", () => {
  expect(summarize("Drive a slice to a merged PR. Use when shipping.")).toBe("Drive a slice to a merged PR.");
});

test("folds a multi-line YAML description onto one line", () => {
  expect(summarize("Forces the laziest\nsolution that works. Use when coding.")).toBe(
    "Forces the laziest solution that works.",
  );
});
