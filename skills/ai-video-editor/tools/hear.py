#!/usr/bin/env python3
"""hear.py <edit_dir> <wav> <t0> <t1> [<t0> <t1> …] — what whisper hears in spans of a cut (DTW word times, no context carried):
the check for one splice at a time. Times are seconds in <wav> (e.g. work/aroll_check.wav, output time)."""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__, need=4)
os.chdir(os.path.abspath(sys.argv[1])); wav = sys.argv[2]; xs = [float(v) for v in sys.argv[3:]]
M = aie.need_model()
DTW = os.path.basename(M)[5:-4] if os.path.basename(M).startswith("ggml-") else "medium.en"
d = tempfile.mkdtemp(prefix="hear_")
for k in range(0, len(xs) - 1, 2):
    t0, t1 = xs[k], xs[k + 1]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-t", str(t1 - t0), "-i", wav, "-ac", "1", "-ar", "16000", f"{d}/x.wav"], check=True)
    subprocess.run([aie.whisper_cli(), "-m", M, "-f", f"{d}/x.wav", "--dtw", DTW, "-nfa", "-ojf", "-of", f"{d}/x", "-np", "-mc", "0",
                    "--prompt", aie.prompt()], capture_output=True)
    out = []
    for seg in json.load(open(f"{d}/x.json"))["transcription"]:
        for tk in seg.get("tokens", []):
            tx = tk["text"]
            if tx.startswith("[_") or not tx.strip(): continue
            t = t0 + (tk["t_dtw"] / 100 if tk.get("t_dtw", -1) >= 0 else tk["offsets"]["from"] / 1000)
            if tx.startswith(" ") or not out: out.append([tx.strip(), t])
            else: out[-1][0] += tx
    print(f"{t0:7.2f}–{t1:7.2f}: " + " ".join(w for w, _ in out))
