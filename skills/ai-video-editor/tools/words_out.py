#!/usr/bin/env python3
"""words_out.py <edit_dir> — every word said in the CUT with its output time → work/words_out.json [{i, w, t, e}] + words_out.txt.
Run after island_cut.py and aroll_audio.py (cut.py writes words_out.json itself).

The words come from keep.json (spelled the way you mean them: product names, numbers), their TIMES from whisper's whole-file
DTW pass over the cut (work/rep/cut_whole.json — made here if it is missing, from work/aroll_check16k.wav). The two are
aligned token by token (difflib; spelling variants folded: number words, gonna/going, plus AI_EDITOR_HOME/folds.json);
a word the ASR missed gets a time between its neighbours. DTW onsets run ~0.2–0.3 s late, so each onset is moved back to
the voice onset it belongs to: the last quiet→voice edge in [t − 0.45, t + 0.05] of the cut's own voice, else t − 0.12.
The plan's T("phrase") anchors and every graphic's word timing read this file."""
import difflib, json, os, re, shutil, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__)
E = os.path.abspath(sys.argv[1]); os.chdir(E)
SR = 48000
FOLD = {"gonna": "going", "wanna": "want", "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
        "seven": "7", "eight": "8", "nine": "9", "ten": "10", "okay": "ok"}
FOLD.update(aie.folds())


def norm(w):
    w = re.sub(r"[^a-z0-9%$]", "", w.lower().replace("'", ""))
    return FOLD.get(w, w)


wav = "work/aroll_check.wav"           # aroll_audio.py: the same trims and fades as the A-roll's voice, never half-written
if not os.path.exists(wav): sys.exit("no work/aroll_check.wav: run aroll_audio.py first")
CW = "work/rep/cut_whole.json"
if not os.path.exists(CW) or os.path.getmtime(CW) < os.path.getmtime(wav):
    os.makedirs("work/rep", exist_ok=True)
    model = aie.need_model()
    dtw = os.path.basename(model)[5:-4] if os.path.basename(model).startswith("ggml-") else "medium.en"
    subprocess.run((["nice", "-n", "10"] if shutil.which("nice") else []) +
                   [aie.whisper_cli(), "-m", model, "-f", "work/aroll_check16k.wav", "--dtw", dtw, "-nfa", "-ojf", "-of", CW[:-5], "-np"],
                   check=True, stdout=subprocess.DEVNULL)
K = json.load(open("keep.json"))["keep"]
words = [w for r in K for w in r[2].replace("…", " ").split()]
asr = []
for seg in json.load(open(CW))["transcription"]:
    for tk in seg.get("tokens", []):
        tx = tk["text"]
        if tx.startswith("[_") or not tx.strip(): continue
        t = tk["t_dtw"] / 100 if tk.get("t_dtw", -1) >= 0 else tk["offsets"]["from"] / 1000
        if tx.startswith(" ") or not asr: asr.append({"w": tx.strip(), "t": t})
        else: asr[-1]["w"] += tx
A = [norm(x["w"]) for x in asr]; B = [norm(w) for w in words]
sm = difflib.SequenceMatcher(a=B, b=A, autojunk=False)
T = [None] * len(words)
for blk in sm.get_matching_blocks():
    for k in range(blk.size): T[blk.a + k] = asr[blk.b + k]["t"]
known = [i for i, t in enumerate(T) if t is not None]
if not known: sys.exit("no word of keep.json was heard in the cut: is keep.json the cut that aroll_audio.py made?")
for i in range(len(T)):                                 # fill the gaps by interpolation between known neighbours
    if T[i] is None:
        lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
        if lo is None: T[i] = max(0.0, T[hi] - 0.25 * (hi - i))
        elif hi is None: T[i] = T[lo] + 0.25 * (i - lo)
        else: T[i] = T[lo] + (T[hi] - T[lo]) * (i - lo) / (hi - lo)
# onset correction on the cut's own voice
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout, np.float32).astype(np.float64)
hop = SR // 100; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12))
thr = min(-40.0, float(np.percentile(db, 95)) - 20.0)  # the voice threshold the cut tools use, measured on this voice
loud = db > thr
on = np.array([f for f in range(3, n) if loud[f] and not loud[f - 3:f].any()]) / 100.0   # ≥ 30 ms of quiet, then voice
fixed = []
for i, t in enumerate(T):
    c = on[(on >= t - 0.45) & (on <= t + 0.05)] if len(on) else on
    tt = float(c[-1]) if len(c) else t - 0.12
    if fixed and tt <= fixed[-1] + 0.04: tt = max(t - 0.12, fixed[-1] + 0.06)   # never before the previous word
    fixed.append(round(max(0.0, tt), 3))
out = []
for i, (w, t) in enumerate(zip(words, fixed)):
    e = fixed[i + 1] if i + 1 < len(fixed) else t + 0.4
    out.append({"i": i, "w": w, "t": t, "e": round(min(e, t + 1.2), 3)})
json.dump(out, open("work/words_out.json", "w"))
open("work/words_out.txt", "w").write(" ".join(w["w"] for w in out) + "\n")
miss = sum(1 for k in range(len(words)) if k not in known)
print(f"{len(out)} words · {miss} interpolated · last at {out[-1]['t']:.2f} s · voice threshold {thr:.1f} dB")
