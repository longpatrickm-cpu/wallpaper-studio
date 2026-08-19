# Glyph Canon Kit

Build a tiling mark-field wallpaper for **any** subject — bugs, cars, dinosaurs, shapes,
flowers — with variety that is *engineered and measured*, not hoped for.

Companion to `WALLPAPER_SPEC.md` (in `../ninetiesglyphs/`), which specifies the renderer.
This document is the **canon production workflow**: how you get 64 good marks, then 256.

```
glyph-kit/
  render.py         subject-agnostic renderer  →  python3 render.py configs/x.json
  audit_canon.py    diversity measurement      →  python3 audit_canon.py path/to/marks --dupes
  configs/          one JSON per wallpaper
  out/              generated tiles
```

Regenerate the two that exist:

```bash
python3 render.py configs/originalmd.json        # 129 marks · 729 cells · 1296px
python3 render.py configs/christmascherry.json   # 121 marks · 400 cells · 1160px
```

---

## 1. The central problem: models cluster

Ask for 64 marks freehand and you get roughly 20 good ones and 44 variations on a circle.
The cause is not laziness, it is that "draw another one" has no gradient — nothing tells the
model what it has *already covered*.

**The fix is a coordinate system.** Every mark gets an assigned cell in a grid whose two
axes are *what it is about* and *how it is drawn*. Cells are handed out before any drawing
starts. Then you measure the result and redraw the failures.

---

## 2. What the two existing canons actually measure

Not theory. `audit_canon.py` run over both live canons:

| Metric | OriginalMD (hairline, 129) | christmascherry (bold, 121) |
|---|---|---|
| elements / mark | **3.3** (median 3, max 6) | **2.6** (median 2, max 9) |
| stroke-width median | **0.9** (none above 2.2) | **4.0** (70% in 3–5) |
| explicit opacities / mark | **3.3** | **~0** |
| opacity spread | 52% primary · 45% secondary · 3% ghost | flat |
| colours / mark | 1→95, 2→34, **never 3** | 1→46, 2→54, 3→16, 4+→5 |
| primary ink appears in | **100%** of marks | **61%** |
| marks using fill | **29%** | **71%** |
| mean span of the 64px box | 42 | 47 |
| off-centre marks | 66% | 50% |

### The finding that matters

**Variety has a fixed budget, and each register spends it in a different currency.**

- **Hairline** spends it on **opacity layering**: more elements (3.3), each faint, stacked
  in three bands to create depth. Colour is nearly constant — one ink in 100% of marks.
- **Bold** spends it on **colour**: fewer elements (2.6), each carrying real weight, with
  2–3 colours per mark doing the differentiating that opacity does in the other register.

So: **do not ask a bold canon to also layer opacity, and do not ask a hairline canon to
also carry colour.** Each will read as noise. Pick the currency in Round 0 and commit.

Element *mix* is stable across both — circle ~30%, path ~20%, line 16–24%, rect 15–18%.
Treat that as a target, not a coincidence: it is what a field of mixed geometry needs to
avoid looking like one shape repeated.

---

## 3. Configuration — palette, style, register

One JSON per wallpaper. This is the whole surface for "how do I specify colour and style".

