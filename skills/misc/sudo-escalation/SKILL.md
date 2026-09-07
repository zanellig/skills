---
name: sudo-escalation
description: Use whenever a command needs root privileges — a `sudo` command, a write outside the user's home, a package install or removal, or a "permission denied" failure.
---

# Sudo escalation

Run it under `pkexec` instead of `sudo`. The desktop's polkit agent prompts for the password on screen and the command runs as root:

```sh
pkexec pacman -Syu --noconfirm
```

`pkexec` grants root without a TTY.

```sh
pkexec pacman -Rns --print <pkgs>      # preview, changes nothing
pkexec pacman -Rns --noconfirm <pkgs>  # after the user okays the list
```

`pkexec` also sanitizes the environment, so pass any values the command depends on explicitly.

When `pkexec` is missing or no polkit agent is running, hand the command back for the user to run in their own session, where sudo can prompt them directly:

> Run this yourself: `! sudo <cmd>`
