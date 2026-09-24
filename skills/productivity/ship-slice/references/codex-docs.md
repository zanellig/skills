# What the docs state

Sources, read 2026-09-24:

- OpenAI, [Review GitHub pull requests with Codex](https://learn.chatgpt.com/docs/third-party/github) (formerly `developers.openai.com/codex/integrations/github`, which now redirects there).
- The "About Codex in GitHub" footer on every Codex review. All 143 footers in the [sweep](observed-behavior.md#sweep) carry the same text, from 2026-03-13 to 2026-09-24.

## Bot identity

The docs' screenshot shows reviews posted by `chatgpt-codex-connector` with a `bot` badge. The REST API names it `chatgpt-codex-connector[bot]`.

## Review triggers

The docs describe one switch: "turn on **Automatic reviews** in Codex settings. Codex will post a review whenever someone opens a new PR for review, without needing an `@codex review` comment." Their troubleshooting section adds: "check that you turned on Automatic reviews and that the pull request event matches your review trigger settings." They never name the settings.

The footer lists the events:

> Reviews are triggered when you
> - Open a pull request for review
> - Mark a draft as ready
> - Comment "@codex review".
>
> If Codex has suggestions, it will comment; otherwise it will react with 👍.

The footer never mentions pushes, yet a push alone activated a review on [skills#11](observed-behavior.md#a-push-activates-a-review). It reads as fixed text rather than the repo's actual trigger.

The three setting names (**On PR open**, **On every push**, **Smart detect**), the account-level setting with its per-repo override, and the claim that no API exposes the setting all come from the Codex settings page at `chatgpt.com/codex/settings/code-review`. No public doc covers them.

## Mentions

> In a pull request comment, mention `@codex review`. Wait for Codex to react (👀) and post a review.

> If you mention `@codex` in a comment with anything other than `review`, Codex starts a cloud chat using your pull request as context.

> After Codex posts a review, you can ask it to fix issues in the same pull request by leaving another comment: `@codex fix the P1 issue`. Codex starts a cloud chat with the pull request as context and can push a fix back to the branch when it has permission to do so.

The docs mention only comments. They say nothing about a mention in the PR body; [skills#12](observed-behavior.md#task-summaries) shows what one does.

## Reactions

- 👀: "Wait for Codex to react (👀) and post a review." The docs don't say whether the reaction is removed afterwards.
- 👍: the settings page reads "Codex automatically suggests improvements (or reacts with 👍)", and the footer reads "otherwise it will react with 👍."

## Severity

> In GitHub, Codex flags only P0 and P1 issues so review comments stay focused on high-priority risks.

In the sweep, findings also carry P2 badges, e.g. on skills#11 and skills#12.

## GitHub

A user holds at most one reaction of each type on an issue or PR. The [reactions API](https://docs.github.com/en/rest/reactions/reactions#create-reaction-for-an-issue) returns the existing reaction (`200`) instead of adding a second one.
