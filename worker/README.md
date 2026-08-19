# Keyless mode

Optional. Without it the Studio works fine — visitors bring their own key.

**Deploying this means you pay for every generation on an open page.** The three
guards in `worker.js` are the only thing between that and a bill: a per-IP hourly
limit, a global daily cap, and a payload check so nobody can proxy arbitrary
prompts through your key.

```bash
cd worker
wrangler kv namespace create RL      # paste the id into wrangler.toml
wrangler secret put ANTHROPIC_API_KEY
wrangler deploy
```

Then in `index.html`:

```js
var CC_STUDIO_ENDPOINT = "https://wallpaper-studio.<you>.workers.dev";
```

Set `ALLOWED_ORIGINS` to your domains, and tune `DAILY_CAP` to a number you would
be relaxed about seeing on an invoice. Start it lower than you think.
