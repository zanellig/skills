---
name: openai-model-choice
description: Choose an OpenAI model family, its newest available checkpoint, and reasoning effort for a ChatGPT subscription. Use before setting a model or effort for a Codex delegate or subagent, pinning a model in Codex config or an agent file, or answering which OpenAI model to use.
license: MIT
---

# OpenAI model choice

Pick the model and reasoning effort for work you hand to an OpenAI model: a Codex delegate, a subagent, or a model pinned in Codex config or an agent file. This skill covers which model to use once you delegate. Whether to delegate is a separate decision, and a model or effort the user names always wins.

## Resolve the checkpoint

1. Run `codex debug models` in the target Codex environment each time you need to resolve a family to a model ID. Read `models[].slug` and `supported_reasoning_levels`. Use the normal command so Codex can refresh the catalog.
2. Choose a family and effort from the sections below. Within that family, pick the newest checkpoint available to the runner that will execute the task. Use the exact ID from the catalog and compare version components numerically, treating an omitted minor version as zero. When the runner exposes its own supported models, use it to check that it accepts the ID. If the CLI catalog is unavailable, use the runner's model list. If neither confirms a usable ID for the chosen family, say what you could verify.
3. Set the model ID and effort together. In T3 Code the default effort differs by model (`low` on Sol and Terra, `medium` on Astra and Luna in the last snapshot), so an unset effort is a choice too. If the newest checkpoint lacks the suggested effort, pick a supported effort that fits the task. If the runner cannot honor an explicit user choice, report the limitation before substituting.

## The budget

The work runs on a ChatGPT subscription, so the budget is the plan's Codex allowance. All families draw on one allowance, in credits per token, at a published rate per model.

- In the last snapshot, every credit rate was 25 times the API dollar price, so the Cost column below is the relative draw on the allowance. Per token, Astra drew 5 times Sol, Sol 2 times Terra, and Terra 10 times Luna. A new checkpoint can change these rates.
- Plus has a five-hour window and Pro does not. A weekly limit can apply on both. On Plus, Astra usage is described as limited.
- OpenAI's faster speeds draw 2.5 to 8 times as much. Leave the service tier at its default unless the user asks.

## Family size

A larger model stores more patterns from training: domain knowledge, failure modes, idioms, styles. Effort buys more reasoning over that store, not a bigger store. The Intelligence Index scores tasks with known answers, so it understates the gap on open-ended work.

Grilling a plan, free-hand or unscoped work, and creative work depend on that breadth. Give them Sol at `medium` or above, or Astra when the user wants the strongest result and the allowance covers it. When a larger family at lower effort and a smaller one at higher effort score about the same, take the larger family. Keep Terra and Luna for work where the brief carries the knowledge: clear inputs, stated requirements, and a way to verify the result.

## Picks

Each row sat on the Artificial Analysis cost frontier for the snapshot checkpoints: no cheaper setting scored as high. Index is the Intelligence Index score, Cost is dollars per index task at API prices, and Minutes is time per index task. Read Cost and Minutes as ratios between rows, and treat them as estimates for newer checkpoints of the same family.

| Work | Family | Effort | Index | Cost | Minutes |
| --- | --- | --- | --- | --- | --- |
| Tagging, routing, or simple extraction at volume | Luna | `low` | 10 | \$0.01 | 0.6 |
| Finding files, searching code, reading logs, or summarizing | Terra | `low` | 29 | \$0.07 | 1.2 |
| A scoped code fix, concise writing from supplied material, or computer use with a defined outcome | Terra | `high` | 42 | \$0.26 | 4.2 |
| Everyday engineering when someone is waiting for the reply | Sol | `low` | 35 | \$0.16 | 1.9 |
| Everyday engineering and technical work you expect to revise | Sol | `medium` | 46 | \$0.36 | 4.3 |
| Engineering where edge cases or verification decide the result | Sol | `high` | 50 | \$0.59 | 7.4 |
| A polished deliverable or a decision from conflicting evidence | Sol | `xhigh` | 52 | \$0.76 | 9.8 |
| The hardest work when the wait does not matter | Sol | `max` | 55 | \$1.27 | 22.0 |

Two more settings sat on the frontier between those rows: Luna at `medium` (18, \$0.04) and Terra at `medium` (38, \$0.17).

## Astra

Astra buys time, a small ceiling, and the most stored knowledge. Below `max` it sat off the cost frontier, because Sol reached the same scores for under half the draw.

- Astra at `high` (55, \$3.24, 9.5 minutes) matched Sol at `max` in under half the time, for 2.6 times the draw. Use it for the hardest work when someone is waiting, or for the breadth work under [Family size](#family-size) when the allowance covers it.
- Astra at `max` (57, \$6.24, 24.3 minutes) was the top score, two points over Sol at `max` for 4.9 times the draw. Use it only when the user asks.

## Settings that lose

On the snapshot checkpoints, another setting scored at least as high for less draw:

- Luna above `medium`. Terra at `low` scored higher for the same cost or less, in a fraction of the time.
- Terra at `xhigh` or `max`. Sol at `medium` and at `xhigh` beat them on score, cost and time.
- Astra at `low` or `medium`. Sol at `medium` and at `xhigh` scored at least as high for under a third of the draw, and took 0.3 and 2.4 minutes longer.
- Astra at `xhigh`. Astra at `high` scored the same for less cost and less time.
- `ultra` on any family. It has no index data and splits the task across parallel subagents. Use it only when the user asks.

## When a pick falls short

Work through this order, one step at a time:

1. Give the model clear inputs, the requirements, and a way to verify the result, such as a regression test or a saved record it can reopen. Terra and Luna depend on this most.
2. Raise effort to the next supported setting for that family.
3. Move up a family: from Terra at `high` to Sol at `medium`, and from Sol at `max` to Astra. A wrong approach or missing knowledge needs the larger family, and more effort will not supply it.

## Freshness

The numbers are from Artificial Analysis Intelligence Index v5.0.1, read on 2026-11-12, for the checkpoints named in [references/evidence.md](references/evidence.md). That file also holds the full table, the frontier working, the plan rules, the sources and the refresh steps. Read it before quoting a number to the user, and match a benchmark row to the exact checkpoint and effort first. When the newest checkpoint of a family has no matching row, treat the numbers above as estimates and tell the user the table is stale.
