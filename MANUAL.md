# Wallpaper Studio — User Manual

Type a subject. Get a seamless tiling wallpaper made of marks drawn one at a time.

Everything except the drawing happens in your browser. There is no server, no account,
no analytics, and nothing is stored.

---

## Before you start

**You need an Anthropic API key** — `sk-ant-…` from [console.anthropic.com](https://console.anthropic.com).
It is typed into the page, held in that tab, sent only to Anthropic, and never stored.
Closing the tab forgets it.

**You do not need one to look around.** Press **tile a demo canon** and the renderer
runs on a built-in set of marks. Every control — density, strength, reseed, download,
copy as CSS — works on it. That is the whole tiling engine, for free.

**Rough cost.** A 64-mark run is about five requests. In the low tens of cents. A full
256 run is roughly four times that. Check current pricing; do not take this as a quote.

---

## The five steps

Three get you 64 marks. Two more get you 256.

### Step 1 — Seed & criteria

**Concept seed.** One or two words. `bugs`, `dinosaurs`, `lighthouses`, `kitchen tools`.
Concrete beats abstract: *bugs* produces a better canon than *nature*, because a canon
needs specific things to be about.

**Direction** *(optional)*. Where the register comes from. *"victorian specimen cabinet,
slightly menacing"* pulls somewhere quite different from *"saturday morning cartoon"*
on the same seed. This is the field that changes the most for the least typing.

**Register** — the single most consequential choice.

| | **Ghost** | **Bold** |
|---|---|---|
| looks like | hairline, whisper, texture | thick, filled, reads across a room |
| stroke | 1.0–1.3 | 3–5 |
| fills | almost none | solid |
| variety comes from | layered opacity | colour |
| good for | backgrounds behind text | statement walls, packaging, a hero |

They are not interchangeable and they do not blend. A bold canon told to also layer
opacity reads as noise, and a ghost canon carrying three colours per mark reads as mud.
Pick one.

**Palette** — six presets. Each is one primary (in every mark), one accent (a single
point in ~40% of marks), and three supporting colours used sparingly. The primary does
most of the work; the rare colours are what make it feel considered.

**Density** — cell size, 34–86px. Smaller = more marks per screen. **Bold marks need
bigger cells.** Bold at 34px is mud. Rule of thumb: ghost 40–48, bold 56–60.

**Strength** — overall opacity, 0.10–1.00. Behind body text, 0.3–0.5. As the subject
of the page, 0.8–1.0. Adjustable any time without redrawing.

Press **GENERATE 4 PROTOTYPES**. Twenty seconds or so.

### Step 2 — Judge four

Four marks. **Each needs a verdict.**

- **keep** — draw more like this
- **cut** — do not
- **the note** — why. This is the highest-leverage text in the whole tool.

Kept marks are handed to the next round **as source code**, so it sees the exact geometry
that worked rather than a description of it. Cuts and notes go through verbatim as binding
direction.

**Overall direction** applies to all 64. Things worth writing: *more negative space* ·
*fewer circles* · *let some run off the edge* · *calmer* · *the accent colour is doing too
much*.

Two rules the tool enforces:

- **You cannot advance without judging all four.**
- **You cannot cut all four and continue.** It will tell you to reseed. Drawing 64 marks
  in a direction you just rejected is the expensive mistake this step exists to prevent.

If nothing is close, press **← change the seed**. Reseeding costs one small request.
Being wrong at step 3 costs sixty-four.

### Step 3 — Draw 64

Drawn in batches of sixteen, each told what came before so it does not repeat itself.
A failed batch keeps what it has rather than losing the run.

Then:

- **reseed layout** — same marks, new arrangement. Free, instant, no request. Do this
  several times; the arrangement matters more than people expect.
- **audit the canon** — measures elements per mark, element mix, mean span, off-centre
  percentage, against the targets in `CANON_KIT.md`.
- **download .svg** — the tile. Drop it into any project.
- **copy as CSS** — a ready `background-image` rule.

### Steps 4 and 5 — expanding to 256

Only if you want them.

**Step 4** opens with an audit of your 64 so you can aim at what is demonstrably thin
rather than at whatever comes to mind. Write an expansion direction and it draws 16
prototypes against the gaps.

**Step 5** is step 2 again with sixteen. **All sixteen need a verdict.** That is
deliberately tedious — it is the last cheap moment before 192 more marks are committed
to those decisions.

---

## Reading the audit

```
elements/mark  2.6   (target 2.2–2.8)
element mix
  circle   ████████··············· 31.9%
  path     █████·················· 19.9%
mean span      47 of 64   (target 42–47)
off-centre     50%        (target 50–65%)
```

| Reading | Means | Do |
|---|---|---|
| elements/mark too high | not reducing to one gesture | note it: *simpler, fewer parts* |
| one element type >45% | one shape repeated | *fewer circles, more line and polygon* |
| mean span < 38 | everything huddled centre | *use the whole box, let marks run off the edge* |
| off-centre < 40% | mechanical field | *more asymmetry* |

---

## Troubleshooting

**"needs an Anthropic key"** — must start `sk-ant-`. Or use the demo.

**HTTP 401** — key wrong or revoked.

**HTTP 429** — Anthropic is rate-limiting you. Wait a minute.

**"nothing came back"** — occasionally the reply has no parseable SVG. Try again; if it
persists, simplify the direction field.

**Fewer than 64 marks** — a batch failed. What arrived is kept. Reseed, or start again.

**It looks like mud** — density too tight for the register. Raise the cell size, or drop
strength to 0.4.

**It looks empty** — density too loose, or too few marks. Lower cell size.

**Everything looks the same** — the seed was too abstract. *Nature* has no grammar;
*ferns* does.

---

## What it is actually doing

Claude receives a canon brief: register-specific stroke weights and opacity bands,
palette slots with frequencies, element-mix targets, eight formal strategies to spread
across, and a hard rule against parametric generation. From step 2 it also gets your
kept prototypes as source, and your notes verbatim.

The marks come back as bare SVG. Your browser then does the rest — an offset lattice
where odd rows shift half a cell, per-cell rotation, jitter, scale and opacity from a
seeded PRNG, and a seam wrap so the tile repeats forever without a visible edge.

The full construction is in [`WALLPAPER_SPEC.md`](WALLPAPER_SPEC.md). The canon
production workflow, including the 8×8 taxonomy grid that stops a canon collapsing into
variations on a circle, is in [`CANON_KIT.md`](CANON_KIT.md).

---

## Privacy

No analytics. No cookies. No server. No account. Your key stays in the tab and is sent
only to `api.anthropic.com`. Marks and settings live in the page and vanish when you
close it — **download anything you want to keep.**
