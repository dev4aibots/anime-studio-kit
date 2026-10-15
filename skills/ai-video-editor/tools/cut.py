#!/usr/bin/env python3
"""cut.py <edit_dir> — the quick cut for a CLEAN take (no retakes): remove word ranges, edges on the WAVEFORM, never on a word stamp.
A take full of retakes and restarts is cut from a keep list instead: islands.py → keep.json → island_cut.py.

Reads  edit/work/audio/words.json + take48k.wav, and edit/cutfix.json (optional):
  {"remove":  [[first_word_index, last_word_index, "why"], …],      fact-check cuts and flubs (indices from read.txt)
   "src_keep": [[t0, t1, "why"], …], "src_cut": [[t0, t1, "why"], …]   source spans forced in / out, measured on the waveform
   "src_fix": [[current_segment_start_s, corrected_start_s, "why"], …]}   splices measured on the waveform when whisper's
                                                                         stamps were wrong (verify_cut.py finds them)
Writes edit/work/edl.json [{src_in, src_out, out_in}] and edit/work/words_out.json (every kept word's OUTPUT time).
Then: assemble_aroll.py, and ALWAYS verify_cut.py — a removal that leaks is a false claim shipped."""
import json, os, subprocess, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)

E = os.path.abspath(sys.argv[1]); os.chdir(E)
FPS = 30
SR = 48000
fix = json.load(open("cutfix.json")) if os.path.exists("cutfix.json") else {}
REMOVE = [(r[0], r[1]) for r in fix.get("remove", [])]
SRC_FIX = [(r[0], r[1]) for r in fix.get("src_fix", [])]
SRC_KEEP = [(r[0], r[1]) for r in fix.get("src_keep", [])]   # [t0, t1, why]: source spans that MUST be in the cut (a word the
                                                              # 150 ms rule dropped: "two point … five" has a pause inside it)
SRC_CUT = [(r[0], r[1]) for r in fix.get("src_cut", [])]     # [t0, t1, why]: source spans that must NOT be (a word whisper
                                                              # stamped wrong, a bump, music from the room) — measured on the waveform

w = json.load(open("work/audio/words.json"))
drop = set(i for a, b in REMOVE for i in range(a, b + 1))

# energy envelope (10 ms) of the voice
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", "work/audio/take48k.wav", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32).astype(np.float64)
hop = SR // 100
n = len(x) // hop
rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
db = 20 * np.log10(rms)
floor = np.percentile(db, 8)
p95 = float(np.percentile(db, 95))
thr = min(-40.0, p95 - 20.0)                        # voice vs pause: -40 dB on a normal take (speech -20..-30, p95 ≈ -20).
                                                    # A quiet take follows its own level (one take: speech median -46 dB, p95 -33 →
                                                    # thr -53; a fixed -40 dropped 58 kept words).
loud = db > thr

QUIET = 15                                            # 150 ms of quiet = the voice has stopped (stop closures are shorter)

def voice_end(t_word, t_limit):
    """A's sound ends where the first 150 ms of quiet begins after A started (searching up to t_limit)"""
    a, b = int((t_word + 0.12) * 100), min(int(t_limit * 100), len(loud))
    run = 0
    for f in range(a, max(a, b)):
        run = run + 1 if not loud[f] else 0
        if run >= QUIET: return (f - QUIET + 1) / 100
    return None                                       # no real silence before the next word

def voice_start(t_from, t_word):
    """B's sound starts where the last 150 ms of quiet before B ends"""
    a, b = int(t_from * 100), min(int((t_word + 0.06) * 100), len(loud) - 1)
    run = 0
    for f in range(b, a, -1):
        run = run + 1 if not loud[f] else 0
        if run >= QUIET: return (f + QUIET) / 100
    return None

def quietest(lo, hi):
    """the quietest 10 ms between lo and hi — where to cut when there is no pause at all"""
    a, b = int(lo * 100), max(int(lo * 100) + 1, min(int(hi * 100), len(db)))
    return (a + int(np.argmin(db[a:b]))) / 100

