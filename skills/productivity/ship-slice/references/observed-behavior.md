# What Codex actually did

## Sweep

On 2026-09-24, every PR on `user:zanellig` or `org:cogniarg` matching `commenter:chatgpt-codex-connector[bot]` or `reviewed-by:chatgpt-codex-connector[bot]`: 99 PRs from 2026-03-13 to 2026-09-24. For each, the issue comments, reviews, review comments, PR reactions, and the reactions on every human comment containing `@codex`. `cogniarg/*` links are private to that org.

## Response shapes

| Shape | Count | Names a commit |
| --- | --- | --- |
| Review (`### 💡 Codex Review` + inline findings) | 119 | Yes, `**Reviewed commit:** \`<sha>\`` |
| Empty-body review holding one in-thread reply | 10 | No |
| Issue comment `Codex Review: Didn't find any major issues.` + sign-off | 24 | Yes |
| Issue comment: usage-limit notice | 46 | No |
| Issue comment: missing-environment notice | 3 | No |
| Issue comment: task summary | 1 | No |
| 👍 on the PR | 29 PRs | No |

Every review or issue comment that answered a review request named its commit. Everything else without the marker was a notice, a task, or a thread reply.

## Notices

Usage limit, 46 times, e.g. [skills#10](https://github.com/zanellig/skills/pull/10#issuecomment-5761633678):

> You have reached your Codex usage limits for code reviews. You can see your limits in the Codex usage dashboard.

Missing environment, 3 times, e.g. [skills#11](https://github.com/zanellig/skills/pull/11#issuecomment-5765331231) and [sampedro#50](https://github.com/cogniarg/sampedro/pull/50#issuecomment-4550017533):

> To use Codex here, create an environment for this repo.

On [email#37](https://github.com/cogniarg/email/pull/37) a request at 18:30:10 got the usage-limit notice 13 seconds later, and the push of `2346f98` at 18:48 got it again at 18:50. A notice repeats until the limit clears.

## Task summaries

A task summary starts `### Summary`, lists the changes Codex made, has a **Testing** section, and ends with `View task →`. It has no `Reviewed commit:`.

**PR body mention.** [skills#12](https://github.com/zanellig/skills/pull/12) opened at 16:20:14 with a body containing ``posts one pinned `@codex review` ``, inside a code span. No human comment came before Codex's [task summary](https://github.com/zanellig/skills/pull/12#issuecomment-5817959640) at 16:22:39, which reported a commit and "created the follow-up PR metadata". No review came. The body was edited at 16:24:02 to drop the `@`, and the pinned request at 16:24:08 started round 1. The PR's edit history (`userContentEdits` in GraphQL) shows both body versions.

**Thread mentions.** `@codex` with anything but `review` in a review thread gets an answer or a task in that thread:

- [skills#11](https://github.com/zanellig/skills/pull/11#discussion_r4065454962): a "Fixed in b008e36" reply that said "escalating to @codex only if the finding returns" started a task. A mention mid-sentence counts.
- [skills#11](https://github.com/zanellig/skills/pull/11#discussion_r4065942129) and [pagos#10](https://github.com/cogniarg/pagos/pull/10#discussion_r3487403791): requests to change code got task summaries.
- [email#29](https://github.com/cogniarg/email/pull/29#discussion_r3432766677) and [deployment-command-centre#23](https://github.com/zanellig/deployment-command-centre/pull/23#discussion_r3669710610): questions got answers.
- [cogniar-growth-engine#29](https://github.com/cogniarg/cogniar-growth-engine/pull/29#discussion_r3888145785) and [personal-page#14](https://github.com/zanellig/personal-page/pull/14#discussion_r3927722462): the repo had no environment, so the reply was the environment notice. Thread mentions run as tasks.

## Clean rounds

24 clean rounds, each an issue comment that opens `Codex Review: Didn't find any major issues.` and names the commit, e.g. [email#90](https://github.com/cogniarg/email/pull/90#issuecomment-5817405570):

> Codex Review: Didn't find any major issues. Another round soon, please!
>
> **Reviewed commit:** `1996891037`

The sign-off after the first sentence varies (12 variants: `:+1:`, `Swish!`, `:rocket:`, `Bravo.`, …), so match only the prefix.

Codex has 👍 on 29 PRs. On 20 the clean comment came 0–4 seconds after the 👍 (one outlier, Web-de-pagos-para-aseguradora#36, came 139 seconds before it). The other 9 got the 👍 and no comment. No 👍 arrived alongside a findings review; the nearest findings reviews came 5–8 minutes earlier, in the round before a fix push. The 👍 names no commit, and GitHub keeps one per user and type, so it cannot mark a later clean round.

[skills#13](https://github.com/zanellig/skills/pull/13), opened 2026-09-24 at 20:42:26 with Smart detect:

| Time (UTC) | Event |
| --- | --- |
| 20:42:33 | 👀 on the PR |
| 20:45:26 | 👀 gone, 👍 on the PR; no comment and no review |
| 21:08:27 | `f8dd6f6` pushed |
| 21:12:07 | [Review of `f8dd6f6`](https://github.com/zanellig/skills/pull/13#pullrequestreview-5310279163) with one P1 finding |
| 21:12:57 | The 20:45 👍 is gone from the PR |

Codex's task page for that review read "Worked for 2m 47s" and "Codex didn't flag any issues." So a 👍 alone was a clean review, as the footer promises. Codex also cleared that 👍 once the next round began, so a later clean round could add a fresh one.

## A push activates a review

Repo trigger: Smart detect. On [skills#11](https://github.com/zanellig/skills/pull/11), `ab75e86` was committed at 15:34:53 and pushed. The only human activity afterwards was a plain inline reply at 15:36:36 with no `@codex`. Codex [reviewed `ab75e86`](https://github.com/zanellig/skills/pull/11#pullrequestreview-5306706262) at 15:43:14 with five findings.

## Eyes reaction

Of 87 human comments containing `@codex`, Codex's 👀 remains on 2, and no 👀 remains on any PR. So the bot usually removes 👀 when it responds. It removed the PR-level 👀 on [skills#13](#clean-rounds) too, replacing it with 👍. The two leftovers:

- [pagos#28](https://github.com/cogniarg/pagos/pull/28#issuecomment-4987829042): a request pinned `62250c9` at 03:22:33. Three minutes later `2de567c` was pushed and [re-requested](https://github.com/cogniarg/pagos/pull/28#issuecomment-4987843030). The next review, at 03:31, read `2de567c`, and `62250c9` was never reviewed. The dropped request kept its 👀.
- [sampedro#44](https://github.com/cogniarg/sampedro/pull/44#issuecomment-4526879496): answered by a review 8 minutes later, yet the 👀 stayed.

The skill's rule still holds either way: an 👀 that outlives a full wait is stale.

## Thread replies

64 plain replies (no `@codex`) in Codex-opened threads got 0 bot replies. Of 11 thread replies containing `@codex`, 10 got a bot reply; [Finar#2](https://github.com/zanellig/Finar/pull/2#discussion_r2930488336), from March, got none.

Nothing here shows whether a thread mention bills code-review usage or task usage. The environment notices suggest tasks.

## Stale and duplicate reviews

[email#37](https://github.com/cogniarg/email/pull/37):

| Time (UTC) | Event |
| --- | --- |
| 18:03:54 | `f028737` committed |
| 18:05:38 | `@codex review` |
| 18:14:59 | [Review of `f028737`](https://github.com/cogniarg/email/pull/37#pullrequestreview-4627480442) |
| 18:19:40 | `4077ef0` committed (fixes) |
| 18:19:48 | [`@codex review the latest fixes: …`](https://github.com/cogniarg/email/pull/37#issuecomment-4878575561), no SHA |
| 18:28:54 | [Second review of `f028737`](https://github.com/cogniarg/email/pull/37#pullrequestreview-4627521595), the stale commit |

The unpinned request got a duplicate review of the old commit, and none of the fixes were reviewed. On pagos#28 above, pinned requests got reviews of the head at request time: `2de567c` for the 03:25 request and `5ade630` for the 03:35 one.

## Review latency

Measured on 2026-09-24 over 128 Codex reviews from the same owners (up to 40 PRs per repo): minutes from the reviewed commit's committer date to the review's `submitted_at`. Commit time comes before push time, so each figure overstates the wait slightly.

| Commit to review | Reviews |
| --- | --- |
| ≤ 5 min | 20 |
| 6–10 min | 39 |
| 11–15 min | 26 |
| 16–30 min | 17 |
| 31–60 min | 2 |
| > 60 min | 24 |

Median 11 minutes. The > 60 min group is mostly pushes Codex skipped and reviewed later on request. Of the other 104, 85 (82%) answered within 15 minutes and 102 (98%) within 30. The waiter's 15-minute default follows from this. Its cost is a duplicate review when a slow review lands after the pinned request. Pinned requests on skills#12 came back in 4–6 minutes.
