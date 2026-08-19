# Deploying the Studio Worker

Two paths. **Use the dashboard path** unless you have a Workers-scoped API token
already in hand.

---

## Before either path: set the real spend ceiling

The Worker's `DAILY_CAP` is a courtesy brake, not a hard cap — its KV counters
are a non-atomic read-modify-write on an eventually-consistent store, so a burst
of concurrent requests overshoots it. **The only ceiling that actually holds is
an Anthropic-side spend limit.** Set it first.

1. Anthropic Console → **Settings → Workspaces → Create Workspace**.
   Name it something like `wallpaper-studio`.
2. On that workspace, set a **monthly spend limit**. `DAILY_CAP = 8` targets
   ~$2/day, so **$60/month** matches. Lower is fine; the Worker will just start
   returning errors sooner.
3. Create the API key **inside that workspace** — not in the default one. A key
   minted in the default workspace ignores the limit you just set.

Cost model behind those numbers (Claude Sonnet 5, $3/$15 per MTok; $2/$10
introductory through 2026-08-31):

| | worst-case request | at `DAILY_CAP = 8` |
|---|---|---|
| intro rates (to 2026-08-31) | ~$0.17 | ~$1.36/day |
| standard rates (from 2026-09-01) | ~$0.25 | ~$2.00/day |

A complete 64-mark wallpaper is roughly 3 requests; 256 marks is roughly 5.
So 8 requests/day is about two to three finished wallpapers.

---

## Path A — Cloudflare dashboard (recommended)

Everything happens in your browser. The API key goes Anthropic Console →
Cloudflare dashboard and never touches a local machine, a terminal, a file, or
a chat transcript. `worker.js` is a single self-contained file with no build
step, so it pastes straight in.

1. **Create the KV namespace.** Cloudflare dashboard → **Storage & Databases →
   KV → Create namespace**. Call it `wallpaper-studio-rl`.

2. **Create the Worker.** **Compute (Workers) → Create → Worker**. Name it
   `wallpaper-studio` and deploy the starter.

3. **Paste the code.** Open the Worker → **Edit code**. Select all, delete, and
   paste the full contents of `worker.js` from this directory. Before saving,
   check `ALLOWED_ORIGINS` at the top lists your domains. **Deploy.**

4. **Bind the KV namespace.** Worker → **Settings → Bindings → Add → KV
   namespace**. Variable name must be exactly `RL`. Select
   `wallpaper-studio-rl`.

5. **Add the secret.** Worker → **Settings → Variables and Secrets → Add**.
   Type **Secret** (not plaintext). Name it exactly `ANTHROPIC_API_KEY`. Paste
   the key from step 3 of the spend-limit section. Deploy.

6. **Copy the URL** — `https://wallpaper-studio.<subdomain>.workers.dev`.

7. **Point the site at it.** In `christmascherry.com/index.html`, set:

   ```js
   var CC_STUDIO_ENDPOINT = "https://wallpaper-studio.<subdomain>.workers.dev";
   ```

   Leave it empty or unset and the Studio falls back to bring-your-own-key,
   which is a safe default — nothing breaks if you never do this step.

8. **Verify.** Load the Studio on christmascherry.com and run one generation.
   Then check Cloudflare → the Worker → **Logs**, and Anthropic Console →
   **Usage**, to confirm exactly one request was billed.

Dashboard labels shift between Cloudflare redesigns. If a breadcrumb above
doesn't match, look for the equivalent by function — KV namespaces live under
storage, bindings and secrets under the Worker's own settings.

---

## Path B — wrangler CLI

Needs a **Workers-scoped** API token. The `CLOUDFLARE_API_TOKEN` exported from
`~/.zshrc` on the Mini is DNS/zone-scoped and will fail with *"Failed to
automatically retrieve account IDs"* — that error means wrong permissions, not
a missing login.

```bash
cd worker
wrangler kv namespace create RL        # paste the id into wrangler.toml
wrangler secret put ANTHROPIC_API_KEY  # reads from your terminal; never a file
wrangler deploy
```

`wrangler login` opens a browser **on the machine running wrangler**, so it is
not usable from a remote session where you can't see that machine's screen. Mint
a scoped token in the dashboard and pass it as `CLOUDFLARE_API_TOKEN` for the
deploy instead.
