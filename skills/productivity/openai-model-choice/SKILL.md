---
name: openai-model-choice
description: Which OpenAI model (Luna, Terra, Sol or Astra) and reasoning effort to give a task, picked from the Artificial Analysis cost frontier for a ChatGPT subscription. Use before setting a model or reasoning effort on a Codex delegate or subagent, when pinning a model in Codex config or an agent file, or when the user asks which OpenAI model to use.
license: MIT
---

# OpenAI model choice

Pick the model and reasoning effort for work you hand to an OpenAI model: a Codex delegate, a subagent, or a model pinned in Codex config or an agent file. This reference covers which model to use once you delegate. Whether to delegate is a separate decision, and a model or effort the user names always wins.

## The budget

The work runs on a ChatGPT subscription, so the budget is the plan's Codex allowance. It is drawn in credits per token, at a published rate for each model.

| Model | Id | Credits per 1M input | Credits per 1M output |
| --- | --- | --- | --- |
| Astra | `gpt-6-astra` | 250 | 1,250 |
| 6.1 Sol | `gpt-6.1-sol` | 50 | 250 |
| 6.1 Terra | `gpt-6.1-terra` | 25 | 125 |
| Luna | `gpt-6-luna` | 2.5 | 12.5 |

- Every rate is 25 credits per API dollar, so the Cost column below is the relative draw on the allowance at standard speed.
- The four models draw on one allowance, so the cost frontier applies as it stands. On Plus, Astra usage is described as limited.
- Plus has a five-hour window and Pro does not. A weekly limit can apply on both.
- OpenAI's faster speeds draw 2.5 to 8 times as much. Leave `serviceTier` at `default` unless the user asks.

## Picks

Each row sits on the Artificial Analysis cost frontier: no cheaper setting scores as high. Index is the Intelligence Index score, Cost is dollars per index task at API prices, and Minutes is time per index task. Read Cost and Minutes as ratios between rows.

| Work | Model | `reasoningEffort` | Index | Cost | Minutes |
| --- | --- | --- | --- | --- | --- |
| Tagging, routing or simple extraction at volume | `gpt-6-luna` | `low` | 10 | \$0.01 | 0.6 |
| Find files, search code, read logs, summarize | `gpt-6.1-terra` | `low` | 29 | \$0.07 | 1.2 |
| A scoped code fix, concise writing from supplied material, computer use with a defined outcome | `gpt-6.1-terra` | `high` | 42 | \$0.26 | 4.2 |
| Everyday engineering and technical work you expect to revise | `gpt-6.1-sol` | `medium` | 46 | \$0.36 | 4.3 |
| The same, where edge cases or verification decide the result | `gpt-6.1-sol` | `high` | 50 | \$0.59 | 7.4 |
| A polished deliverable, or a decision from conflicting evidence | `gpt-6.1-sol` | `xhigh` | 52 | \$0.76 | 9.8 |
| The hardest work, when the wait does not matter | `gpt-6.1-sol` | `max` | 55 | \$1.27 | 22.0 |

Three more settings are on the frontier between those rows: `gpt-6-luna` at `medium` (18, \$0.04), `gpt-6.1-sol` at `low` (35, \$0.16, 1.9 minutes) and `gpt-6.1-terra` at `medium` (38, \$0.17). Use Sol at `low` when someone is waiting on the reply.

Set the model id and `reasoningEffort` together. In T3 Code the default effort differs by model (`low` on 6.1 Sol and Terra, `medium` on Astra and Luna), so an unset effort is a choice too.

## Astra

Astra buys time and a small ceiling. Below `max` it is off the cost frontier, because Sol reaches the same scores for under half the draw.

- `gpt-6-astra` at `high` (55, \$3.24, 9.5 minutes) matches Sol at `max` in under half the time, for 2.6 times the draw. Use it for the hardest work when someone is waiting.
- `gpt-6-astra` at `max` (57, \$6.24, 24.3 minutes) is the top score. It adds two points over Sol at `max` for 4.9 times the draw. Use it only when the user asks for it.

## Settings that lose

- `gpt-6-luna` above `medium`. Terra at `low` scores higher for the same cost or less, in a fraction of the time.
- `gpt-6.1-terra` at `xhigh` or `max`. Sol at `medium` and at `xhigh` beat them on score, cost and time.
- `gpt-6-astra` at `low` or `medium`. Sol at `medium` and at `xhigh` score at least as high for under a third of the draw, and take 0.3 and 2.4 minutes longer.
- `gpt-6-astra` at `xhigh`. Astra at `high` scores the same for less cost and less time.
- `ultra`. It has no index data, and it splits the task across parallel subagents. Use it only when the user asks for it.
- The older ids (`gpt-6-sol`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`). They have no rows in the index, so use the four models above.

## When a pick falls short

Work through this order, one step at a time:

1. Give the model clear inputs, the requirements, and a way to verify the result, such as a regression test or a saved record it can reopen. Terra and Luna depend on this most.
2. Raise effort to the next frontier setting for that model.
3. Move up a model: from Terra at `high` to Sol at `medium`, and from Sol at `max` to Astra.

## Freshness

The numbers are from Artificial Analysis Intelligence Index v5.0.1, read on 2026-11-12. The full table, the frontier working, the plan rules, the sources and the refresh steps are in [references/evidence.md](references/evidence.md). Read it when a model here is no longer the newest of its family, when the harness offers a model missing from the table, or before quoting a number to the user. When the table is stale, tell the user.
