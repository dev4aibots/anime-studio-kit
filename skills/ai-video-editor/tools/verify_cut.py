#!/usr/bin/env python3
"""verify_cut.py <edit_dir> — after cut.py, never skipped: prove the cut says what we think it says.

1. Every removal in cutfix.json: the cut around it is re-transcribed and printed — the removed words must be GONE and the
   words either side INTACT. (On one video, four of five removals had leaked before this check existed, a false number among them.)
2. The whole A-roll is re-transcribed and diffed against the intended words (words_out.json). Only spelling variants
   ("$0" / "zero dollars") may differ; a missing or extra word is a clipped word or a leak.
If something leaks, find the true boundary with a word-level re-transcription of the TAKE around it
(`whisper-cli … -ml 1`) and add a src_fix to cutfix.json, then cut.py → assemble_aroll.py → this again."""
import difflib, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)

E = os.path.abspath(sys.argv[1]); os.chdir(E)
M = aie.need_model()
TMP = os.path.join(E, "work", "_verify"); os.makedirs(TMP, exist_ok=True)
w = json.load(open("work/audio/words.json"))
wo = {x["i"]: x["t"] for x in json.load(open("work/words_out.json")) if x["t"] is not None}

def hear(ss, t, wav="work/aroll.wav"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, ss)), "-t", str(t), "-i", wav, "-ac", "1", "-ar", "16000", f"{TMP}/x.wav"], check=True)
    subprocess.run([aie.whisper_cli(), "-m", M, "-f", f"{TMP}/x.wav", "-oj", "-of", f"{TMP}/x", "-np"], capture_output=True)
    return " ".join(s["text"].strip() for s in json.load(open(f"{TMP}/x.json"))["transcription"])

fix = json.load(open("cutfix.json")) if os.path.exists("cutfix.json") else {}
print("1 · removals")
for r in fix.get("remove", []):
    a, b = r[0], r[1]
    ta, tb = wo.get(a - 1), wo.get(b + 1)
    if ta is None or tb is None: print(f"   [{a}-{b}] can't place it (neighbours unmapped)"); continue
    gone = " ".join(x["w"] for x in w[a:b + 1])
    print(f"   removed {gone[:48]!r:52} → heard: {hear(ta - 1.2, tb - ta + 2.4)!r}")

print("2 · the whole A-roll against the intended words")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/aroll.wav", "-ac", "1", "-ar", "16000", f"{TMP}/all.wav"], check=True)
subprocess.run([aie.whisper_cli(), "-m", M, "-f", f"{TMP}/all.wav", "-oj", "-of", f"{TMP}/all", "-np"], capture_output=True)
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
want = [x["w"] for x in json.load(open("work/words_out.json"))]
got = " ".join(s["text"] for s in json.load(open(f"{TMP}/all.json"))["transcription"]).split()
sm = difflib.SequenceMatcher(a=[norm(x) for x in want], b=[norm(x) for x in got], autojunk=False)
print(f"   intended {len(want)} words · heard {len(got)} · similarity {sm.ratio():.3f}")
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != "equal":
        print(f"   {op:8s} …{' '.join(want[max(0, i1 - 4):i1])[-40:]} | want {' '.join(want[i1:i2])[:50]!r} | heard {' '.join(got[j1:j2])[:50]!r}")
