---
name: session-audit
description: Audit Claude Code and Codex history for work patterns, repeated instructions, missed skills and new skill candidates, and end with an HTML report.
disable-model-invocation: true
license: MIT
---

# Session audit

Read the user's Claude Code and Codex history in chunks through delegates, merge their findings, and publish one HTML report. The orchestrator (you) works from numbers and screened findings, never from raw transcripts.

**Orchestrator hygiene.** Raw session text stays in `out/` and `digests/`, and only delegates open those. Keep transcript text out of your own context: open no transcript, digest or `out/` file, and print none of it. A safeguard classifier once ended an orchestrator thread that had read security-themed sessions. Your inputs are `stats.json`, `status.json`, `check_cites.py` output and the findings files.

Below, `<skill>` is this skill's directory. The scripts run with `python3 -I`.

## 1. Scope

Get from the user: the date range, the earlier review notes to compare against (ask if none are given), and any health-check prompts that differ from the defaults ("Reply only with Hi", "Respondé únicamente DISPONIBLE"). Create the audit directory `<audit>` owner-only (`mkdir -m 700`, default `~/.agents/session-reviews/audit-<today>`). Done when all four are fixed.

## 2. Extract

```sh
python3 -I <skill>/scripts/extract.py <audit>/out --since YYYY-MM-DD --until YYYY-MM-DD [--health-check PREFIX ...] [--self-prompt PREFIX ...]
```

Pass `--self-prompt` with the opening words of this thread's own prompt. `--health-check` replaces the default prompts.

**History homes.** The script finds homes by content: a Claude Code home holds `projects/*/*.jsonl`, a Codex home holds `sessions/YYYY/MM/DD/rollout-*.jsonl`. It reads `$CLAUDE_CONFIG_DIR`, `$CODEX_HOME`, and every such dir up to two levels under the hidden dirs of `$HOME` and the XDG config and data dirs, one per realpath. Repeat `--claude-home DIR` or `--codex-home DIR` to read only those homes for that harness. It prints each home with its session count and date range in the audited range; a home with 0 sessions adds nothing. Show the user that list and confirm it before step 3.

The script does three things that keep the counts honest:

- **Exclusions.** It drops subagent transcripts, health checks, greeting-only sessions and the audit's own threads (first prompt starts with `# Session audit brief`, `/session-audit` or a `--self-prompt` prefix, or names `<audit>/out`).
- **Forks.** A resumed or forked session replays its parent under the same turn ids (Claude Code event `uuid` or `forkedFrom.messageUuid`, Codex `turn_id`). Within one source and project, the script keeps the earliest session and folds in each later one's unique tail (turns, tools, skills, commands, models, end time), so one conversation counts once. Sessions that only share opening words stay separate, as do Codex rollouts without turn ids.
- **Machine turns.** It marks user-channel turns that the machine wrote (CI and review-bot events, agent-to-agent messages, harness tags, headless prompts) with a label. They stay visible as `M[label]` and stay out of `n_user`.

Done when the user has confirmed the homes and the printed kind counts are plausible: `interactive` is the bulk, and `healthcheck`, `greeting`, `self` and `fork` are small. A greeting or ping that survived as `interactive` means the exclusion rules need a new prefix; rerun with it.

## 3. Stats and digests

```sh
python3 -I <skill>/scripts/stats.py <audit>/out
python3 -I <skill>/scripts/digest.py <audit>/out <audit>/digests --chunk-chars 150000
```

`stats.json` holds counts only. `digest.py` refuses a `digests/` or `findings/` dir that already holds files, since new S-ids would let old findings pass; after changing the range or exclusions, start a fresh `<audit>`. It writes chunks of about 150K characters in time order, plus `session_index.json` and `status.json` (every chunk `pending`). **Security-themed sessions** are found with the script's regex over each session's rendered text, not its first prompt. They go only into `s<NN>-gpt.md` chunks. Done when every chunk printed has a file and an entry in `status.json`.

## 4. Delegate one chunk each

Send each chunk to a delegate with `references/brief.md`, filled in: `{AUDIT_DIR}`, `{CHUNK}` (the chunk name without `.md`), `{DATE_RANGE}`, `{SKILLS_DIRS}` (`~/.agents/skills` and `~/.claude/skills`), `{RULES_FILES}` (the user's global `CLAUDE.md` and Codex `AGENTS.md`), `{EARLIER_REVIEWS}`. Keep the brief's first line, since it marks the delegate's thread as the audit's own.

| Chunk name | Delegate |
| --- | --- |
| `*-claude` | Claude Sonnet, high effort |
| `*-gpt` | GPT Sol, high effort |

Claude delegates run Sonnet because Haiku's 100K auto-compact loops on chunks this size. The `s<NN>-gpt` chunks reach GPT delegates only, and their findings describe behaviour at the level of "ran a security review on project X". Check the harness's delegation tool and its model list before the first launch. If Sonnet or Sol is unavailable, tell the user and wait for their choice.

## 5. Track status

`<audit>/digests/status.json` maps each chunk to `pending`, `done` or `failed`. Set `failed` when a delegate stops on a usage limit or error. After a limit resets, relaunch only chunks that are not `done`. `check_cites.py` marks a chunk `done` whenever its findings file exists, so a findings file on disk outranks a stale failure notice. Done when `check_cites.py` prints `relaunch: none`.

## 6. Check citations

```sh
python3 -I <skill>/scripts/check_cites.py <audit>
```

It lists every S-id that is absent from its chunk, with file and line. Delete each invented id from the findings file, and delete any claim left without a valid S-id. Rerun until it exits 0.

## 7. Merge and compare

Merge the findings into one set of sections A–F (the brief's headings), keeping counts and S-ids. Each delegate tagged its findings `[confirms]`, `[contradicts]` or `[extends]` against the earlier reviews. Carry the tags through, and give the contradictions their own short list. Done when every merged finding has a tag, an S-id and an origin findings file.

## 8. Report

Load the `dataviz` skill (bundled with Claude Code; where it is absent, draw the charts as inline SVG with labelled axes), then write `<audit>/report.html` from `stats.json` and the merged findings: the charts first (sessions per month, start hour, skills used against skills read, delegation), then sections A–F, then the comparison with earlier reviews. Finish with:

```sh
python3 -I <skill>/scripts/check_cites.py <audit> --report <audit>/report.html
```

Done when it exits 0, so every S-id in the report traces to a findings file. Give the user the report path and the three biggest findings; leave the raw `out/` and `digests/` in place and say they hold raw session text.
