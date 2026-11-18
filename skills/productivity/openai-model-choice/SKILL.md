---
name: openai-model-choice
description: Choose an OpenAI model family, its newest available checkpoint, and reasoning effort for a ChatGPT subscription. Use before setting a model or effort for a Codex delegate or subagent, pinning a model in Codex config or an agent file, or answering which OpenAI model to use.
license: MIT
---

# OpenAI model choice

Honor the model and effort the user explicitly requests. This skill applies once you need to choose a model or effort.

## Resolve the checkpoint

1. Run `codex debug models` in the target Codex environment each time you need to resolve a family to a model ID. Read `models[].slug` and `supported_reasoning_levels`. Use the normal command so Codex can refresh the catalog.
2. Choose a family and effort from the table below. Within that family, pick the newest checkpoint available to the runner that will execute the task. Use the exact ID from the catalog and compare version components numerically, treating an omitted minor version as zero. When the runner exposes its own supported models, use it to check that it accepts the ID. If the CLI catalog is unavailable, use the runner's model list. If neither confirms a usable ID for the chosen family, say what you could verify.
3. Set the model ID and effort together. If the newest checkpoint lacks the suggested effort, pick a supported effort that fits the task. If the runner cannot honor an explicit user choice, report the limitation before substituting.

## Choose a family and effort

Use the lightest setting that meets the task's quality and latency requirements. These starting points come from the measured cost frontier and carry forward as estimates when a family gets a new checkpoint.

| Work | Family | Effort |
| --- | --- | --- |
| Tagging, routing, or simple extraction at volume | Luna | `low` |
| Finding files, searching code, reading logs, or summarizing | Terra | `low` |
| A scoped code fix, concise writing from supplied material, or computer use with a defined outcome | Terra | `high` |
| Everyday engineering when someone is waiting for the reply | Sol | `low` |
| Everyday engineering and technical work you expect to revise | Sol | `medium` |
| Engineering where edge cases or verification decide the result | Sol | `high` |
| A polished deliverable or a decision from conflicting evidence | Sol | `xhigh` |
| The hardest work when latency is flexible | Sol | `max` |
| The hardest work when latency matters and the subscription allowance can cover the higher cost | Astra | `high` |

Use `max` on Astra or `ultra` on any model only when the user asks. Leave the service tier at its default unless the user asks for another tier.

If a pick falls short, first clarify the inputs, requirements, and how to verify the result. Then raise effort within the family if there is a suitable supported setting. Move from Terra to Sol or from Sol to Astra if the task still needs more capability.

## Benchmark evidence

Read [references/evidence.md](references/evidence.md) when you need scores, costs, timings, or plan rules. Match benchmark rows to the exact checkpoint and effort before using their numbers, and check the source before quoting them. If the newest checkpoint has no matching benchmark, treat the family recommendation as provisional and say so when explaining the pick.
