# The Tiling Mark-Field Wallpaper — Replication Spec

A build spec, not a mood board. Follow it and you get the wallpaper on
christmascherry.com and originalmd.com. The last section is how to extend it.

Reference implementation: `build.py` in this directory. Live example:
`christmascherry.com` (`.cc-wall`). Ancestor: `originalmd-website/public/generate_wallpaper.py`.

---

## 0. What it is, in one paragraph

A seamless background built from **N individually hand-drawn SVG marks** scattered
across an **offset lattice**. Every cell gets one mark, rotated / jittered / rescaled /
faded by a **seeded** RNG so the grid never visually resolves. It is emitted as **one
inline `<svg>`** using `<defs>` + `<use>` inside a `<pattern>`, so the browser tiles it
natively and the whole thing costs ~70–110 KB instead of ~350 KB.

**The marks are the art. The generator is plumbing.** Do not spend your effort on the
generator.

---

## 1. Architecture — the non-obvious part

Emit **one** `<svg>` containing:

```
<svg class="wall" preserveAspectRatio="xMidYMid slice" fill="none"
     stroke-linecap="round" stroke-linejoin="round">
  <defs>
    <g id="m0">…mark 0 geometry…</g>      ← one per mark, N total
    <g id="m1">…</g>
    …
    <pattern id="wall" width="TILE" height="TILE" patternUnits="userSpaceOnUse">
      <use href="#m37" opacity=".82" transform="translate(x,y) scale(s) rotate(r,32,32)"/>
      …one per cell, COLS*ROWS of them…
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#wall)"/>
</svg>
```

Three decisions carry the whole design:

1. **`<defs>` + `<use>`, never inlined copies.** Each mark's geometry appears once.
   The 729-cell OriginalMD tile inlines everything → **365 KB**. The same construction
   with `<use>` → **~110 KB**. That difference is what makes it *inlineable*, which
   matters enormously where sidecar assets are forbidden (auth-gated origins, or a fleet
   shipping `immutable` cache headers you cannot purge).
2. **`<pattern>` does the tiling, not CSS `background-repeat`.** No data-URI encoding,
   no separate file, no cache story. It is DOM.
3. **`preserveAspectRatio="xMidYMid slice"`** + a 100%×100% rect, so it fills any
   container without distorting the marks.

> **If you namespace nothing else, namespace the ids.** Injecting into a page that
> already has inline SVG will collide. Prefix everything (`ccw-m0`, `ccw-wall`).

---

## 2. Lattice geometry

```
CELL          px per cell
COLS, ROWS    cells per tile (square)
TILE = CELL * COLS
MARK          rendered mark size, px
SCALE = MARK / 64          (source marks are a 64×64 viewBox)
PAD   = (CELL - MARK) / 2
```

For each cell at (col,row):

```
xoff = CELL/2 if row is odd else 0        ← the offset lattice; this is the whole look
cx   = col*CELL + xoff
cy   = row*CELL
x    = cx + PAD + jitter_x
y    = cy + PAD + jitter_y
```

### The seam (the bug you will hit)

Half-offset odd rows push their last mark past the right edge, so the tile stops being
seamless. **For every odd row, emit the last cell twice** — once normally, once at
`x - TILE`. Same jitter, same rotation, same opacity, or the seam shows as a stutter.

```python
uses.append(emit(x))
if row % 2 and col == COLS - 1:
    uses.append(emit(x - TILE))
```

---

## 3. Per-cell randomisation

Everything below comes from **one seeded RNG** (`random.Random(seed)`), so a given seed
always reproduces the same field. Different seed per page-section = visually different
arrangement of identical material.

| Parameter | Ghost field | Bold field |
|---|---|---|
| rotation | ±20° | ±24° |
| jitter | ±7 px | ±9 px |
| scale multiplier | 0.75–1.25 | 0.75–1.25 |
| opacity multiplier | 0.55–1.00 | 0.85–1.00 |

Rotate **about the mark's own centre** — `rotate(r,32,32)` in the 64-unit source space,
applied *inside* the scale transform. Rotating about the origin flings marks out of cell.

---

## 4. ⚠ Stroke weight drives cell size

This is the mistake that cost a full rebuild.

| Mark style | stroke-width | CELL | MARK |
|---|---|---|---|
| Hairline / ghost | 1.0–1.3 | 40–48 | 24–26 |
| Bold / filled | 3.0–7.0 | 56–60 | 38–40 |

**Bold marks in a hairline lattice read as mud.** If you double the stroke weight you
must open up the lattice. Tune `CELL` first, then `MARK`, then re-check at 100% zoom
*and* at 50% — a field that reads at one scale can close up at the other.

---

## 5. Opacity doctrine

Two valid schools. Pick deliberately.

**A — flatten (OriginalMD).** Strip every inline opacity from the source marks; group
opacity is the sole control. Correct when marks are uniform and you want absolute
evenness.

