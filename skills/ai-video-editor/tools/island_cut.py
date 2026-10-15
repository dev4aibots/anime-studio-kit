#!/usr/bin/env python3
"""island_cut.py <edit_dir> — the cut, built from KEEP ranges (edit/keep.json) on the waveform. The main way to cut a take.

cut.py removes word-index ranges, but whisper writes repeats and restarts once, so a take with many retakes (28 min of
take for a 10 min script, ~25 restarts) can't be cut by word indices. Here every range to KEEP is listed in source
seconds, with the words it should say (spelled the way you mean them), and the waveform decides the exact edges:

  {"keep": [[t0, t1, "the words in it", "s"|"m"], …]}      s = it starts a sentence, m = it continues one (a splice)
  optional 5th item: "in" / "out" / "both" — an edge measured by hand (splice.py), used as is, not snapped
  optional 6th item: {"pause": s} — keep this range's inner pauses up to s seconds (a list said slowly, a demo wait)

- an edge in a pause snaps to the voice (the first/last loud 10 ms within 0.6 s) and keeps a natural margin: 0.10 s before
  a sentence, 0.06 s before a continuation; 0.12 s after a sentence end, 0.07 s after a word mid-sentence;
- an edge inside the voice (a splice between two takes mid-phrase) cuts at the quietest 10 ms within ±0.06 s;
- inside a range every pause longer than the target is closed up to it: 0.22 s on screen after a sentence, 0.13 s inside
  one (glances down at the script live in those pauses). A stop closure (< 150 ms) is never a pause.
Writes work/edl.json [{src_in, src_out, out_in}] (what assemble_aroll.py and assemble.py read) and work/keep_text.txt (the
intended words, in order, for the verification diff). Example: templates/keep.example.json."""
import json, os, re, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)

E = os.path.abspath(sys.argv[1]); os.chdir(E)
FPS, SR = 30, 48000
K = json.load(open("keep.json"))
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", "work/audio/take48k.wav", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32).astype(np.float64)
hop = SR // 100; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12))
thr = min(-40.0, float(np.percentile(db, 95)) - 20.0)
loud = db > thr
QUIET = 15                                            # 150 ms of quiet = a pause (stop closures are shorter)

# the voice mask for PAUSES: a loud blip under 50 ms between quiet stretches (a breath tick, a lip smack) is part of the pause
vm = loud.copy()
f = 0
while f < n:
    if vm[f]:
        g = f
        while g < n and vm[g]: g += 1
        if g - f < 5 and f >= 8 and g + 8 <= n and not vm[f - 8:f].any() and not vm[g:g + 8].any(): vm[f:g] = False
        f = g
    else: f += 1
runs, s = [], None
for f in range(n):
    if not vm[f] and s is None: s = f
    if vm[f] and s is not None:
        if f - s >= QUIET: runs.append((s, f))
        s = None
if s is not None and n - s >= QUIET: runs.append((s, n))

def quietest(t, w=0.06):
    a, b = max(0, int((t - w) * 100)), min(n, int((t + w) * 100) + 1)
    return (a + int(np.argmin(db[a:b]))) / 100

def snap_in(t, sent):
    """a range's start: in a pause → the next voice onset minus a margin, never back into the previous voice;
    inside the voice (a splice mid-phrase) → the quietest 10 ms within ±60 ms"""
    pre = 0.10 if sent else 0.06
    f = int(round(t * 100))
    if loud[min(n - 1, f)]: return quietest(t)
    g = f
    while g < min(n, f + 60) and not loud[g]: g += 1
    p = f
    while p > 0 and not loud[p - 1]: p -= 1                 # p = first quiet frame after the previous voice
    return max(g / 100 - pre, p / 100 + 0.02)