```jsonc
{
  "name": "bugs — the cabinet",
  "marks_dir": "../canons/bugs",        // relative to the KIT ROOT
  "out": "out/bugs.svg",
  "id_prefix": "bug-m",                 // MUST be unique per page; ids collide otherwise
  "seed": 1994,                         // same seed = byte-identical tile, forever
  "register": "ghost",                  // "ghost" | "bold"  — see §2

  "grid":   { "cell": 48, "cols": 27, "rows": 27, "mark": 24 },
  "jitter": { "px": 8, "rotate": [-20,20], "scale": [0.75,1.25], "opacity": [0.55,1.00] },

  "palette": {
    "ink":     "#2E2A22",   // 100% of marks. the spine.
    "accent":  "#C9A227",   // ~40%. a SINGLE point per mark — vertex, node, dot.
    "second":  "#4E6B4A",   // ~8%.  thematic (living / vegetal / warm)
    "third":   "#6E7A82",   // ~5%.  faint scaffolds
    "gravity": "#7A2E1E",   // ~3%.  rare and earned. reach for it almost never.
    "ground":  "#F6F3EA"    // the surface. never drawn, always present.
  },

  "tints": [["#2E2A22",62],["#C9A227",18],["#4E6B4A",12],["#7A2E1E",8]],

  "style": {
    "stroke_primary":   [1.0, 1.3],
    "stroke_secondary": [0.7, 0.8],
    "stroke_ghost":     [0.4, 0.6],
    "opacity_bands":    [[0.30,0.55],[0.16,0.29],[0.05,0.15]],
    "fills": "none",              // "none" | "sparse" | "solid"
    "max_colors_per_mark": 2
  }
}
```

**`tints`** enables free colour scatter: the renderer swaps `palette.ink` for
`currentColor` in the defs and puts `color=` on each `<use>`. Weighted, zero extra bytes.
Set `null` for a monochrome field. **Only use it in the `ghost` register** — a bold canon
already carries per-mark colour and will fight it.

### Register presets

| | ghost | bold |
|---|---|---|
| `grid.cell` / `grid.mark` | 40–48 / 24–26 | 56–60 / 38–40 |
| `stroke_primary` | 1.0–1.3 | 3.0–5.0 |
| `fills` | `none` | `solid` |
| `max_colors_per_mark` | 2 | 3 |
| `jitter.opacity` | [0.55, 1.00] | [0.85, 1.00] |
| variety currency | opacity layering | colour |

> **Bold marks in a ghost lattice read as mud.** If you change stroke weight you must
> change `cell` with it. This cost a full rebuild once already.

---

## 4. The workflow

### Round 0 — Beta. Eight prototypes. **Do not skip this.**

Draw **8 marks that embody the theme at its strongest** — not a representative sample, the
eight you would show someone to explain what this canon *is*. Then render a field and look
at it.

```bash
python3 render.py configs/bugs.json && open out/bugs.svg
```

Round 0 exists to settle five things **before** 56 more marks are committed to them:

1. **Register** — does the subject want ghost or bold? Look at the field, not the marks.
2. **Palette** — do the accent and gravity colours earn their place at 10% opacity?
3. **Lattice** — is `cell`/`mark` right, or is the field crowded / sparse?
4. **Complexity** — are you at the register's element budget (§2) or over it?
5. **Does it read as the subject at 24px?** If a stranger cannot tell it is insects,
   the concept families in §5 are wrong, not the drawing.

**Ship a contact sheet and a field render from Round 0 and stop.** Get a human verdict.
Everything after this is expensive to undo.

### Round 1 — 64 marks. The full grid (§5).

### Rounds 2–4 — 64 each, to 256.

Each later round does three jobs, in this order:

1. **Redraw the failures** the audit flagged (near-dupes, off-target complexity).
2. **Fill the thin cells** — the audit shows which grid rows/columns are underpopulated.
3. **Extend the grid** — add concept families, or add a formal strategy column, or open
   *hybrid* cells (family A treated in strategy B where that pairing was skipped).

Do **not** just "draw 64 more." That is how a canon fills up with variations.

### A week, realistically

| Day | Work | Output |
|---|---|---|
| 1 | Round 0 beta, config, palette | 8 marks + verdict |
| 2 | Round 1 grid, cells 1–32 | 32 |
| 3 | Round 1 grid, cells 33–64 | **64 · audit · field render** |
| 4 | Audit response + Round 2 | 128 |
| 5 | Round 3 | 192 |
| 6 | Round 4 | **256** |
| 7 | Final audit, redraws, tune `--wpo`, ship | 256 clean |

---

## 5. The taxonomy grid — 8 × 8 = 64

