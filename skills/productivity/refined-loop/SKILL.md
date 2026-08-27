---
name: refined-loop
description: Schedule a prompt or slash command to run on a repeating schedule — every N minutes/hours/days, or at a fixed time of day. Use when the user wants a recurring task, a poll for status, or something run repeatedly on an interval or at a set hour ("check the deploy every 5 minutes", "run X every morning at 6"). Do NOT invoke for one-off tasks.
argument-hint: "[interval or time] <prompt>"
---

# refined-loop — schedule a recurring prompt

Turn the request into a **systemd user timer** that runs the prompt headlessly on schedule.
Every job this skill creates follows the same layout.

## Parse

Split the input into a schedule and a prompt:

- Leading interval token — `5m`, `2h`, `1d` — rest is the prompt.
- Trailing clause — `every 20m`, `every 5 minutes`, `every 2 hours` — strip it from the prompt.
  Only when a time expression follows "every"; `check every PR` has no schedule.
- Time of day — `at 5am`, `every day at 06:30`, `weekdays at 9` — strip it from the prompt.
- Nothing matched → ask the user for an interval before proceeding. Suggest 10 minutes as a default.

Empty prompt → show `refined-loop [interval or time] <prompt>` and stop.

Slash commands pass through verbatim as the prompt.

Pick a short kebab-case `<slug>` from the prompt; it names the units.

## Schedule

Express it as `OnCalendar=` whenever the user named a wall-clock time — that is the point of
their request. Use `OnUnitActiveSec=` only for pure "every N from now"
intervals. Verify the expression before writing it:

```sh
systemd-analyze calendar 'Mon..Fri *-*-* 09:00:00'
```

Set `Persistent=true` only if a missed run should still happen late. When the value of the job
is *when* it fires, leave it off — a catch-up run at the wrong hour is worse than a skipped one.

You should ask the user if they want to persist missed runs when the schedule is a wall-clock time, and explain the implications.

## Standard structure

`~/.config/systemd/user/loop-<slug>.service`

```ini
[Unit]
Description=<one line: what this run is for>

[Service]
Type=oneshot
WorkingDirectory=<repo the prompt concerns, or /home/developer>
# Inherited ANTHROPIC_API_KEY would bill the API account; unset it so the
# subscription credentials in ~/.claude are used instead.
UnsetEnvironment=ANTHROPIC_API_KEY
ExecStart=/home/developer/.local/bin/claude --model sonnet -p "<prompt>"
TimeoutStartSec=infinity
```

`~/.config/systemd/user/loop-<slug>.timer`

```ini
[Unit]
Description=<cadence, in words>

[Timer]
OnCalendar=<expression>
AccuracySec=1min

[Install]
WantedBy=timers.target
```

Defaults worth keeping: `sonnet` is enough for polling and status prompts — reach for `opus`
only when the scheduled work is genuinely hard.

**Never leave `TimeoutStartSec` out to mean "no limit".** Omitting it applies
`DefaultTimeoutStartUSec`, which in most hosts is set to 15s — an agent doing real work gets killed
mid-task, and the journal shows a timeout rather than the model's answer. Keep
`TimeoutStartSec=infinity` for anything non-trivial. Set a concrete cap (`5min`) for a
job that is genuinely a ping and should page you if it hangs.

With no timeout, guard against a wedged run instead of a slow one: `systemd` will not start a
service that is still active, so a job that outlives its own interval causes the next trigger
to be skipped, not stacked. If that matters, say so when confirming.

## Install and prove it

```sh
systemctl --user daemon-reload
systemctl --user enable --now loop-<slug>.timer
systemctl --user start loop-<slug>.service      # one real run
systemctl --user show loop-<slug>.service -p Result -p ExecMainStatus
journalctl --user -u loop-<slug>.service -n 20 --no-pager -o cat
```

A job is not done until a real run has exited 0 and the journal shows the model's output.
Report that output. If it failed, fix the unit — do not hand over a timer that has never run.

When the schedule exists precisely to hit a wall-clock moment, say plainly that
the test run also fired the job early, so the user knows.

## Confirm

State the cadence in words, the next fire time from `systemctl --user list-timers 'loop-*'`,
and how to stop it:

```sh
systemctl --user disable --now loop-<slug>.timer
rm ~/.config/systemd/user/loop-<slug>.{service,timer}
```

Timers persist until disabled — there is no expiry. If the host sleeps through the scheduled
time the run is skipped, so mention that for anything scheduled outside working hours.

## Input

$ARGUMENTS
