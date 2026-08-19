/**
 * Wallpaper Studio — keyless proxy.
 *
 * Holds the Anthropic key as a Worker secret so visitors do not need one.
 * Deploying this means YOU are paying for every generation, on an open page,
 * so all three guards below are load-bearing. Do not remove them.
 *
 *   wrangler secret put ANTHROPIC_API_KEY
 *   wrangler kv namespace create RL
 *   wrangler deploy
 *
 * Then in index.html:  var CC_STUDIO_ENDPOINT = "https://your-worker.workers.dev";
 */

const ALLOWED_ORIGINS = ["https://christmascherry.com", "https://www.christmascherry.com"];
const DAILY_CAP   = 300;   // total generations per day, all users
const PER_IP_HOUR = 8;     // generations per IP per hour
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
