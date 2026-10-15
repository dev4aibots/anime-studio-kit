#!/usr/bin/env python3
"""literal_asr.py <wav> <out.json> — a VERBATIM transcription, for finding repeats, restarts and false starts.

Whisper over a long file smooths disfluencies ("and it, and it connects" → "and it connects"). Here the audio is split at
pauses into 3–9 s chunks, each decoded on its own with no carried-over context (-mc 0) and a disfluent prompt, so a phrase
said twice is written twice. → [{w, t, e}] in the wav's own seconds.
Typical uses:
  literal_asr.py edit/work/audio/take16k.wav edit/work/rep/literal.json        the take (islands.py shows it)
  literal_asr.py edit/work/aroll_check16k.wav edit/work/rep/cut_literal.json   the cut (cut_diff.py compares it)
Names you say often (product names) go in AI_EDITOR_HOME/vocab.txt, one per line: they are added to the prompt."""
import json, os, shutil, subprocess, sys, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__, need=2)
SR = 16000
MODEL = aie.need_model()
wav, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                                 capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
hop = SR // 100; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12))
thr = min(-40.0, float(np.percentile(db, 95)) - 20.0)
quiet = db < thr
# cut points: the middle of every pause of >= 0.2 s; then greedily make 3–9 s chunks
runs, s = [], None
for i, q in enumerate(quiet):
    if q and s is None: s = i
    if not q and s is not None:
        if i - s >= 20: runs.append((s + i) / 2 / 100)
        s = None
cuts, last = [0.0], 0.0
for c in runs:
    if c - last >= 3.0:
        if c - last > 9.0:                      # too long without a pause: split it anyway at 8 s steps
            while c - last > 9.0: last += 8.0; cuts.append(last)
        cuts.append(c); last = c
end = n / 100
if end - cuts[-1] > 0.5: cuts.append(end)
tmp = tempfile.mkdtemp(prefix="lit_")
files = []
for k, (a, b) in enumerate(zip(cuts, cuts[1:])):
    f = f"{tmp}/c{k:04d}.wav"
    seg = x[int(a * SR): int(b * SR)]
    with wave.open(f, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(seg, -1, 1) * 32767).astype(np.int16).tobytes())
    files.append((f, a))
words = []
# ONE whisper-cli run over every chunk (the model loads once: loading it per chunk took ~10 s each); with several inputs
# whisper-cli writes <chunk>.wav.json next to each one, and -mc 0 keeps every chunk context-free
cmd = (["nice", "-n", "10"] if shutil.which("nice") else []) + [aie.whisper_cli(), "-m", MODEL, "-mc", "0", "--prompt", aie.prompt(),
                                                                 "-ml", "1", "-sow", "-ojf", "-np"]
for f, a in files: cmd += ["-f", f]
subprocess.run(cmd, capture_output=True)
for f, a in files:
    try: j = json.load(open(f + ".json"))
    except Exception: continue
    for seg in j.get("transcription", []):
        txt = seg.get("text", "").strip()
        if not txt: continue
        t0 = seg["offsets"]["from"] / 1000 + a; t1 = seg["offsets"]["to"] / 1000 + a
        words.append(dict(w=txt, t=round(t0, 2), e=round(t1, 2)))
shutil.rmtree(tmp, ignore_errors=True)
json.dump(words, open(out, "w"))
print(len(files), "chunks ·", len(words), "words →", out)