Rows are **concept families** (subject-specific: *what the mark is about*).
Columns are **formal strategies** (universal: *how it is drawn*).
**Every cell gets exactly one mark.** This is what forces coverage.

### Columns — the eight formal strategies

| # | Strategy | Test |
|---|---|---|
| 1 | **Single gesture** | one continuous line or curve. nothing else. |
| 2 | **Radial** | organised around a centre; rotational symmetry |
| 3 | **Nested** | concentric or contained; a thing inside a thing |
| 4 | **Repeated unit** | the same small element 3–8 times in a row or grid |
| 5 | **Solid mass** | a filled shape carries it (bold) / a 3–8% wash (ghost) |
| 6 | **Pure outline** | hollow, no fill, the boundary is the subject |
| 7 | **Fragment** | cropped, partial, implied — runs off the edge of the box |
| 8 | **Negative space** | the gap *is* the mark; ink defines what is absent |

Strategies 7 and 8 are the ones that get skipped and the ones that make a canon feel
intelligent. **Enforce them.**

### Rows — concept families per subject

**Bugs** — wing venation · leg & joint · antenna & sense · compound eye · segment & plate ·
colony & swarm · metamorphosis & instar · trace (web, gall, tunnel)

**Cars** — wheel & hub · grille & face · body line & profile · engine & drivetrain ·
dash & gauge · road, lane & sign · speed & motion · fastener & part

**Dinosaurs** — bone & joint · track & trace · tooth & claw · plate, frill & horn ·
egg & nest · stratum & deep time · posture & gait · reconstruction (the dashed missing half)

**Shapes** — primitive · subdivision · tessellation · symmetry operation · boolean
(union / subtract) · progression & series · distortion · void

**Flowers** — petal arrangement · stamen & centre · stem & node · leaf & vein ·
bud & unfurling · seed & dispersal · root & bulb · cluster & inflorescence

Deriving families for a new subject: list the **eight things a specialist would notice**
that a layperson would not. If two families would produce the same drawing, one of them
is wrong.

---

## 6. The prompt

Fill the bracketed fields. Give the model the config block and this brief together.

````
You are drawing a canon of tiling wallpaper marks. Subject: [SUBJECT].

## Config
[paste the JSON config block]

Register: [ghost|bold]. Read that row of the register table: it fixes stroke
weights, fill policy, colours per mark, and — critically — WHERE THE VARIETY
COMES FROM. In `ghost` variety comes from layered opacity; in `bold` it comes
from colour. Do not do both.

## Your assignment this round
Draw exactly [N] marks, one per assigned cell:

[paste the assigned grid cells, e.g.
  R1C1 wing venation × single gesture
  R1C2 wing venation × radial
  ... ]

The cell is a CONSTRAINT, not a suggestion. If a cell feels wrong, draw it
anyway and flag it — a wrong-feeling cell is usually the most interesting mark
in the batch, and it is definitely the one nobody would have drawn freehand.

## Form — non-negotiable
- 64×64 viewBox. `fill="none"` on the root, round caps and joins.
- Stroke weights, opacity bands, fill policy, max colours: from the config.
- Target [2.6 bold | 3.3 ghost] elements per mark. Median [2|3]. Six is a lot.
  If you need more than six elements you have not reduced the idea yet.
- Element mix across the batch, approximately: circle 30%, path 20%,
  line 20%, rect 15%, polygon 10%, ellipse/polyline 5%.
- Use the whole box. Mean span should be ~42–47 of 64. A canon of marks that
  all sit in the middle 30px reads as a grid of dots.
- ~50–65% of marks should be visibly off-centre. Perfect centring is what
  makes a scattered field look mechanical.

## Concept — the thing that actually matters
Each mark is ONE gesture: one idea, drawn with restraint. Nothing is literally
depicted. It must read at 24px and it must sit beside its neighbours WITHOUT
matching them.