def snap_out(t, sent):
    """a range's end: in a pause → the last voice (a stop's release burst included) plus a margin, never into the next
    voice; inside the voice → the quietest 10 ms within ±60 ms"""
    post = 0.12 if sent else 0.07
    f = int(round(t * 100))
    if loud[min(n - 1, f)]: return quietest(t)
    g = f
    while g > max(0, f - 60) and not loud[g]: g -= 1
    off = g + 1                                             # first quiet frame after the voice
    # a release burst (≤ 70 ms of voice) within 100 ms after a closure belongs to the word ("cost" keeps its t)
    k = off
    while k < min(n, off + 10) and not loud[k]: k += 1
    if k < min(n, off + 10):
        e = k
        while e < n and loud[e]: e += 1
        if e - k <= 7 and not loud[e:min(n, e + 6)].any(): off = e
    nxt = off
    while nxt < n and not loud[nxt]: nxt += 1               # the next voice
    return min(off / 100 + post, nxt / 100 - 0.02)

lit = json.load(open("work/rep/literal.json")) if os.path.exists("work/rep/literal.json") else []
def sentence_end_before(f):
    """does the word that ends just before frame f end a sentence? (the verbatim pass's punctuation)"""
    t = f / 100
    c = [w for w in lit if w["e"] <= t + 0.15 and w["e"] >= t - 1.5]
    w = c[-1]["w"].rstrip() if c else ""
    return w.endswith((".", "?", "!")) and not w.endswith("...")     # "in..." is a held breath, not a full stop

segs, text = [], []
for r in K["keep"]:
    t0, t1, words, kind = r[0], r[1], r[2], (r[3] if len(r) > 3 else "s")
    exact = r[4] if len(r) > 4 else ""                  # "in" / "out" / "both": an edge measured by hand (splice.py), not snapped
    opt = r[5] if len(r) > 5 else {}                    # {"pause": s}: keep this range's inner pauses up to s (a list said slowly)
    ends_sentence = words.rstrip().endswith((".", "?", "!"))
    a = t0 if exact in ("in", "both") else snap_in(t0, kind == "s")
    b = t1 if exact in ("out", "both") else snap_out(t1, ends_sentence)
    # close up the long pauses inside the range
    cur = a; cur_x = exact in ("in", "both")
    for q0, q1 in runs:
        qa, qb = q0 / 100, q1 / 100
        if qa <= a + 0.02 or qb >= b - 0.02: continue
        sent = sentence_end_before(q0)
        post, pre = (0.12, 0.10) if sent else (0.07, 0.06)
        if opt.get("pause"): post, pre = max(post, 0.55 * opt["pause"]), max(pre, 0.45 * opt["pause"])
        if qb - qa > post + pre + 0.06:
            segs.append([cur, qa + post, cur_x, False]); cur = qb - pre; cur_x = False
    segs.append([cur, b, cur_x, exact in ("out", "both")])
    text.append(words)

import math
# whole frames: the nearest one, except a hand-set edge, which rounds OUTWARD (a start floors, an end ceils) so it keeps
# ≤ 33 ms of the neighbour rather than losing the first or last consonant of the word it protects
clean = []
for a, b, ax, bx in segs:
    a = math.floor(a * FPS + 1e-6) / FPS if ax else round(a * FPS) / FPS
    b = math.ceil(b * FPS - 1e-6) / FPS if bx else round(b * FPS) / FPS
    if b - a < 2 / FPS: continue
    if clean and a <= clean[-1][1]: clean[-1][1] = max(clean[-1][1], b)
    else: clean.append([a, b])
edl, t = [], 0.0
for a, b in clean:
    edl.append({"src_in": round(a, 4), "src_out": round(b, 4), "out_in": round(t, 4)}); t += b - a
json.dump(edl, open("work/edl.json", "w"), indent=0)
open("work/keep_text.txt", "w").write(" ".join(text) + "\n")
src = sum(r[1] - r[0] for r in K["keep"])
print(f"{len(K['keep'])} keep ranges → {len(edl)} segments · {t:.1f} s ({t / 60:.2f} min) · voice threshold {thr:.1f} dB")
