---
name: ai-model-disclosure
description: Attribution note for GitHub text posted on the user's behalf. Use when creating or editing an issue, pull request body, review, comment, or review comment.
license: MIT
---

Append this note as the final block of every non-empty issue, pull request, review, comment, or review comment body you create or edit:

```md
> [!NOTE]
> This {type} was uploaded by <img src="https://avatars.githubusercontent.com/u/{avatar}?v=4" width="20" height="20" align="absmiddle" alt="{agent}" /> {model} on behalf of Gonzalo.
```

- `{type}`: one of `issue`, `pull request`, `review`, `comment`, `review comment`.
- `{agent}` and `{avatar}`: `zcode` / `223098841` when you are zcode or running a GLM model; otherwise `Claude` / `81847` when you are Claude; `Codex` / `267193182` when you are Codex.
- `{model}`: your model name and version (e.g. "Opus 5.5", "GPT 6.1 Sol"), taken from a known source, never guessed or copied from these examples.
  - Claude: your system prompt states it.
  - Codex: query `$CODEX_HOME/state_5.sqlite` read-only with `SELECT rollout_path FROM threads WHERE id = $CODEX_THREAD_ID`, then extract only `payload.model` from the last JSONL record whose `type` is `turn_context`.
  - zcode / GLM: use the model name and version supplied by the runtime or system prompt.

Done when the body ends with exactly one attribution note: replace an existing one instead of adding a second.
