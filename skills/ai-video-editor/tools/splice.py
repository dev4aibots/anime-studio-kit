#!/usr/bin/env python3
"""splice.py <edit_dir> <t0> <t1> [--asr] — everything needed to place a cut INSIDE an island (a filler, a stutter, a splice
between two takes), in source seconds of the take: whisper's words with their times, the verbatim pass's words
(work/rep/literal.json), an energy strip (one character per 20 ms: # loud, + mid, - low, . under the voice threshold), the
quiet runs and the deep dips inside the voice. --asr also re-transcribes the span word by word (-ml 1), so a word both
passes missed shows up. Put the edge you find into keep.json (5th item "in"/"out"/"both" keeps it exactly)."""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__, need=3)
ap = argparse.ArgumentParser(); ap.add_argument("edit"); ap.add_argument("t0", type=float); ap.add_argument("t1", type=float)
ap.add_argument("--asr", action="store_true")
a = ap.parse_args()
E = os.path.abspath(a.edit); os.chdir(E)
SR = 48000
full = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "work/audio/take48k.wav", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                                    capture_output=True, check=True).stdout, np.float32).astype(np.float64)
h8 = 80; n8 = len(full) // h8
db8 = 20 * np.log10(np.sqrt((full[: n8 * h8].reshape(n8, h8) ** 2).mean(axis=1) + 1e-12))
THR = min(-40.0, float(np.percentile(db8, 95)) - 20.0)       # the take's own voice threshold (≈ island_cut.py's, measured at 8 kHz)
pcm = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.t0), "-t", str(a.t1 - a.t0), "-i", "work/audio/take48k.wav",
                      "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32).astype(np.float64)
hop = SR // 100; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12))
ws = [w for w in json.load(open("work/audio/words.json")) if a.t0 - 0.3 <= w["t"] <= a.t1 + 0.3]
print("WHSP   " + "  ".join(f"{w['w']}[{w['t']:.2f}]" for w in ws))
if os.path.exists("work/rep/literal.json"):
    lit = [w for w in json.load(open("work/rep/literal.json")) if a.t0 - 0.3 <= w["t"] <= a.t1 + 0.3]
    print("LIT    " + "  ".join(f"{w['w']}[{w['t']:.2f}-{w['e']:.2f}]" for w in lit))
strip = ""
for i in range(0, n, 2):
    v = db[i:i + 2].mean()
    strip += "#" if v > THR + 18 else ("+" if v > THR + 6 else ("-" if v > THR else "."))
for k in range(0, len(strip), 100):
    print(f"E {a.t0 + k * 0.02:8.2f} {strip[k:k + 100]}")
runs, s = [], None
for i in range(n):
    q = db[i] <= THR
    if q and s is None: s = i
    if not q and s is not None:
        if i - s >= 3: runs.append((a.t0 + s / 100, a.t0 + i / 100))
        s = None
print(f"QUIET  (threshold {THR:.1f} dB) " + "  ".join(f"{p:.2f}-{q:.2f}" for p, q in runs))
mins = []
for i in range(3, n - 3):
    if db[i] == db[i - 3:i + 4].min() and db[i] > THR and db[i - 3:i + 4].max() - db[i] >= 12:
        mins.append(f"{a.t0 + i / 100:.2f}({db[i]:.0f})")
print("DIPS   " + "  ".join(mins))
if a.asr:
    d = tempfile.mkdtemp(prefix="spl_")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.t0), "-t", str(a.t1 - a.t0), "-i", "work/audio/take16k.wav", f"{d}/x.wav"], check=True)
    M = aie.need_model()
    DTW = os.path.basename(M)[5:-4] if os.path.basename(M).startswith("ggml-") else "medium.en"
    subprocess.run([aie.whisper_cli(), "-m", M, "-f", f"{d}/x.wav", "--dtw", DTW, "-nfa", "-ojf", "-of", f"{d}/x", "-np",
                    "-mc", "0", "--prompt", aie.prompt()], capture_output=True)
    out = []
    for seg in json.load(open(f"{d}/x.json"))["transcription"]:
        for tk in seg.get("tokens", []):
            tx = tk["text"]
            if tx.startswith("[_") or not tx.strip(): continue
            t = a.t0 + (tk["t_dtw"] / 100 if tk.get("t_dtw", -1) >= 0 else tk["offsets"]["from"] / 1000)
            if tx.startswith(" ") or not out: out.append([tx.strip(), t])
            else: out[-1][0] += tx
    print("ASR    " + "  ".join(f"{w}[{t:.2f}]" for w, t in out))
