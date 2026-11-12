---
name: claude-model-choice
description: Which Claude model and effort level to give a task, picked from the Artificial Analysis cost frontier for a Claude subscription. Use before setting a model or effort on a subagent, delegate or workflow agent, when pinning `model:` or `effort:` in a skill or agent file, or when the user asks which Claude model to use.
license: MIT
---

# Claude model choice

Pick the model and effort for work you hand to another Claude: a subagent, a delegate, a workflow agent, or a `model:` / `effort:` pin in a skill or agent file. This reference covers which model to use once you delegate. Whether to delegate is a separate decision, and a model or effort the user names always wins.

## The budget

The work runs on a Claude subscription (Max or Ultra), so the budget is the weekly allowance. Nothing is billed per token until it runs out.

- Fable can spend at most half of the weekly allowance and draws it down faster than the other models. Past that half, Fable bills at API rates as usage credits.
- Whatever Fable leaves, at least half, can only go to Opus, Sonnet and Haiku. When you lead on Fable, a subagent on one of those spends allowance you cannot use yourself.
- On Max, a five-hour window also caps bursts on every model. Parallel subagents reach it first.
- Anthropic publishes no per-model draw rate. Use the Cost column below as the relative draw.

Fable is the scarce half. Keep it for the lead and for delegated work that needs it, and put the rest on Opus, Sonnet and Haiku.

## Picks

Each row sits on the Artificial Analysis frontier for its pool: within Fable, or within the other three models, no setting scores higher for less. Index is the Intelligence Index score, Cost is dollars per index task at API prices, and Minutes is time per index task. Read Cost and Minutes as ratios between rows.

| Work | `model` | `effort` | Index | Cost | Minutes |
| --- | --- | --- | --- | --- | --- |
| Find files, search code, run a command and report | `haiku` | `medium` | 25 | $0.09 | 4.0 |
| Read logs or docs, then summarize, classify or extract | `haiku` | `xhigh` | 35 | $0.25 | 9.6 |
| Scoped code against a clear spec, or a repeated agent task | `sonnet` | `high` | 42 | $1.64 | 7.0 |
| Everyday engineering, debugging, review, computer use | `opus` | `medium` | 48 | $2.45 | 7.2 |
| The same, where edge cases or verification decide the result | `opus` | `high` | 52 | $3.46 | 9.5 |
| A hard problem you want kept off the Fable half | `opus` | `xhigh` | 57 | $6.05 | 15.8 |
| Architecture, a major refactor or migration, deep research, a long unattended run | `fable` | `medium` | 56 | $3.80 | 7.7 |
| The same, after `medium` falls short | `fable` | `high` | 62 | $9.08 | 16.8 |

Pass both `model` and `effort` on the call. A subagent on a different model from yours ignores the session's effort and runs at that model's default.

Two picks sit off the cost frontier and earn their place another way:

- When someone is waiting on the reply, use `sonnet` at `low` (26, $0.51, 2.5 minutes) or `opus` at `low` (35, $0.98, 3.0 minutes). Haiku reaches the same scores for less, but takes about three times as long.
- For a short second opinion, `fable` at `low` (54, $3.10, 6.2 minutes) beats `opus` at `high` on score, cost and time. It still spends the Fable half.

## Settings that lose

- `sonnet` at `xhigh` or `max`, and `fable` at `xhigh`. Another setting scores at least as high for less cost and less time.
- `opus` at `max` (59, $10.04, 25.2 minutes) loses to `fable` at `high` on all three. Use it only when the Fable half is spent and `opus` at `xhigh` fell short.
- `fable` at `max` (65, $26.54, 46.7 minutes) adds three points for about three times the cost of `high`. Use it only when the user asks for it.
- `haiku` at `max` adds one point over `xhigh` for half again the wait.

## When a pick falls short

Work through Anthropic's order, one step at a time:

1. Give the agent a way to check its own work: a test, a build, a script.
2. Raise effort to the next row for that model. Effort buys verification and edge cases.
3. Move up a model and start it at a lower effort. A wrong approach needs the bigger model, and more effort will not supply it.

## Briefing

Give Haiku work where a wrong answer is cheap to spot. Send code edits to Sonnet or above, and keep judgment calls with the lead. Smaller models do better with specific, step-by-step briefs than with open-ended ones.

## Outside this table

Application code that calls the Claude API is billed per token, so the allowance reasoning above does not apply to it. Follow the application's own requirements there.

## Freshness

The numbers are from Artificial Analysis Intelligence Index v5.0.1, read on 2026-11-12. The full table, the frontier working, the sources and the refresh steps are in [references/evidence.md](references/evidence.md). Read it when a model here is no longer the newest of its family, when your session offers a model missing from the table, or before quoting a number to the user. When the table is stale, tell the user.
