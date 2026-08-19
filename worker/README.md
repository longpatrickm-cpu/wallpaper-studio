# Keyless mode

Optional. Without it the Studio works fine — visitors bring their own key, and
nothing in this directory needs to exist.

**Deploying this means you pay for every request on an open page.** Read
[`DEPLOY.md`](DEPLOY.md) before you do — it covers the spend limit, the cost
model, and both deploy paths.

## The guards, and what they are not

`worker.js` has three: a per-IP hourly limit, a global daily cap, and a payload
check so nobody can proxy arbitrary prompts through your key.

⚠️ **The daily cap is not a hard cap.** Its KV counters are a non-atomic
read-modify-write on an eventually-consistent store, so concurrent requests read
the same value and a burst overshoots. The only ceiling that actually holds is a
**spend limit on the Anthropic workspace the key belongs to**. Set that first
(`DEPLOY.md`, step 1); treat these numbers as a courtesy brake on top of it.

## Defaults

```js
const DAILY_CAP   = 8;   // ~$1.40/day worst case  (~2–3 finished wallpapers)
const PER_IP_HOUR = 3;   // one full 64-mark run per visitor per hour
const MAX_TOKENS  = 16000;
```

At Claude Sonnet 5 rates ($2/$10 per MTok — the announced Sept-2026 increase
was cancelled) a worst-case request is ~$0.17. Raise `DAILY_CAP` only to a number you
would be relaxed about seeing on an invoice, and raise the Anthropic workspace
limit to match. Start lower than you think.

Set `ALLOWED_ORIGINS` to your own domains — it is what stops someone else's page
from spending your key.
