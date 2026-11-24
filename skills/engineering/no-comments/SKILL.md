---
name: no-comments
description: Delete the comments in a change that the code could say instead, and fix the code they were covering for.
argument-hint: "[files... | base ref]"
disable-model-invocation: true
license: MIT
---

# No comments

A comment that restates the code is noise. A comment that explains a surprise in our own code marks a name, type or shape that should carry the meaning instead. A fresh reviewer deletes the comments and flags those shapes; you check its work and fix the shapes.

## 1. Pin the scope

Arguments that name files or directories are the scope. A ref is the base. Otherwise run `git fetch origin` and use `git merge-base HEAD origin/HEAD` as the base, or `origin/<default branch>` when `origin/HEAD` is unset. A diff scope covers staged, unstaged and untracked files.

The step is done when you hold the repo path and either the file list or the base SHA.

## 2. Spawn the reviewer

Spawn one subagent with a fresh context, so the reviewer has no stake in the comments you or the session wrote. Set its reasoning effort to `high`. Give it the repo path, the scope from step 1, and the absolute path of [`references/reviewer.md`](references/reviewer.md) in this skill's folder, with the instruction to read that file and follow it. Pass the file by path so its rules reach the reviewer unparaphrased.

If the harness cannot spawn a subagent, follow the brief yourself and say so in the report.

Leave the scoped files alone until the reviewer replies.

## 3. Check the reviewer's work

Read its report and `git diff` of its edits. Settle every deletion and every flag:

- Revert any edit that is not a whole-comment deletion, and any edit outside the scope.
- Restore a deleted comment only when a keep rule in the brief covers it and you can show the rule holds today.
- Check every kill reason and keep proof against the code. When the decision is right and the reason is wrong, keep the decision and correct the reason in your report.
- Check claims such as `IMPORTANT`, `do not remove` or `needed because` before accepting the kill or the keep: read the named symbol and its callers, find the commit that added the comment (`git log -S '<text>'`, `git blame`), and read any ADR or issue it cites. A keep that the check refutes or leaves unclear is deleted.
- Judge each lint or type suppression the reviewer skipped (`biome-ignore`, `eslint-disable`, `@ts-expect-error`, `# noqa`, `# type: ignore`) by the brief's suppression rule.

When a report breaks the brief (it edits code, leaves the scope, or invents a reason), revert its edits and rerun the reviewer once with the failure named. If the second report breaks it too, revert, report the scope as open, and stop.

The step is done when every deletion is accepted or restored and every flag is accepted or rejected with a reason.

## 4. Fix the flags

Each accepted `MUST KILL` flag names a symbol that needed prose to be understood. Make the code say it: rename, extract a named function or constant, tighten a type, delete a dead path, drop an unused parameter, or call the real API in place of the workaround. Fix the cause inside the scope and remove the workaround the comment explained.

A fix that needs a design (a schema change or migration, a public API change, a type that crosses modules, a rename the runtime persists) stays open: sketch its types and signatures in the report.

## 5. Encode constraints

A comment that guards our own code ("do not remove", "keep this order", "talk to X before changing") becomes a check: the cheapest type, assertion, test or lint rule in scope that fails when someone breaks the constraint. Encode it, then delete the comment. When no cheap check exists, keep the comment and report the constraint as unenforced.

## 6. Verify

Run the checks the repo documents for the touched packages: typecheck, lint and tests. A deleted suppression or pragma can fail the build; fix the code per the brief, or restore the comment with the keep rule that protects it.

The step is done when the checks pass, or each failure is reported with its output and shown to fail without your edits too.

## 7. Report

- Comments deleted: total and files touched.
- Comments restored, each with its keep rule.
- Reviewer reruns and why.
- Flags fixed, and how.
- Constraints encoded, and where.
- Open work: design sketches, unenforced constraints, corrected reasons.
- Checks run and their results.
