#!/usr/bin/env python3
"""islands.py <edit_dir> [--from S] [--to S] [--quiet 0.25] — the take as SPEECH ISLANDS: the reading view for choosing what to keep.

An island = voice between quiet runs of ≥ 0.25 s (the voice threshold: −40 dB, or p95 − 20 dB on a quiet take).
Per island: its index, source start–end, the pause before it, and its words — the verbatim pass (work/rep/literal.json, from
literal_asr.py: repeats and restarts written out) and, when it differs, whisper's whole-file words (work/audio/words.json).
Read it top to bottom; for each idea keep the LAST clean take of it; write the keep list (keep.json, see island_cut.py).
Writes work/islands.json."""
import argparse, json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__)
ap = argparse.ArgumentParser(); ap.add_argument("edit"); ap.add_argument("--from", dest="t0", type=float, default=0)
ap.add_argument("--to", dest="t1", type=float, default=1e9); ap.add_argument("--quiet", type=float, default=0.25)
a = ap.parse_args()
E = os.path.abspath(a.edit); os.chdir(E)
SR = 48000
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", "work/audio/take48k.wav", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32).astype(np.float64)
hop = SR // 100; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12))
thr = min(-40.0, float(np.percentile(db, 95)) - 20.0)
loud = db > thr
Q = int(round(a.quiet * 100))
isl, s, run = [], None, 0
for f in range(n):
    if loud[f]:
        if s is None: s = f
        run = 0
    elif s is not None:
        run += 1
        if run >= Q: isl.append([s / 100, (f - run + 1) / 100]); s = None; run = 0
if s is not None: isl.append([s / 100, n / 100])
isl = [i for i in isl if i[1] - i[0] >= 0.06]              # a click or a breath tick is not speech
lit = json.load(open("work/rep/literal.json")) if os.path.exists("work/rep/literal.json") else []
whs = [{"w": w["w"], "t": w["t"], "e": w["e"]} for w in json.load(open("work/audio/words.json"))]
if not lit: print("(no work/rep/literal.json yet — run literal_asr.py on work/audio/take16k.wav to see repeats written out)")


def words_in(ws, a0, a1):
    return " ".join(w["w"] for w in ws if a0 - 0.12 <= (w["t"] + w["e"]) / 2 <= a1 + 0.12)


out, prev = [], 0.0
for k, (i0, i1) in enumerate(isl):
    out.append(dict(k=k, t0=i0, t1=i1, gap=round(i0 - prev, 2), lit=words_in(lit, i0, i1), whisper=words_in(whs, i0, i1)))
    prev = i1
json.dump(out, open("work/islands.json", "w"), indent=0)
print(f"voice threshold {thr:.1f} dB · {len(out)} islands")
norm = lambda s: s.lower().replace(",", "").replace(".", "").replace("?", "").replace("!", "")
for o in out:
    if o["t1"] < a.t0 or o["t0"] > a.t1: continue
    g = f"{o['gap']:5.2f}" if o["gap"] < 99 else " long"
    print(f"{o['k']:4d} {o['t0']:8.2f}–{o['t1']:8.2f} gap{g} | {o['lit'] or o['whisper'] or '∅'}")
    if o["lit"] and o["whisper"] and norm(o["whisper"]) != norm(o["lit"]):
        print(f"{'':34s}   whisper: {o['whisper']}")
