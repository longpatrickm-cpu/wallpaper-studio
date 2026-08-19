#!/usr/bin/env python3
"""audit_canon.py — measure a mark canon. Diversity is engineered, not hoped for.

    python3 audit_canon.py ../ninetiesglyphs/marks-jazz [--dupes]

Reports element mix, complexity, stroke/opacity distribution, palette usage,
canvas coverage, centroid spread, and near-duplicate pairs.
"""
import os, re, sys, glob, math
from collections import Counter

ELEMS = ["circle","ellipse","line","path","polygon","polyline","rect"]

def parse(fp):
    raw = open(fp, encoding="utf-8").read()
    m = re.search(r'<svg[^>]*>(.*)</svg>', raw, re.DOTALL)
    inner = m.group(1) if m else ""
    inner = re.sub(r'<!--.*?-->', '', inner, flags=re.DOTALL)
    d = {"file": os.path.basename(fp)}
    d["elems"] = Counter(re.findall(r'<(' + "|".join(ELEMS) + r')\b', inner))
    d["n"] = sum(d["elems"].values())
    d["stroke"] = [float(x) for x in re.findall(r'stroke-width="([\d.]+)"', inner)]
    d["opacity"] = [float(x) for x in re.findall(r'opacity="([\d.]+)"', inner)]
    d["colors"] = set(c.upper() for c in re.findall(r'#[0-9A-Fa-f]{6}', inner))
    d["fills"] = len(re.findall(r'fill="#', inner))
    nums = [float(x) for x in re.findall(r'-?\d+\.?\d*', re.sub(r'stroke-width="[\d.]+"','',
             re.sub(r'opacity="[\d.]+"','', re.sub(r'#[0-9A-Fa-f]{6}','',inner))))]
    pts = [v for v in nums if -20 <= v <= 84]
    d["bbox"] = (min(pts), max(pts)) if pts else (0, 0)
    d["pts"] = pts
    d["cmds"] = Counter(re.findall(r'[MCLQAZmclqaz]', "".join(re.findall(r'd="([^"]*)"', inner))))
    d["cx"] = sum(pts[0::2])/max(1,len(pts[0::2])) if pts else 32
    d["cy"] = sum(pts[1::2])/max(1,len(pts[1::2])) if pts else 32
    return d

def vec(d):
    """Shape signature, not a feature count.

    v1 compared element counts, which made every one-element mark identical —
    'sparkle' and 'flame' both scored 1.0000 because both are a single <path>.
    This bins actual geometry into an 8x8 occupancy grid, so the comparison is
    about WHERE the ink is, plus a path-command histogram for stroke character.
    """
    g = [0.0]*64
    pts = d["pts"]
    for x, y in zip(pts[0::2], pts[1::2]):
        gx = min(7, max(0, int(x / 8)))
        gy = min(7, max(0, int(y / 8)))
        g[gy*8 + gx] += 1.0
    tot = sum(g) or 1.0
    g = [v/tot for v in g]
    cmds = d["cmds"]
    ctot = sum(cmds.values()) or 1
    g += [cmds.get(c,0)/ctot*0.5 for c in "MCLQAZ"]      # weighted below geometry
    g += [d["fills"]/max(1,d["n"])*0.3, len(d["colors"])/6*0.3]
    return g


def cos(a,b):
    na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b))/(na*nb) if na and nb else 0

def bar(frac, w=26):
    f=int(round(frac*w)); return "█"*f + "·"*(w-f)

def main():
    d = sys.argv[1]
    files = sorted(glob.glob(os.path.join(d, "*.svg")))
    if not files: sys.exit(f"no marks in {d}")
    M = [parse(f) for f in files]
    N = len(M)
    print(f"\n╭─ {os.path.basename(d.rstrip('/'))} — {N} marks")

    tot = Counter()
    for m in M: tot.update(m["elems"])
    allE = sum(tot.values())
    print(f"├─ ELEMENT MIX  ({allE} elements, {allE/N:.1f} per mark)")
    for e in ELEMS:
        f = tot.get(e,0)/allE if allE else 0
        print(f"│    {e:<9} {bar(f)} {f*100:5.1f}%  ({tot.get(e,0)})")

    comp = Counter(m["n"] for m in M)
    print(f"├─ COMPLEXITY   min {min(m['n'] for m in M)} · "
          f"median {sorted(m['n'] for m in M)[N//2]} · max {max(m['n'] for m in M)}")
    for k in sorted(comp):
        print(f"│    {k:>2} elem  {bar(comp[k]/N)} {comp[k]}")

    st = [x for m in M for x in m["stroke"]]
    if st:
        st_s = sorted(st)
        print(f"├─ STROKE       min {min(st)} · median {st_s[len(st)//2]} · max {max(st)}")
        buckets = [(0,1),(1,2),(2,3),(3,5),(5,99)]
        for lo,hi in buckets:
            c = sum(1 for x in st if lo<=x<hi)
            print(f"│    {lo}–{hi if hi<99 else '+':<4} {bar(c/len(st))} {c/len(st)*100:5.1f}%")

    op = [x for m in M for x in m["opacity"]]
    if op:
        print(f"├─ OPACITY      {len(op)} explicit values, {len(op)/N:.1f} per mark")
        for lo,hi,lab in [(0,.16,'ghost .00–.15'),(.16,.30,'second .16–.29'),
                          (.30,.56,'primary .30–.55'),(.56,1.01,'loud .56–1.0')]:
            c=sum(1 for x in op if lo<=x<hi)
            print(f"│    {lab:<15} {bar(c/len(op))} {c/len(op)*100:5.1f}%")
    else:
        print("├─ OPACITY      none declared — flat field, all weight from stroke/fill")

    cu = Counter(c for m in M for c in m["colors"])
    print(f"├─ PALETTE      {len(cu)} distinct colours")
    for c,k in cu.most_common():
        print(f"│    {c}  {bar(k/N)} {k/N*100:5.1f}% of marks")
    pc = Counter(len(m["colors"]) for m in M)
    print(f"│    colours/mark: " + " · ".join(f"{k}→{pc[k]}" for k in sorted(pc)))
    nf = sum(1 for m in M if m["fills"]>0)
    print(f"│    marks using fill: {nf}/{N} ({nf/N*100:.0f}%)")

    spans = [m["bbox"][1]-m["bbox"][0] for m in M]
    print(f"├─ COVERAGE     span of the 64px box: min {min(spans):.0f} · "
          f"mean {sum(spans)/N:.0f} · max {max(spans):.0f}")
    off = sum(1 for m in M if abs(m['cx']-32)>7 or abs(m['cy']-32)>7)
    print(f"│    off-centre marks: {off}/{N} ({off/N*100:.0f}%)  "
          f"— some asymmetry keeps the field alive")

    if "--dupes" in sys.argv:
        V=[vec(m) for m in M]; pairs=[]
        for i in range(N):
            for j in range(i+1,N):
                s=cos(V[i],V[j])
                if s>0.86: pairs.append((s,M[i]["file"],M[j]["file"]))
        pairs.sort(reverse=True)
        print(f"├─ NEAR-DUPES   {len(pairs)} pairs above 0.86 spatial similarity  ({len(pairs)/max(1,N)*100:.0f}% of N)")
        for s,a,b in pairs[:12]:
            print(f"│    {s:.4f}  {a}  ≈  {b}")
    print("╰─\n")

if __name__ == "__main__":
    main()
