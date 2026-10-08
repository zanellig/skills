# Workflow details

## Review-trigger setup

The settings are On PR open, On every push, and Smart detect. They apply per account with per-repo overrides; no API exposes the selection.

For a missing or unscoped setting, ask the user which setting applies and whether it is an account setting or a repo override. For a recorded account setting belonging to another login, ask which setting applies to the current account.

Record the answer in `AGENTS.md`, or `CLAUDE.md` if there is no `AGENTS.md`. Use a `Codex Code review settings` heading one level below an existing code-review section, otherwise at `##`. Include the scope as `(repo override)` or `(account setting for @<login>)`:

```markdown
## Codex Code review settings

Review trigger: Smart detect (account setting for @<login>).
```

Tell the user only when you added the line. An applicable recorded setting passes silently.

## Blocking wait in Codex

A Codex `exec` cell calls nested tools without returning to the model, so one cell can hold the whole wait. `exec_command` yields after at most 30 seconds. `write_stdin` with empty `chars` returns when the process exits or when `background_terminal_max_timeout` elapses (default 300000 ms, set in `config.toml`). Loop on it until it reports an exit code:

```js
// @exec: {"yield_time_ms": 1200000, "max_output_tokens": 20000}
let r = await tools.exec_command({cmd: `REQUIRE_COMMIT=<0|1> <skill-dir>/scripts/wait-for-codex.sh <n> "<since>"`, yield_time_ms: 30000});
let out = r.output;
while (r.exit_code == null) {
  r = await tools.write_stdin({session_id: r.session_id, chars: "", yield_time_ms: 960000, max_output_tokens: 20000});
  out += r.output;
}
text(`exit ${r.exit_code}\n${out}`);
```

Without code mode, make the same `write_stdin` call directly until it reports an exit code. A `background_terminal_max_timeout` of 960000 covers the waiter's default 15 polls in about one call.

## Delegated validation

Assign one subagent per behavior-dependent claim to use `diagnosing-bugs` for validation only, returning the reproduction, whether it went red, and a verdict. Code-evident findings stay with the main agent. If the skill is installed neither in the repo nor globally, recommend installing Matt Pocock's skill and provide the command for the user's skill package manager.

## Thread operations

Reviews come from `chatgpt-codex-connector[bot]`; `gh pr view` JSON shows `chatgpt-codex-connector`.

Reply using the finding's comment id from the waiter:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments/<id>/replies \
  -f body="Fixed in <sha>: <what changed>"
```

Use the substantive reason instead for declined findings, or the issue link for filed findings. Resolve bot-opened threads with the GraphQL `resolveReviewThread` mutation and their thread ids. This query lists unresolved thread ids, authors, and paths:

```bash
gh api graphql --paginate \
  -f query='query($o:String!,$r:String!,$n:Int!,$endCursor:String){repository(owner:$o,name:$r){pullRequest(number:$n){
    reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{id isResolved path comments(first:1){nodes{author{login}}}}}}}}' \
  -f o=<owner> -f r=<repo> -F n=<n> \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false) | "\(.id) \(.comments.nodes[0].author.login) \(.path)"'
```
