# Evidence for Claude model choice

Everything here was read on 2026-11-12 through an automated page fetch, which can mis-transcribe a figure. Re-read the source before you quote a number to the user.

## Artificial Analysis table

Source: the [Artificial Analysis model leaderboard](https://artificialanalysis.ai/leaderboards/models), Intelligence Index v5.0.1. Cost is the weighted average cost per Intelligence Index task at API list prices. Minutes is output tokens divided by end-to-end output speed, per task. The index mixes reasoning, knowledge and coding evaluations, so it is not an agentic coding benchmark.

Rows are sorted by cost.

| Setting | Index | Cost | Minutes | First answer token (s) | Position |
| --- | --- | --- | --- | --- | --- |
| Haiku 5.5 low | 19 | $0.04 | 2.2 | 7.13 | Frontier |
| Haiku 5.5 medium | 25 | $0.09 | 4.0 | 11.07 | Frontier |
| Haiku 5.5 high | 30 | $0.16 | 6.5 | 21.92 | Frontier |
| Haiku 5.5 xhigh | 35 | $0.25 | 9.6 | 51.52 | Frontier |
| Haiku 5.5 max | 36 | $0.41 | 14.7 | 182.88 | Frontier, one point for 64% more cost |
| Sonnet 5.5 low | 26 | $0.51 | 2.5 | 2.70 | Behind Haiku high on cost. Speed pick |
| Sonnet 5.5 medium | 31 | $0.78 | 3.8 | 4.62 | Behind Haiku xhigh on cost and Opus low on time |
| Opus 5.5 low | 35 | $0.98 | 3.0 | 4.79 | Behind Haiku xhigh on cost. Speed pick |
| Sonnet 5.5 high | 42 | $1.64 | 7.0 | 10.34 | Frontier |
| Opus 5.5 medium | 48 | $2.45 | 7.2 | 15.64 | Frontier |
| Fable 5.2 low | 54 | $3.10 | 6.2 | 8.42 | Frontier |
| Opus 5.5 high | 52 | $3.46 | 9.5 | 23.66 | Behind Fable low. Frontier without Fable |
| Fable 5.2 medium | 56 | $3.80 | 7.7 | 11.23 | Frontier |
| Sonnet 5.5 xhigh | 50 | $4.09 | 14.6 | 27.81 | Loses to Opus high on score, cost and time |
| Opus 5.5 xhigh | 57 | $6.05 | 15.8 | 79.62 | Frontier, one point over Fable medium for 59% more cost |
| Fable 5.2 high | 62 | $9.08 | 16.8 | 27.98 | Frontier |
| Sonnet 5.5 max | 55 | $10.02 | 33.0 | 260.44 | Loses to Opus xhigh on score, cost and time |
| Opus 5.5 max | 59 | $10.04 | 25.2 | 361.95 | Loses to Fable high on all three. Top of the pool without Fable |
| Fable 5.2 xhigh | 62 | $14.83 | 26.4 | 85.87 | Loses to Fable high on all three |
| Fable 5.2 max | 65 | $26.54 | 46.7 | 262.29 | Frontier, three points for 2.9 times Fable high |

The index and minutes columns were cross-checked against the [Anthropic creator page](https://artificialanalysis.ai/models/creators/anthropic), and the two max-effort costs against the Opus 5.5 and Sonnet 5.5 model pages. They matched.

## How the frontier was worked out

A setting is on the cost frontier when no cheaper setting scores as high. Sorted by cost, that is every row whose score beats all rows above it.

- All four models: Haiku low, medium, high, xhigh and max, then Sonnet high, Opus medium, Fable low, Fable medium, Opus xhigh, Fable high, Fable max.
- Without Fable: the same Haiku rows, then Sonnet high, Opus medium, Opus high, Opus xhigh, Opus max.
- On time instead of cost: Haiku low, Sonnet low, Opus low, Fable low, Fable medium, Opus xhigh, Fable high, Fable max.

The skill uses the frontier without Fable for delegated work, because of the plan rules below, and the Fable rows for work that needs Fable.

The steps up the frontier cost very different amounts per point. Opus medium to Fable low buys six points for $0.65. Fable medium to Fable high buys six points for $5.28. Fable high to Fable max buys three points for $17.46.

## Plan rules

Source: [Claude Fable models on your plan](https://support.claude.com/en/articles/15424964-claude-fable-models-on-your-plan).

- On Max, Ultra and premium seats, up to half of the weekly usage limit can go to Fable at no extra cost. The half is a share of the weekly limit and adds nothing to it.
- Fable models "draw from your plan's regular weekly usage limits and use them faster than other Claude models". The article gives no multiplier.
- Past the Fable share, the choices are usage credits at API rates or another model.
- On Pro and standard seats, Fable runs on usage credits from the first request. This skill assumes Max or Ultra.
- Fable 5.2, 5.1 and 5 are counted together.

The five-hour window on Max comes from a search summary of [claude.com/pricing](https://claude.com/pricing), which was not read directly, and from a limit message seen in a session on this account. The same summary says Ultra has no five-hour window.

Treating Artificial Analysis cost as the relative draw on the allowance is an assumption. Anthropic does not publish how each model is weighted.

## Anthropic's guidance by task

Source: [Which Claude model should you build with?](https://claude.dev/blog/which-claude-model-should-you-build-with/) (Addy Osmani, 2026-11-09) and [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model).

| Task | Anthropic's starting model and effort |
| --- | --- |
| Classification, routing, tagging, high-volume extraction | Haiku 5.5 at its default |
| Subagents that search files, read logs or summarize | Haiku 5.5 or Sonnet 5.5 at the model's default |
| Chat and interactive sessions | Sonnet 5.5 at low or medium |
| Scoped coding: bug fixes, feature iteration, spec-driven work | Sonnet 5.5 at medium, then high |
| Repeated agent tasks such as investigation, review or drafting | Sonnet 5.5 at medium |
| Everyday engineering, debugging, multi-PR feature work | Opus 5.5 at medium, then high |
| Computer use and vision-heavy work | Opus 5.5 at medium |
| Major refactors and migrations, architecture, leading many subagents | Fable 5.2 at medium, then high |
| Deep research, scientific or quantitative analysis | Fable 5.2 at medium, then high |
| Not sure yet | Opus 5.5 at medium |

Other points the skill relies on:

- Try effort before changing models. Past high, one more level can cost as much as a bigger model, so test the next model up at a lower effort.
- Fix order when a model falls short: self-verification, then one effort level, then the next model at lower effort.
- Keep small models on work where a mistake is cheap to spot. Keep code edits and judgment calls on the main model.
- From [Spending your effort](https://claude.dev/blog/spending-your-effort/) (Thariq Shihipar, 2026-09-25): effort mainly changes how much verification and edge-case testing the model does. It cuts missed-case failures and does not fix a wrong approach.
- From [Claude model and effort level in Claude Code](https://claude.com/blog/claude-model-and-effort-level-in-claude-code) (Lydia Hallie, 2026-07-07): smaller models do better with specific, step-by-step instructions. If the model tried and failed with the right context, use a larger model. If it did not try hard enough, raise effort.
- From the [Claude Code subagent docs](https://code.claude.com/docs/en/sub-agents): the Agent tool takes a `model` alias (`sonnet`, `opus`, `haiku`, `fable`) and an `effort` level per call. A subagent on a different model from the session does not get the session's effort.
- From [Optimizing for cost and intelligence](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence): a lead that hands work to cheaper models came out ahead only for work larger than one context window and for routine work with a long cost tail. For one chain of dependent steps, the lead's model alone at lower effort did better.

## Where the two sources disagree

Anthropic starts scoped coding on Sonnet at medium. Artificial Analysis scores Sonnet medium at 31, below Haiku xhigh (35) at a third of the cost, and puts Sonnet on the frontier only at high. The skill follows Artificial Analysis for effort, as its owner asked, and keeps Anthropic's task-to-model mapping.

Anthropic's own agentic numbers point the other way in places. In the cost guide, Opus 5.5 at low matched Sonnet 5.5 at its default on SWE-bench Pro for about 7% more per solved task, while the index puts Opus low (35) under Sonnet high (42). If delegated coding results disagree with the table, trust the results and tell the user.

## Refresh steps

1. Fetch the [leaderboard](https://artificialanalysis.ai/leaderboards/models) and list every Claude row with its index, cost per task and minutes per task.
2. Recompute the three frontiers as described above.
3. Re-read the plan article for changes to the Fable share.
4. Update the picks and the date in `SKILL.md`, and this file's table.
