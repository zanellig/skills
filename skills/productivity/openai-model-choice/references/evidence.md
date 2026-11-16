# Evidence for OpenAI model choice

Everything here was read on 2026-11-12 through an automated page fetch, which can mis-transcribe a figure. Re-read the source before you quote a number to the user.

## Artificial Analysis table

Source: the [Artificial Analysis model leaderboard](https://artificialanalysis.ai/leaderboards/models), Intelligence Index v5.0.1. Cost is the weighted average cost per Intelligence Index task at API list prices. Minutes is output tokens divided by end-to-end output speed, per task. The index mixes reasoning, knowledge and coding evaluations, so it is not an agentic coding benchmark. These figures have one source and were not cross-checked against a second page.

Rows are sorted by cost.

| Setting | Index | Cost | Minutes | First answer token (s) | Position |
| --- | --- | --- | --- | --- | --- |
| Luna low | 10 | $0.01 | 0.6 | 3.14 | Frontier |
| Luna medium | 18 | $0.04 | 3.5 | 5.96 | Frontier |
| Luna non-reasoning | 9 | $0.07 | 1.9 | 1.68 | Loses to Terra low on score and time at the same cost |
| Luna high | 21 | $0.07 | 5.7 | 11.95 | Loses to Terra low on score and time at the same cost |
| 6.1 Terra low | 29 | $0.07 | 1.2 | 2.75 | Frontier |
| Luna xhigh | 23 | $0.10 | 7.4 | 19.19 | Loses to Terra low on all three |
| Luna max | 28 | $0.15 | 11.6 | 78.05 | Loses to Terra low on all three |
| 6.1 Sol low | 35 | $0.16 | 1.9 | 2.90 | Frontier |
| 6.1 Terra medium | 38 | $0.17 | 2.8 | 4.62 | Frontier |
| 6.1 Terra non-reasoning | 31 | $0.23 | 2.4 | 2.10 | Loses to Sol low on all three |
| 6.1 Terra high | 42 | $0.26 | 4.2 | 11.57 | Frontier |
| 6.1 Sol medium | 46 | $0.36 | 4.3 | 4.62 | Frontier |
| 6.1 Terra xhigh | 45 | $0.40 | 6.4 | 32.11 | Loses to Sol medium on all three |
| 6.1 Sol high | 50 | $0.59 | 7.4 | 34.70 | Frontier |
| 6.1 Sol xhigh | 52 | $0.76 | 9.8 | 69.77 | Frontier |
| 6.1 Terra max | 51 | $0.96 | 14.2 | 164.71 | Loses to Sol xhigh on all three |
| 6.1 Sol max | 55 | $1.27 | 22.0 | 165.06 | Frontier |
| Astra low | 43 | $1.42 | 4.0 | 3.63 | Behind Sol medium on cost. 0.3 minutes faster |
| Astra medium | 52 | $2.73 | 7.4 | 6.99 | Behind Sol xhigh on cost. 2.4 minutes faster |
| Astra high | 55 | $3.24 | 9.5 | 56.50 | Behind Sol max on cost. Under half the time |
| Astra xhigh | 55 | $3.66 | 11.6 | 100.90 | Loses to Astra high on all three |
| Astra max | 57 | $6.24 | 24.3 | 231.95 | Frontier, two points for 4.9 times Sol max |

The leaderboard has no scored rows for GPT-6 Sol, the GPT-5.6 models or the `ultra` effort.

## How the frontier was worked out

A setting is on the cost frontier when no cheaper setting scores as high. Sorted by cost, that is every row whose score beats all rows above it.

- On cost: Luna low, Luna medium, Terra low, Sol low, Terra medium, Terra high, Sol medium, Sol high, Sol xhigh, Sol max, Astra max.
- On time instead of cost: Luna low, Terra low, Sol low, Terra medium, Astra low, Sol medium, Astra medium, Astra high, Astra max.

Astra appears on the cost frontier only at max, and on the time frontier at every level except xhigh. That is why the skill treats Astra as the way to buy time.

## Plan rules

Source: [Codex pricing](https://learn.chatgpt.com/docs/pricing.md) and the [API pricing page](https://developers.openai.com/api/docs/pricing).

| Model | Credits per 1M (input / cached / output) | API dollars per 1M (input / cached / output) |
| --- | --- | --- |
| GPT-6 Astra | 250 / 25 / 1,250 | $10.00 / $1.00 / $50.00 |
| GPT-6.1 Sol | 50 / 2.5 / 250 | $2.00 / $0.10 / $10.00 |
| GPT-6.1 Terra | 25 / 1.25 / 125 | $1.00 / $0.05 / $5.00 |
| GPT-6 Sol | 50 / 5 / 250 | $2.00 / $0.20 / $10.00 |
| GPT-6 Luna | 2.5 / 0.25 / 12.5 | $0.10 / $0.01 / $0.50 |

Every credit rate is 25 times the API dollar price, for input, cached input and output alike. A cost in API dollars is therefore the same relative draw in credits.

- Estimated local messages per five-hour period on Plus and Standard Business: Astra 5 to 45, 6.1 Sol 15 to 160, 6.1 Terra 35 to 285, GPT-6 Sol 15 to 150, Luna 350 to 3,000. The page calls these "not fixed message limits".
- "Pro plans currently have no five-hour limit." On Plus, "Weekly limits may also apply."
- Fast speed draws 2.5 times the included usage. Ultrafast, on Astra and 6.1 Sol, draws 8 times.
- Past the limit, Plus and Pro users can buy credits. An active turn is allowed to finish.
- The page says nothing about how reasoning effort, `ultra` or subagents count. Higher effort uses more tokens, and tokens are what is billed.

Two points come from a search summary and were not read on a page directly: that Astra usage is limited on Plus, and that the Pro plans cover Astra inside the normal allowance. The help-centre article on [managing usage with GPT-6 Astra](https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex) refused the fetch.

How T3 Code's `serviceTier` option maps to OpenAI's speed tiers was not checked.

## OpenAI's guidance by task

Source: [Model selection](https://developers.openai.com/api/docs/guides/model-selection.md) and [Models in Codex](https://learn.chatgpt.com/docs/models).

OpenAI's ladder, lightest first:

1. Luna at low: fine-grained edits, well-scoped problem-solving, simple data extraction.
2. Luna at extra high: finding current context across apps, prioritizing work, problems with clear constraints.
3. 6.1 Sol at medium: complex technical work and coordinated deliverables you expect to revise.
4. 6.1 Sol at extra high: polished deliverables, connected visual systems, decisions from conflicting evidence.
5. Astra at low: concise writing and content adaptation that preserve facts and nuance.
6. Astra at medium: ambitious projects that need broad context and complete results.
7. Astra at extra high: demanding analysis and complex deliverables with exacting requirements.

Other points the skill relies on:

- 6.1 Terra suits concise writing from supplied material, computer use with a defined outcome, and scoped code fixes. Give it clear inputs, requirements and a way to verify results.
- 6.1 Sol is described as "Near-Astra performance for complex work at a lower cost than Astra."
- Luna is "Our most efficient model for focused, high-volume tasks".
- "Most tasks do not need Max or Ultra." Ultra uses subagents to work on parts of a task in parallel, and Luna does not support it.
- Compare models on the same inputs and "keep the lightest setting that meets your quality bar."
- T3 Code offers these Codex models with a `reasoningEffort` option of low, medium, high, xhigh, max and ultra. Its defaults are low on 6.1 Sol and 6.1 Terra, and medium on Astra and Luna.

## Where the two sources disagree

- OpenAI suggests starting Luna at high and uses Luna at extra high for context gathering. The index puts every Luna setting above medium behind Terra at low, which scores higher for the same cost or less and is several times faster.
- OpenAI places Astra at low and medium above Sol at extra high on its ladder. The index scores Astra low at 43, under Sol medium (46), and Astra medium level with Sol xhigh (52) at 3.6 times the cost.
- OpenAI says that if cost and latency are not concerns, you can default to Astra. On a subscription cost is the allowance, so the skill does not default to it.

The skill follows the index for effort, as its owner asked, and keeps OpenAI's task-to-model mapping where the index does not contradict it. If delegated results disagree with the table, trust the results and tell the user.

## Refresh steps

1. Fetch the [leaderboard](https://artificialanalysis.ai/leaderboards/models) and list every OpenAI row with its index, cost per task and minutes per task.
2. Recompute the cost and time frontiers as described above.
3. Re-read the pricing page and confirm the credit rates still equal 25 times the API prices.
4. Update the picks and the date in `SKILL.md`, and this file's tables.
