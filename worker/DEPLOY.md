# Deploying the Studio Worker

Two paths. **Use the dashboard path** unless you have a Workers-scoped API token
already in hand. Every click-path below was verified against the live Cloudflare
and Anthropic documentation on 2026-08-19; both dashboards drift, so accept
minor label differences.

---

## Part 1 — set the real spend ceiling (Anthropic Console)

The Worker's `DAILY_CAP` is a courtesy brake, not a hard cap — its KV counters
are a non-atomic read-modify-write on an eventually-consistent store, so a burst
of concurrent requests overshoots it. **The only ceiling that actually holds is
a workspace spend limit in the Anthropic Console.** Set it first.

The Console is at **platform.claude.com** (console.anthropic.com redirects
there). Prerequisites: your account needs a payment method or credits under
**Settings → Billing**, and creating workspaces requires the Organization Admin
role.

1. **Create the workspace.** Settings → **Workspaces** → **Create workspace**.
   Name it `wallpaper-studio`.

2. **Cap it.** Open the workspace's details page → **Spend limits** tab (older
   UI shows this as a **Limits** tab with a **Change Limit** button). Set the
   **monthly** spend limit — **$50** comfortably covers the Worker's worst case
   (~$42/month if the daily cap maxed out every day). The workspace limit must
   be lower than the organization's limit. On the same tab, **Add notification**
   to get an email before the hard stop — the alert is configured separately
   from the cap.

3. **Mint the key inside that workspace.** Settings → **API keys** → **Create
   key** → choose the `wallpaper-studio` workspace in the scope selector (or:
   workspace details page → **API Keys** tab → **Create Key**). The key is
   shown in full exactly once — keep the tab open until it's pasted into
   Cloudflare in Part 2.

   ⚠️ Two facts make this step load-bearing: **the Default workspace cannot
   have limits set on it**, and **keys can never be moved between workspaces**.
   A key accidentally created in the Default workspace bypasses your cap
   entirely and must be deleted and re-created in the right workspace.

Enforcement when the cap is hit: API usage from that workspace pauses until the
next calendar month or until you raise the limit. Watch spend at
**platform.claude.com/usage** (breaks down per workspace).

### Cost model behind the numbers

Claude Sonnet 5 is **$2 / $10 per million input/output tokens** (the increase
to $3/$15 announced for 2026-09-01 was cancelled — $2/$10 is the standard
price). The Worker caps output at 16k tokens and prompts at 12k characters, so:

| | per worst-case request | at `DAILY_CAP = 8` |
|---|---|---|
| Sonnet 5, standard | ~$0.17 | ~$1.40/day → ~$42/month |

A complete 64-mark wallpaper is roughly 3 requests; 256 marks is roughly 5.
So 8 requests/day is about two to three finished wallpapers.

---

## Part 2 — deploy the Worker (Cloudflare dashboard)

Everything happens in your browser. The API key goes Anthropic Console →
Cloudflare dashboard and never touches a local machine, a terminal, a file, or
a chat transcript. `worker.js` is a single self-contained ES-module file with
no build step, so it pastes straight in. Workers Free is the default plan and
is plenty (100k requests/day; KV allows 1,000 writes/day and this uses ~16).

1. **Create the KV namespace first** (the binding form in step 4 picks from a
   dropdown of existing namespaces). Go to the **Workers KV** page — search
   "KV" in the dashboard, or use the deep link
   `dash.cloudflare.com/?to=/:account/workers/kv/namespaces` → **Create
   instance** → name it `wallpaper-studio-rl` → **Create**.

2. **Create the Worker.** **Workers & Pages** → **Create application** →
   **Start with Hello World!** → **Get started** → name it `wallpaper-studio`
   → **Deploy**. Pick the final name now: renaming a Worker changes its public
   URL (names: max 63 chars, letters/numbers/dashes, no leading or trailing
   dash).

3. **Paste the code.** Open the Worker → **Edit code**. Clear the file's
   contents and paste the full `worker.js` from this directory (or from
   `github.com/longpatrickm-cpu/wallpaper-studio` → `worker/worker.js`).
   Check `ALLOWED_ORIGINS` at the top lists your domains, then click
   **Deploy** — not **Save**. The down-arrow next to Deploy offers "Save",
   which creates a new version *without* deploying it; only Deploy makes it
   live.

4. **Bind the KV namespace.** Worker → **Settings → Bindings → Add → KV
   Namespace** (newer UI: a **Bindings** tab → **Add binding**). **Variable
   name must be exactly `RL`** — it's what the code reads as `env.RL` — then
   select `wallpaper-studio-rl` and deploy the binding.

5. **Add the secret.** Worker → **Settings → Variables and Secrets → Add**.
   Type: **Secret** (not plaintext — a secret is hidden from the dashboard
   after saving). Name exactly `ANTHROPIC_API_KEY`, paste the key from Part 1,
   then click **Deploy inside the drawer** — closing it without deploying
   discards the secret.

6. **Copy the URL** — `https://wallpaper-studio.<subdomain>.workers.dev`,
   where `<subdomain>` is shown under "Your subdomain" on the Workers & Pages
   page. If the Worker has no public URL, check the workers.dev route is
   enabled (Settings → Domains & Routes, or the newer **Domains** tab). A
   brand-new hostname can return 523 for a minute while DNS propagates.

7. **Point the site at it.** In `christmascherry.com/index.html`:

   ```js
   var CC_STUDIO_ENDPOINT = "https://wallpaper-studio.<subdomain>.workers.dev";
   ```

   Leave it `null` and the Studio falls back to bring-your-own-key — nothing
   breaks if you never do this step.

8. **Verify end to end.** Load the Studio on christmascherry.com and run one
   generation. Then check Cloudflare → the Worker → **Logs** and
   **platform.claude.com/usage** to confirm exactly one request billed to the
   `wallpaper-studio` workspace. (You can also open the KV namespace's **KV
   Pairs** tab and see the `ip:…` / `day:…` counters the Worker wrote.)

---

## Path B — wrangler CLI

Needs a **Workers-scoped** API token. The `CLOUDFLARE_API_TOKEN` exported from
`~/.zshrc` on the Mini is DNS/zone-scoped and fails with *"Failed to
automatically retrieve account IDs"* — that error means wrong permissions, not
a missing login.

```bash
cd worker
wrangler kv namespace create RL        # paste the id into wrangler.toml
wrangler secret put ANTHROPIC_API_KEY  # reads from your terminal; never a file
wrangler deploy
```

`wrangler login` opens a browser **on the machine running wrangler**, so it is
not usable from a remote session where you can't see that machine's screen.
Mint a scoped token in the dashboard and pass it as `CLOUDFLARE_API_TOKEN` for
the deploy instead.
