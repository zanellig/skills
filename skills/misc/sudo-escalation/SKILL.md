---
name: sudo-escalation
description: Use whenever a command needs root privileges — a `sudo` command, a write outside the user's home, a package install or removal, a "permission denied" failure — or the user asks what was changed with sudo or root.
license: MIT
---

# Sudo escalation

Run it under `pkexec` instead of `sudo`. The desktop's polkit agent prompts for the password on screen and the command runs as root. `pkexec` grants root without a TTY and sanitizes the environment, so pass any values the command depends on explicitly.

Run it through `scripts/root.sh` (next to this file), which calls `pkexec` and logs the change:

```sh
root.sh "<why, one line>" "<command that undoes it, or ->" pacman -Syu --noconfirm
```

Read-only previews change nothing, so call `pkexec` directly and skip the log:

```sh
pkexec pacman -Rns --print <pkgs>
root.sh "remove <pkgs>" "pacman -S <pkgs>" pacman -Rns --noconfirm <pkgs>  # after the user okays the list
```

When `pkexec` is missing, no polkit agent is running, or `root.sh` cannot write its log (it says so and runs nothing), hand the command back for the user to run in their own session, where sudo can prompt them directly. Their run is not logged, so say so when asked about changes:

> Run this yourself: `! sudo <cmd>`

## What changed with root?

Read the log, newest last:

```sh
tail -n 10 "${XDG_STATE_HOME:-$HOME/.local/state}/sudo-escalation/log.jsonl" | jq -c .
```

Fields: `ts` (UTC), `harness`, `session`, `cwd`, `cmd` (argv), `exit`, `why`, `undo`. Exit 126 or 127 usually means the prompt was dismissed and nothing ran.
