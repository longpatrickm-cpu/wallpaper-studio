# Wallpaper Studio

Type a subject. Judge four prototypes. Get a seamless tiling wallpaper built from
sixty-four marks drawn one at a time.

**Claude draws the marks. Your browser does everything else** — the offset lattice, the
per-cell rotation and jitter, the seam wrap that makes it tile forever, the audit, the
SVG export. One HTML file, no build step, no dependencies, no server.

```bash
git clone https://github.com/longpatrickm-cpu/wallpaper-studio
cd wallpaper-studio && python3 -m http.server 8080
open http://localhost:8080
```

Press **tile a demo canon** to try the whole renderer with no API key.

## Why the review step

Ask a model for 64 marks freehand and you get roughly twenty good ones and forty-four
variations on a circle. Not laziness — "draw another one" has no gradient, because
nothing tells the model what it has already covered.

So the flow is gated:

**1 · seed and criteria → 4 prototypes ·  2 · judge every one → 3 · draw 64**

You cannot advance without a verdict on all four, and cutting all four is refused
outright — it tells you to reseed rather than draw 64 marks in a direction you just
rejected. Kept marks are passed forward **as source**, so the next round sees the exact
geometry that worked.

Two more steps expand to 256, mirroring the first two but demanding verdicts on sixteen.

## Files

| | |
|---|---|
| `index.html` | the whole app |
| `MANUAL.md` | user manual — every control, the audit, troubleshooting |
| `CANON_KIT.md` | canon production: the 8×8 taxonomy grid, palette/style config, measured targets |
| `WALLPAPER_SPEC.md` | renderer spec — lattice maths, the seam wrap, `defs`/`use`, opacity doctrine |
| `render.py` | headless renderer · `python3 render.py configs/x.json` |
| `audit_canon.py` | diversity measurement · `python3 audit_canon.py marks/ --dupes` |
| `worker/` | optional Cloudflare Worker for keyless mode |

## Keys

It asks for your own. This is a static page — a shared key would sit in readable
JavaScript and be spent by whoever found it.

For a keyless public deploy, `worker/` holds the key as a Worker secret behind a per-IP
hourly limit, a global daily cap and a payload check, and you point
`CC_STUDIO_ENDPOINT` at it. **That means you pay for every generation on an open page**,
so read `worker/README.md` before deploying it.

## Related

Built for the wallpaper on [christmascherry.com](https://christmascherry.com). The
technique came from a 327-mark hand-drawn identity system; `CANON_KIT.md` carries the
measured comparison of the two canons that exist and what it implies for new ones.

## Licence

MIT — see `LICENSE`.
