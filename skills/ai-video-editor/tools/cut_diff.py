#!/usr/bin/env python3
"""cut_diff.py <edit_dir> [cut_whole.json] [cut_literal.json] — does the cut say what keep.json says it should?

Diffs the cut's transcription against work/keep_text.txt (the intended words, in order, written by island_cut.py) and prints
every difference with its OUTPUT time and the nearest join (work/edl.json), so a clipped word, a leaked restart or a doubled
phrase points straight at the splice that made it. Spelling variants are folded first (number words, gonna/going, and your
AI_EDITOR_HOME/folds.json, e.g. {"cloud": "claude"}).
  cut_whole.json    whisper's whole-file pass over the cut (default work/rep/cut_whole.json — words_out.py makes it)
  cut_literal.json  the verbatim chunked pass (default work/rep/cut_literal.json, if it exists:
                    literal_asr.py work/aroll_check16k.wav work/rep/cut_literal.json). Whisper over a whole file writes a
                    doubled phrase once; the literal pass writes it twice — so only this one catches a repeat you kept.
A difference is not always an error (whisper mishears names); listen to it (hear.py) before you change the cut."""
import difflib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__)
E = os.path.abspath(sys.argv[1]); os.chdir(E)
FOLD = {"gonna": "going", "wanna": "want", "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
        "seven": "7", "eight": "8", "nine": "9", "ten": "10", "okay": "ok", "etcetera": "etc"}
FOLD.update(aie.folds())


def norm(w):
    w = re.sub(r"[^a-z0-9%$]", "", w.lower().replace("'", ""))
    return FOLD.get(w, w)


def toks(text):
    text = text.replace("/", " ").replace(".md", " md").replace("-", " ").replace("…", " ")
    return [t for t in (norm(x) for x in text.split()) if t]


want = toks(open("work/keep_text.txt").read())
edl = json.load(open("work/edl.json"))
joins = [s["out_in"] for s in edl[1:]]


def words_from_ojf(p):
    out = []
    for seg in json.load(open(p))["transcription"]:
        for tk in seg.get("tokens", []):
            tx = tk["text"]
            if tx.startswith("[_") or not tx.strip(): continue
            t = tk["t_dtw"] / 100 if tk.get("t_dtw", -1) >= 0 else tk["offsets"]["from"] / 1000
            if tx.startswith(" ") or not out: out.append({"w": tx.strip(), "t": t})
            else: out[-1]["w"] += tx
    return out


def report(name, got):
    g = []
    for w in got:
        for t in toks(w["w"]): g.append((t, w["t"]))
    sm = difflib.SequenceMatcher(a=want, b=[x[0] for x in g], autojunk=False)
    print(f"== {name}: intended {len(want)} · heard {len(g)} · similarity {sm.ratio():.3f}")
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal": continue
        t = g[min(j1, len(g) - 1)][1] if g else 0
        nj = min(joins, key=lambda x: abs(x - t)) if joins else 0
        print(f"  {op:7s} @{t:7.2f} (join {nj:7.2f}, {t - nj:+.2f}) …{' '.join(want[max(0, i1 - 4):i1])} | want {' '.join(want[i1:i2])!r} | heard {' '.join(x[0] for x in g[j1:j2])!r}")


whole = sys.argv[2] if len(sys.argv) > 2 else "work/rep/cut_whole.json"
lit = sys.argv[3] if len(sys.argv) > 3 else "work/rep/cut_literal.json"
if not os.path.exists(whole): sys.exit(f"no {whole}: run words_out.py first (it transcribes the cut)")
report("whole-file", words_from_ojf(whole))
if os.path.exists(lit): report("literal", json.load(open(lit)))
else: print(f"(no {lit}: run literal_asr.py work/aroll_check16k.wav {lit} to catch kept repeats)")
