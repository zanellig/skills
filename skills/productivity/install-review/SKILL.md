---
name: install-review
description: "Vet a package, editor extension, MCP server, agent skill, plugin or install script before it is installed, and report a verdict without installing it. Use when asked \"is this safe to install\", to review before installing, or to audit a package, extension, MCP server or skill."
license: MIT
---

# Install review

Read an artifact's code and provenance without running it, then give a verdict. The review is read-only: it reports and stops, and installing needs a separate yes from the user.

## 1. Pin

Name the artifact by exact version, plus the commit or checksum when the registry shows one. Resolve "latest" now. The verdict covers only this pin.

## 2. Fetch

Download into a new, empty `mktemp -d` directory and keep it the only thing you write there. Use the fetch-only form of the tool:

- npm: `npm pack <name>@<version> --ignore-scripts`
- Python: in `https://pypi.org/pypi/<name>/<version>/json`, take the `urls` entry whose `packagetype` is `sdist`, then `curl -o` its `url` and check `digests.sha256` (pip prepares an sdist's metadata, which runs its build code)
- Git source (skills, MCP servers, PKGBUILD, install scripts): `git clone --depth 1 --branch <tag> <url>`, or with no tag `git init`, then `git fetch --depth 1 <url> <commit>` and `git checkout FETCH_HEAD`; confirm `git rev-parse HEAD` is the pinned commit
- Extension: download the `.vsix` and unzip it
- Shell installer: `curl -o` the script, then read it

Never run, import, build or `source` anything you fetched, and never run an interpreter from inside the directory. Delete the directory at the end, also when the review fails.

## 3. Read

Cover every item; mark each one "read", "absent" or "not checked":

- **Runs at install or first launch:** lifecycle scripts (`preinstall`, `postinstall`, `prepare`), `setup.py`, build hooks, PKGBUILD, shell installer steps, extension activation events, MCP server start command.
- **Touches:** filesystem reads and writes outside its own directory, environment variables and credentials it reads, network destinations, spawned processes, obfuscated or minified code that hides the above, and the permissions or tool grants it requests.
- **Dependencies:** new or unpinned transitive installs, and git or URL dependencies.

## 4. Provenance

Check release age, maintainer or publisher changes, download count, and whether the published artifact matches its source repo at the tagged commit (diff the packed tarball against the clone). A mismatch, a missing repo or a fresh maintainer change is evidence against.

## 5. Release-age limit

The user's minimum release age lives in their bunfig: `./bunfig.toml` in the project, else `~/.bunfig.toml` (or `$XDG_CONFIG_HOME/.bunfig.toml`). Read `install.minimumReleaseAge` (seconds) from it and do not hard-code a number. If it is unset everywhere, say so and skip this step.

Apply the same age to the package manager the install will use, in its own unit and setting (pnpm `minimumReleaseAge`, uv `exclude-newer`, npm `--before`). Compare the pinned release's publish time with the limit. A release newer than the limit is **too new**: report it, and name the newest version that passes.

## 6. Report, then stop

- **Verdict**, one line: `install`, `install with conditions` (list them), or `don't install`.
- **Evidence:** the findings behind it, each with a file and line.
- **Not checked:** every step 3 item marked "not checked", plus anything you could not verify (closed-source binaries, network behaviour you did not observe).

Then wait for the user's yes.
