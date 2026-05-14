# HITL handoff — worked example

Posted on `cogniarg/email#20` after Slice 1 (workspace skeleton + Cloudflare Worker bindings). The slice's agent work was code scaffolding; the remaining acceptance criteria needed Cloudflare account access and the dashboard.

````md
## Human handoff — Slice 1 remaining acceptance criteria

Three items are `ready-for-human` because they require Cloudflare account access (see `cogniarg/email#2`). Run these from the repo root unless noted.

### 1. Provision D1, R2, KV — replace placeholders in `apps/web/wrangler.jsonc`

```bash
bunx wrangler d1 create mail-cogni-ar
bunx wrangler r2 bucket create mail-cogni-ar-blobs
bunx wrangler kv namespace create KV
```

Take the IDs printed by each command and paste them over the `REPLACE_WITH_D1_ID` and `REPLACE_WITH_KV_NAMESPACE_ID` placeholders in `apps/web/wrangler.jsonc`.

Refs: `.claude/skills/wrangler/SKILL.md` — `d1 create` (line 383), `r2 bucket create` (line 337), `kv namespace create` (line 288).

### 2. Onboard `cogni.ar` to Email Service (both sides)

For inbound (Email Routing → our Worker's `email()` handler):

```bash
bunx wrangler email routing enable cogni.ar
bunx wrangler email routing dns get cogni.ar
```

For outbound (so the `EMAIL` binding works for replies):

```bash
bunx wrangler email sending enable cogni.ar
bunx wrangler email sending dns get cogni.ar
```

Refs: `.claude/skills/cloudflare-email-service/references/cli-and-mcp.md` — "Domain Setup".

### 3. Deploy the Worker and map `mail.cogni.ar`

```bash
cd apps/web
bunx wrangler deploy
```

Then in the Cloudflare dashboard: **Workers & Pages → mail-cogni-ar → Settings → Domains** add `mail.cogni.ar`.

Refs: `.claude/skills/wrangler/SKILL.md` — "Quick Reference: Core Commands".

### 4. Add the catch-all Email Routing rule

Dashboard: **Compute & AI → Email Service → Email Routing → Routing Rules** → add a catch-all rule **Send to a Worker** → `mail-cogni-ar`.

Refs: `.claude/skills/cloudflare-email-service/references/routing.md` — "Email Handler".

### Verification checklist

- [ ] `bunx wrangler deployments list` shows the new deployment
- [ ] `curl -sI https://mail.cogni.ar/ | head -1` → `HTTP/2 200`
- [ ] `bunx wrangler email routing dns get cogni.ar` reports records present
- [ ] `bunx wrangler email sending dns get cogni.ar` reports SPF + DKIM present
- [ ] Sending a test email to `anything@cogni.ar` shows up in `bunx wrangler tail mail-cogni-ar`

Once all five boxes are checked, this PR can be merged.
````

## Anti-patterns

These show what the skill is preventing.

### Bad: vague verification

```md
### Verification

- [ ] Things should work
- [ ] No errors
```

The reader cannot tell when they're done. Replace with observable commands (`curl -sI URL`, `bunx wrangler deployments list`, etc.).

### Bad: uncited commands

```md
### 1. Set up the domain

```bash
cf email-service domain add cogni.ar --type=both
```
```

No `Refs:` line — and the flag `--type=both` was hallucinated. The skill requires citing a local skill file or fetched doc, which would catch the mistake during drafting.

### Bad: narrative tone

```md
Now you'll want to head over to the Cloudflare dashboard. Once you're there, you should look for the Email Routing tab. After clicking it, you'll see a form...
```

Replace with: **Compute & AI → Email Service → Email Routing → Routing Rules** → add a catch-all rule → `mail-cogni-ar`.