Draw the subject's own visual LANGUAGE, not objects from the subject. This is
the single most common failure. A nineties canon of popsicle sticks and buckets
has no nineties in it; the decade is legible through squiggle, confetti, solid
triangle, zigzag, checkerboard. For [SUBJECT], ask of every mark: *is this a
thing from the subject, or is it the subject's own grammar?* Prefer the grammar.

## Output
One file per mark: `NNN-slug.svg`, numbered continuously from [START].
First line inside the file:
`<!-- NNN · Name — one line of intent, the poem of the mark -->`
Literal hex, not CSS variables, so each file stands alone.

## Hard constraints — violating any of these fails the mark
- Do NOT write a generator, a loop, or a parametric function. Every mark is
  conceived individually with its own reasoning shown. Parametric generation
  was tried on the parent system and rejected: "repetition dressed as variety."
  It is obvious in the field.
- No two marks may be rotations, reflections or recolours of each other.
- Never exceed `max_colors_per_mark`.
- If you notice you are drawing the same idea twice, STOP and say so.

## Before you finish
List, in one line each, the three marks you think are weakest and why. You are
better at spotting your own clustering in review than in generation.
````

**Beta-round variant.** Replace the assignment with:

````
This is ROUND 0 — a beta of 8 prototypes. Do NOT use the grid.

Draw the eight marks that best EMBODY [SUBJECT] — not a representative sample,
the eight you would show someone to explain what this canon is. Range widely:
at least two should be almost nothing (one or two elements), and at least one
should be the most complex thing you would ever allow.

Then state, in prose: which register you think this subject wants and why;
which palette slots are earning their place; and the eight concept families you
would use for the full grid.
````

---

## 7. The audit loop

```bash
python3 audit_canon.py ../canons/bugs --dupes
```

Targets, derived from §2:

| Check | Target | If it fails |
|---|---|---|
| elements / mark | ghost 3.0–3.6 · bold 2.2–2.8 | over → not reducing; under → thin marks |
| complexity spread | median at target, tail to 5–6 | all identical → clustering |
| element mix | circle ~30, path ~20, line ~20, rect ~15 | one dominant → one shape repeated |
| stroke distribution | ≥90% inside the config's bands | drift → the register is slipping |
| opacity (ghost only) | 3 bands present, roughly 50/45/5 | flat → you lost the depth |
| colours / mark | ≤ `max_colors_per_mark`, always | over → the field will read as noise |
| mean span | 42–47 of 64 | low → everything huddled centre |
| off-centre | 50–66% | low → mechanical field |
| **near-dupes >0.86** | **<8% of N** | redraw the flagged mark, same cell |

### On the duplicate detector

It bins geometry into an **8×8 occupancy grid** plus a path-command histogram — it compares
*where the ink is*, not element counts.

This matters: v1 compared feature counts and reported **825 pairs at >0.995** on a
121-mark canon, because every one-element mark looked identical to every other. `sparkle`
and `flame` scored a perfect 1.0000 and are not remotely alike. The spatial version reports
**12 pairs**, and its top hit is a **true duplicate**:

```
1.0000  033-arrowhead.svg  ≈  114-play.svg      ← both a right-pointing triangle
```

That is the loop working. **A metric that flags 68% of your corpus is not strict, it is
broken** — validate the tool against a canon you already trust before you act on it.

---

## 8. Known state

- **christmascherry / jazz (121)** — live. Near-dupes 10% of N. `arrowhead` ≈ `play`
  is a genuine duplicate and one of them should be redrawn.
- **OriginalMD / hairline (129)** — retired from the live site, kept as a canon.
  Near-dupes 14% of N; `very-special` ≈ `poke-ball` (0.98) and
  `suspenders` ≈ `high-waters` (0.97) are real and would be the first redraws.
- `ninetiesglyphs/marks/` was a **stale mix of both canons** (129 hairline files left over
  after the generator was switched to jazz). Split into `marks-jazz/` and
  `marks-hairline/`; the old directory is renamed `marks-STALE-do-not-use/`.
  **Regenerate mark directories whenever you switch canons in `build.py`.**
