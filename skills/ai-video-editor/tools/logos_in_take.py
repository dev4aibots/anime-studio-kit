#!/usr/bin/env python3
"""logos_in_take.py <edit_dir> — every brand named in the CUT, when, and what is on screen then, so each one gets its logo.
The rule (STYLE.md "Logos"): name it, show it — the real mark, in 3D where it fits; it makes the edit feel alive.
Brands and the words used for them: gfxlib/logos/logos.json ("says" + whisper's "mishears"; add your own brands there).
On screen: read from out/plan.txt (run assemble.py --plan first). A mention on the FACE wants a sticker
(cut(…, layout="sticker"), a clip from gfxlib/logo_clip.py); one inside a graphic wants the logo IN the graphic (logo3d/logoSVG).
Mentions of the same brand closer than 4 s are one window."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)
E = os.path.abspath(sys.argv[1]); SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(f"{SK}/gfxlib/logos/logos.json"))
W = [x for x in json.load(open(f"{E}/work/words_out.json")) if x["t"] is not None]
nw = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
pats = sorted(((tuple(nw(t) for t in s.split()), k) for k, v in L.items() for s in v["says"] + v.get("mishears", []) if s.strip()),
              key=lambda x: -len(x[0]))
hits, i = [], 0
while i < len(W):
    for toks, k in pats:
        if i + len(toks) <= len(W) and all(nw(W[i + j]["w"]) == toks[j] for j in range(len(toks))):
            hits.append((W[i]["t"], k, " ".join(W[i + j]["w"] for j in range(len(toks))))); i += len(toks) - 1; break
    i += 1
plan = []
if os.path.exists(f"{E}/out/plan.txt"):
    for ln in open(f"{E}/out/plan.txt"):
        m = re.match(r"\s*([\d.]+)\s+([\d.]+)s\s+(.*)", ln)
        if m: plan.append((float(m[1]), float(m[2]), m[3].strip()))
on = lambda t: next((w for a, d, w in plan if a <= t < a + d), "?")   # note: OUTPUT time; equal to A-roll time when there is no insert
win = []
for t, k, said in hits:
    if win and win[-1][1] == k and t - win[-1][3] < 4.0: win[-1][3] = t; win[-1][4].append(said)
    else: win.append([t, k, said, t, [said]])
print(f"{len(hits)} mentions · {len(win)} logo windows · {len(set(k for _, k, _ in hits))} brands")
for a, k, said, b, all_ in win:
    what = on(a); face = what.startswith("face")
    print(f"{a:7.2f}–{b + 1.5:7.2f}  {k:13s} {said!r:22s} on screen: {what[:60]}{'  → STICKER (on the face)' if face and '+ logo' not in what else ''}")
