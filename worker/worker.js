/**
 * Wallpaper Studio — keyless proxy.
 *
 * Holds the Anthropic key as a Worker secret so visitors do not need one.
 * Deploying this means YOU are paying for every request, on an open page,
 * so all three guards below are load-bearing. Do not remove them.
 *
 * ⚠️ THE GUARDS BELOW ARE NOT A HARD CAP. The KV counters are a non-atomic
 * read-modify-write on an eventually-consistent store: concurrent requests
 * read the same value, so a burst overshoots DAILY_CAP. They bound casual
 * traffic, not a determined one. The only real ceiling is a SPEND LIMIT on
 * the Anthropic workspace the key belongs to. Set that first; treat these
 * numbers as a courtesy brake on top of it.
 *
 * Cost model (Claude Sonnet 5, $2/$10 per MTok — the announced Sept-2026
 * increase to $3/$15 was cancelled; $2/$10 is the standard price):
 *   worst-case request = 16k output + ~4k input ≈ $0.17
 *   DAILY_CAP 8  →  ~$1.40/day ceiling  →  ~$42/month if it maxed out daily
 *   A complete 64-mark wallpaper is ~3 requests; 256 marks is ~5.
 *
 * Deploy (dashboard — no wrangler, no secret on any local machine):
 *   see DEPLOY.md in this directory.
 *
 * Deploy (wrangler — needs a Workers-scoped API token, NOT the DNS one):
 *   wrangler kv namespace create RL      → paste id into wrangler.toml
 *   wrangler secret put ANTHROPIC_API_KEY
 *   wrangler deploy
 *
 * Then in index.html:  var CC_STUDIO_ENDPOINT = "https://your-worker.workers.dev";
 */

const ALLOWED_ORIGINS = ["https://christmascherry.com", "https://www.christmascherry.com"];
const DAILY_CAP   = 8;     // total requests per day, all users  (~$1.40/day worst case)
const PER_IP_HOUR = 3;     // requests per IP per hour (one full 64-mark run)
const MAX_TOKENS  = 16000;

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = {
      "Access-Control-Allow-Origin": ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
      "Access-Control-Allow-Headers": "content-type",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Vary": "Origin",
    };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST")    return json({ error: "POST only" }, 405, cors);
    if (!ALLOWED_ORIGINS.includes(origin)) return json({ error: "origin not allowed" }, 403, cors);

    // ── guard 1: per-IP hourly ────────────────────────────────────────
    const ip = req.headers.get("CF-Connecting-IP") || "0";
    const hour = new Date().toISOString().slice(0, 13);
    const ipKey = `ip:${ip}:${hour}`;
    const ipN = parseInt(await env.RL.get(ipKey) || "0", 10);
    if (ipN >= PER_IP_HOUR) return json({ error: "rate limit — try again next hour" }, 429, cors);

    // ── guard 2: global daily spend cap ───────────────────────────────
    const day = new Date().toISOString().slice(0, 10);
    const dayKey = `day:${day}`;
    const dayN = parseInt(await env.RL.get(dayKey) || "0", 10);
    if (dayN >= DAILY_CAP) return json({ error: "daily cap reached — back tomorrow" }, 429, cors);

    // ── guard 3: never proxy an arbitrary payload ─────────────────────
    let body;
    try { body = await req.json(); } catch { return json({ error: "bad json" }, 400, cors); }
    const msgs = Array.isArray(body.messages) ? body.messages : null;
    if (!msgs || msgs.length !== 1 || typeof msgs[0].content !== "string")
      return json({ error: "unexpected payload" }, 400, cors);
    if (msgs[0].content.length > 12000) return json({ error: "prompt too long" }, 400, cors);

    await env.RL.put(ipKey,  String(ipN + 1),  { expirationTtl: 3700 });
    await env.RL.put(dayKey, String(dayN + 1), { expirationTtl: 90000 });

    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-sonnet-5",
        max_tokens: Math.min(body.max_tokens || MAX_TOKENS, MAX_TOKENS),
        messages: msgs,
      }),
    });
    return new Response(r.body, { status: r.status, headers: { ...cors, "content-type": "application/json" } });
  },
};

const json = (o, s, h) => new Response(JSON.stringify(o), { status: s, headers: { ...h, "content-type": "application/json" } });
