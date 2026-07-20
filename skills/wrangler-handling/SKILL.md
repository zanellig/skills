---
name: wrangler-handling
description: Load this skill whenever needing to use `wrangler` or when handling Cloudflare configuration or deployment issues. Use when the user says "wrangler", "Cloudflare", "deploy", "configuration", or when addressing wrangler/Cloudflare issues on a PR.
---

You have a full-access Cloudflare account with `wrangler` installed and configured. You can use `wrangler` to manage all Cloudflare services.

## Cloudflare Token Handling

- NEVER read, print, copy, edit, source, grep, cat, inspect, chmod, chown, or
  otherwise access `/home/developer/cogniar/CF.env` directly.
- NEVER ask the user to reveal the contents of `/home/developer/cogniar/CF.env` or any Cloudflare token.
- When Cloudflare auth is needed, use `wrangler`, `npx wrangler`, or `bunx wrangler`; local shell wrappers route these through the credential helper.
- If Wrangler auth fails, report the helper error and ask the user to fix the helper instead of bypassing it.
- Do not run commands intended to reveal `CLOUDFLARE_API_TOKEN`, `CF_API_TOKEN`, or `CLOUDFLARE_ACCOUNT_ID`.