kept = [i for i in range(len(w)) if i not in drop]
segs = []                                             # [src_in, src_out]
seg_start = max(0.0, (voice_start(0.0, w[kept[0]]["t"]) or w[kept[0]]["t"]) - 0.06)
for k in range(len(kept) - 1):
    i, j = kept[k], kept[k + 1]
    a, b = w[i], w[j]
    contiguous = (j == i + 1)
    if not contiguous:
        # removed words between A and B. A's sound must end BEFORE the first removed word and B's must start AFTER the
        # last one — searching A→B whole found the pause after the removed words and kept them (a false "30 minutes"
        # claim, "page,", "So" and "the conversation." all survived a first cut that way)
        r0, r1 = w[i + 1], w[j - 1]
        a_end = voice_end(a["t"], r0["t"] + 0.05)
        # no pause at all: cut at the quietest point between the end of one word and the onset of the next (never inside a word)
        out_a = min(a_end + 0.07, r0["t"]) if a_end is not None else quietest(max(a["t"] + 0.12, a.get("e", a["t"]) - 0.05), r0["t"] + 0.08)
        b_start = voice_start(r1["t"] + 0.1, b["t"])
        in_b = b_start - 0.06 if b_start is not None else quietest(max(r1["t"] + 0.1, r1.get("e", r1["t"]) - 0.05), b["t"] + 0.04)
        segs.append([seg_start, out_a]); seg_start = max(in_b, out_a)
        continue
    # where A's sound ends: search from A's start to B's start; where B's sound begins: search back from B's start
    a_end = voice_end(a["t"], b["t"])
    b_start = voice_start(a_end, b["t"]) if a_end is not None else None
    if a_end is None or b_start is None or b_start <= a_end:
        if not contiguous: segs.append([seg_start, b["t"] - 0.02]); seg_start = b["t"] - 0.02   # removed words, no silence: hard cut at B
        continue
    gap = b_start - a_end
    sentence = a["w"].endswith((".", "?", "!"))
    keep_gap = 0.30 if sentence else 0.16             # the breath we leave
    if contiguous and gap <= keep_gap + 0.06:
        continue                                      # natural flow: no cut
    out_a = a_end + (0.12 if sentence else 0.07)
    in_b = b_start - (0.10 if sentence else 0.06)
    if not contiguous or in_b - out_a > 0.04:
        segs.append([seg_start, out_a]); seg_start = in_b
last = w[kept[-1]]
segs.append([seg_start, (voice_end(last["t"], last["t"] + 2.5) or last["t"] + 0.6) + 0.35])

# frame-align, drop slivers, merge overlaps
fa = lambda t: round(t * FPS) / FPS
segs = [[fa(a), fa(b)] for a, b in segs]
clean = []
for a, b in segs:
    if b - a < 2 / FPS: continue
    if clean and a <= clean[-1][1]: clean[-1][1] = max(clean[-1][1], b)
    else: clean.append([a, b])
# waveform-measured splice fixes from cutfix.json (current segment start → corrected start, source seconds)
for old, new in SRC_FIX:
    for k, (a, b) in enumerate(clean):
        if abs(a - old) < 0.05 and (k == 0 or new > clean[k - 1][1]): clean[k][0] = fa(new)
# measured keeps and cuts (source seconds), applied last so they win over everything above
for k0, k1 in SRC_KEEP:
    clean.append([fa(k0), fa(k1)])
clean.sort(); merged = []
for a, b in clean:
    if merged and a <= merged[-1][1] + 0.05: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
for c0, c1 in SRC_CUT:
    c0, c1 = fa(c0), fa(c1); out = []
    for a, b in merged:
        if b <= c0 or a >= c1: out.append([a, b]); continue
        if a < c0: out.append([a, c0])
        if b > c1: out.append([c1, b])
    merged = out
clean = [[a, b] for a, b in merged if b - a >= 2 / FPS]
edl, t = [], 0.0
for a, b in clean:
    edl.append({"src_in": a, "src_out": b, "out_in": round(t, 4)}); t += b - a
json.dump(edl, open("work/edl.json", "w"), indent=0)

def to_out(ts, te=None):
    for e in edl:
        if e["src_in"] - 1e-6 <= ts <= e["src_out"] + 1e-6: return e["out_in"] + ts - e["src_in"]
    if te is not None:                                # whisper often stamps a word early: one that ENDS inside a segment
        for e in edl:                                 # starts at that segment's start ("Okay," at 431.94, heard at 432.36)
            if e["src_in"] < te <= e["src_out"] + 1e-6: return e["out_in"]
    return None
wo = [{"i": i, "w": w[i]["w"], "t": to_out(w[i]["t"], w[i].get("e"))} for i in kept]
json.dump(wo, open("work/words_out.json", "w"))
src_len = w[-1]["e"]
print(f"{len(edl)} segments · {t:.1f} s out of {src_len:.1f} s ({src_len - t:.1f} s removed) · noise floor {floor:.1f} dB · voice threshold {thr:.1f} dB")
missing = [x for x in wo if x["t"] is None]
print("words outside the cut:", len(missing), [m["w"] for m in missing[:12]])
