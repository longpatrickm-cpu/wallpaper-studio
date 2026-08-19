#!/usr/bin/env python3
"""render.py — subject-agnostic tiling mark-field renderer.

    python3 render.py configs/christmascherry.json

Reads a config, reads a directory of 64x64 SVG marks, emits a seamless inline
<svg> using <defs>+<use> inside a <pattern>.  See CANON_KIT.md for the spec.
"""
import os, re, sys, json, glob, random

def load_marks(d):
    out = []
    for fp in sorted(glob.glob(os.path.join(d, "*.svg"))):
        raw = open(fp, encoding="utf-8").read()
        raw = re.sub(r'<\?xml[^?]*\?>\s*', '', raw)
        m = re.search(r'<svg[^>]*>(.*)</svg>', raw, re.DOTALL)
        if not m:
            continue
        inner = m.group(1).strip()
        inner = re.sub(r'<!--.*?-->', '', inner, flags=re.DOTALL).strip()
        if inner:
            out.append((os.path.basename(fp), inner))
    return out


def build(cfg, marks):
    g   = cfg["grid"]
    CELL, COLS, ROWS = g["cell"], g["cols"], g["rows"]
    TILE  = CELL * COLS
    MARK  = g["mark"]
    SCALE = MARK / 64.0
    PAD   = (CELL - MARK) / 2.0
    j     = cfg["jitter"]
    pfx   = cfg.get("id_prefix", "m")
    ink   = cfg["palette"].get("ink")
    tints = cfg.get("tints")            # [[hex, weight], ...] or None

    # ── defs: geometry once.  currentColor swap enables free per-use tinting.
    defs = []
    for i, (_, inner) in enumerate(marks):
        body = inner.replace(ink, "currentColor") if (tints and ink) else inner
        defs.append(f'<g id="{pfx}{i}">{body}</g>')

    pool = []
    if tints:
        for hexv, w in tints:
            pool += [hexv] * int(w)

    rnd   = random.Random(cfg["seed"])
    order, cells = list(range(len(marks))), []
    while len(cells) < COLS * ROWS:
        rnd.shuffle(order); cells.extend(order)
    cells = cells[:COLS * ROWS]

    uses, idx = [], 0
    for row in range(ROWS):
        xoff = CELL / 2 if row % 2 else 0
        for col in range(COLS):
            mi = cells[idx]; idx += 1
            cx, cy = col * CELL + xoff, row * CELL
            jx = rnd.uniform(-j["px"], j["px"])
            jy = rnd.uniform(-j["px"], j["px"])
            rot = rnd.uniform(*j["rotate"])
            sc  = SCALE * rnd.uniform(*j["scale"])
            op  = rnd.uniform(*j["opacity"])
            tint = rnd.choice(pool) if pool else None
            c = f' color="{tint}"' if (tint and tint != ink) else ""

            def emit(tx, c=c, op=op, sc=sc, rot=rot, jy=jy, mi=mi):
                return (f'<use href="#{pfx}{mi}"{c} opacity="{op:.2f}" transform="'
                        f'translate({tx:.1f},{cy + PAD + jy:.1f}) scale({sc:.3f}) '
                        f'rotate({rot:.1f},32,32)"/>')

            uses.append(emit(cx + PAD + jx))
            # ── the seam: half-offset rows must wrap, or the tile is not seamless
            if row % 2 and col == COLS - 1:
                uses.append(emit(cx + PAD + jx - TILE))

    cls = cfg.get("class", "wall")
    return (f'<svg class="{cls}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" '
            f'preserveAspectRatio="xMidYMid slice" fill="none" stroke-linecap="round" '
            f'stroke-linejoin="round"><defs>{"".join(defs)}'
            f'<pattern id="{pfx}pat" width="{TILE}" height="{TILE}" '
            f'patternUnits="userSpaceOnUse">{"".join(uses)}</pattern></defs>'
            f'<rect width="100%" height="100%" fill="url(#{pfx}pat)"/></svg>')


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    # paths in a config resolve against the KIT ROOT, not the config's folder,
    # so configs/ can be reorganised without rewriting every path
    base = os.path.dirname(os.path.abspath(__file__))
    md = cfg["marks_dir"]
    if not os.path.isabs(md):
        md = os.path.normpath(os.path.join(base, md))
    marks = load_marks(md)
    if not marks:
        sys.exit(f"no marks found in {md}")

    g = cfg["grid"]
    cells = g["cols"] * g["rows"]
    if len(marks) < cells / 8:
        print(f"  ! only {len(marks)} marks for {cells} cells "
              f"({cells/len(marks):.1f}x repeat) — repeats may become visible")

    svg = build(cfg, marks)
    out = cfg.get("out")
    if out:
        if not os.path.isabs(out):
            out = os.path.normpath(os.path.join(base, out))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(svg)
    print(f"{cfg['name']}: {len(marks)} marks · {cells} cells · "
          f"tile {g['cell']*g['cols']}px · {len(svg)/1024:.1f} KB"
          + (f" → {out}" if out else ""))


if __name__ == "__main__":
    main()
