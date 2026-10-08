# Ship Slice references

Sources for the documented behavior used by `SKILL.md`.

- [`codex-docs.md`](codex-docs.md): what OpenAI's docs, the bot's own review footer, and its review summary state.

| Claim in `SKILL.md` | Status | Evidence |
| --- | --- | --- |
| Reviews come from `chatgpt-codex-connector[bot]` | Documented | [docs](codex-docs.md#bot-identity) |
| Three triggers: On PR open, On every push, Smart detect; per account, overridable per repo; no API exposes it | Settings UI only | [docs](codex-docs.md#review-triggers) |
| Opening a PR activates round 1; a draft activates on ready | Documented | [docs](codex-docs.md#review-triggers) |
| `@codex` with anything but `review` starts a task | Documented | [docs](codex-docs.md#mentions) |
| A review with no suggestions gets a 👍 | Documented | [docs](codex-docs.md#reactions) |
| 👀 means a review is in flight | Documented | [docs](codex-docs.md#reactions) |
| GitHub keeps one reaction of each type per user | GitHub API behavior | [docs](codex-docs.md#github) |
| The review summary shows each round Running, then Completed, naming the reviewed commit | Observed: 7 PRs | [summary](codex-docs.md#review-summary) |
| Findings land seconds before the summary shows Completed | Observed: 5 rounds | [summary](codex-docs.md#review-summary) |
| `exec_command` yields within 30 s; empty `write_stdin` polls block up to `background_terminal_max_timeout` | Codex source, `rust-v0.158.0` | [blocking wait](workflow-details.md#blocking-wait-in-codex) |
