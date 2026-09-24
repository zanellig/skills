# Ship Slice references

Evidence behind the Codex behavior `SKILL.md` relies on. Check a claim here before changing it, and add its evidence here when you add one.

- [`codex-docs.md`](codex-docs.md): what OpenAI's docs and the bot's own review footer state.
- [`observed-behavior.md`](observed-behavior.md): what Codex actually did across 99 PRs on `zanellig/*` and `cogniarg/*`, swept 2026-09-24.

| Claim in `SKILL.md` | Status | Evidence |
| --- | --- | --- |
| Reviews come from `chatgpt-codex-connector[bot]` | Documented, observed | [docs](codex-docs.md#bot-identity), [sweep](observed-behavior.md#sweep) |
| Three triggers: On PR open, On every push, Smart detect; per account, overridable per repo; no API exposes it | Settings UI only | [docs](codex-docs.md#review-triggers) |
| Opening a PR activates round 1; a draft activates on ready | Documented | [docs](codex-docs.md#review-triggers) |
| A push activates a round under On every push / Smart detect | Observed | [skills#11](observed-behavior.md#a-push-activates-a-review) |
| `@codex` in the PR body starts a task instead of the review | Observed once | [skills#12](observed-behavior.md#task-summaries) |
| `@codex` with anything but `review` starts a task | Documented, observed | [docs](codex-docs.md#mentions), [sweep](observed-behavior.md#task-summaries) |
| Every genuine response names `Reviewed commit: <sha>`; a comment without it is a notice | Observed | [sweep](observed-behavior.md#response-shapes) |
| Notices: usage limit, missing environment | Observed | [sweep](observed-behavior.md#notices) |
| A clean round is the `Didn't find any major issues` comment, often with a PR 👍 | Documented, observed | [docs](codex-docs.md#reactions), [sweep](observed-behavior.md#clean-rounds) |
| 👀 means a review is in flight | Documented | [docs](codex-docs.md#reactions) |
| The bot usually removes 👀 but can leave it on a dropped request | Observed: removed on 85 of 87 | [sweep](observed-behavior.md#eyes-reaction) |
| The bot reads a thread reply only when @-mentioned | Observed | [sweep](observed-behavior.md#thread-replies) |
| `@codex` anywhere in a thread reply starts a task that spends the user's Codex usage | Task observed; billing unverified | [sweep](observed-behavior.md#task-summaries) |
| A second request re-reviews the same commit with duplicate findings | Observed once | [email#37](observed-behavior.md#stale-and-duplicate-reviews) |
| Codex reviews the commit as of request time, so pin the SHA | Observed | [email#37, pagos#28](observed-behavior.md#stale-and-duplicate-reviews) |
| Under Smart detect a reviewed push usually answers within 15 minutes | Observed: 82% | [latency](observed-behavior.md#review-latency) |
| GitHub keeps one reaction of each type per user | GitHub API behavior | [docs](codex-docs.md#github) |