**B — layer (recommended).** *Keep* each mark's internal opacity layering and multiply a
per-cell opacity over it. Correct when the marks have internal depth — a three-band
hierarchy (primary .30–.55 / secondary .16–.29 / ghost .05–.15) is what makes hairline
marks breathe, and flattening destroys it.

**Then dim in CSS, not in the SVG:**

```css
.wall { opacity: var(--wpo, .5); }
```

Bake per-cell opacity **high** (0.85–1.0) and let the CSS variable do the dimming. That
way the dial goes *both* directions. If you bake it faint, you can never turn it up —
`opacity` cannot exceed 1.

**Ship the dial.** How loud a wallpaper should be is a taste call the builder cannot
make for the owner. Expose `--wpo` and let them land on a number.

---

## 6. Free colour variation via `currentColor`

To scatter colour without duplicating `<defs>`:

1. When emitting **defs only**, replace the primary ink hex with `currentColor`.
   Leave accent colours as literal hex.
2. Give each `<use>` a `color` attribute.

```python
inner.replace(PAL["ink"], "currentColor")            # defs
f'<use href="#m{i}" color="{tint}" .../>'            # cells
```

Cost: zero extra bytes. Weight the tints (e.g. 62% ink / 18% teal / 12% magenta / 8%
accent) so the field reads as one material with colour *incidents*, not confetti.

---

## 7. Readability contract — non-negotiable

The wallpaper is a **fixed layer at `z-index:0`**, `pointer-events:none`. Content sits
above it at `z-index:1`.

**Legibility is structural, not tuned.** It works because:
- content containers have an **opaque** background, and
- the content column is **capped** (900 px) and centred,

so the pattern only ever appears in the margins. It is never behind text at any strength.

> Make a content card transparent "to show more of the nice wallpaper" and you have
> broken the document. This is the single most likely future regression — write it down
> in the project's own docs.

Also: `@media print { .wall { display:none } }`.

---

## 8. The canon

- **N ≈ 120 is plenty.** A 400–729 cell tile repeats each mark 3–6×, and under
  rotation + jitter + scale + opacity variation repeats are invisible.
- Source format: 64×64 viewBox, `fill="none"`, round caps and joins, no `<svg>` wrapper
  styling beyond that.
- **Conceive each mark individually.** Parametric generation was tried on the parent
  system and rejected — "repetition dressed as variety." It is obvious in the field.
- Each mark must read at **24 px** and sit beside its neighbours without matching them.

### The two failure modes, both real

1. **Drawing objects instead of the era's graphic language.** A nineties canon of
   popsicle sticks, buckets and blimps has no nineties in it. The decade is legible
   through its *grammar* — squiggle, confetti, solid triangle, zigzag, checkerboard,
   starburst — which is already abstract. Ask: *is this a thing from the subject, or is
   it the subject's own visual language?* Prefer the latter, heavily.
2. **Wrong weight for the register.** Hairline restraint suits a clinical brand. It
   drains a loud one. Match stroke weight to the subject's volume before drawing 100
   marks in the wrong key.

---

## 9. Build order

1. Palette: one primary (100% of marks), one accent (~40%, a single point), 2–4
   supporting, one ground.
2. Decide register → set stroke weights → set `CELL`/`MARK` from §4.
3. Draw 8 marks. Render a field. **Look at it.** Adjust before drawing 100.
4. Draw the canon in batches, checking the field every ~30.
5. Generate seeded variants (one per section).
6. Wire `--wpo`, verify legibility at 0.2 and 1.0.
7. Verify seamlessness: scroll a tall page; look for a repeating vertical stutter at
   x = TILE (that is the §2 seam bug).

---

## 10. Extending it

- **Swap the canon, keep the generator.** It is subject-agnostic. Point `MARKS` at a new
  list; nothing else changes.
- **Per-section seeds** — same material, no two blocks alike. Cheap and effective.
- **Weighted tints** per section for a colour temperature shift down a page.
- **Responsive**: shrink `TILE` on narrow viewports (`background-size`, or a second
  pattern at smaller `CELL`). Do not scale the marks below ~18 px; they stop reading.
- **Animation**: possible via SMIL/CSS on `<use>`, but 400+ animated nodes is expensive.
  If you must, animate ≤5% of cells, and gate on `prefers-reduced-motion`.
- **Density gradient**: bias opacity by row so the field fades toward the content. Do it
  in the generator, not CSS, so it survives tiling.

## 11. Known numbers (christmascherry.com, 2026-08)

```
CELL 58 · COLS/ROWS 20 · TILE 1160 · MARK 40 · 121 marks · 400 cells + 10 seam wraps
rotation ±24° · jitter ±9 · scale 0.75–1.25 · per-cell opacity 0.85–1.00
--cc-wpo default .5   ·  inline size ~67 KB  ·  page total ~98 KB gzipped
```
