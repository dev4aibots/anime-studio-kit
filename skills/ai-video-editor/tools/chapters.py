#!/usr/bin/env python3
"""chapters.py <edit_dir> — YouTube chapters from the cut itself. Each chapter opens on the speaker's words (plan.py
CHAPTERS), shifted by every insert exactly as assemble.py placed it (out/plan.txt).
  → out/chapters.txt   "0:00 Title" lines, ready for the description
  → <project>/publish/publish.json, if it exists: youtube.chapters and the "Chapters" block of youtube.description
YouTube's rules are checked: the first at 0:00, at least 3, each at least 10 s. Run after the last assemble.py pass."""
import importlib.util, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)
E = os.path.abspath(sys.argv[1]); P = os.path.join(os.path.dirname(E), "publish", "publish.json")
_s = importlib.util.spec_from_file_location("plan", f"{E}/plan.py"); pl = importlib.util.module_from_spec(_s); _s.loader.exec_module(pl)
W = [x for x in json.load(open(f"{E}/work/words_out.json")) if x["t"] is not None]
nw = lambda s: re.sub(r"[^a-z0-9$]", "", s.lower())


def T(phrase, after=0.0):
    toks = [nw(p) for p in phrase.split()]
    for i in range(len(W) - len(toks) + 1):
        if W[i]["t"] < after: continue
        if all(nw(W[i + j]["w"]).startswith(toks[j]) for j in range(len(toks))): return W[i]["t"]
    raise SystemExit(f"anchor not found: {phrase}")


# every insert (HERO, HERO1, HERO2…): plan.txt gives OUTPUT starts; back to A-roll positions, then each chapter moves by
# every insert that plays before its words
plan_txt = f"{E}/out/plan.txt"
if not os.path.exists(plan_txt): sys.exit("no out/plan.txt yet: run assemble.py (or assemble.py --plan) first")
ins, acc = [], 0.0
for o, l in re.findall(r"^\s*([\d.]+)\s+([\d.]+)s\s+HERO\w*", open(plan_txt).read(), re.M):
    ins.append((float(o) - acc, float(l))); acc += float(l)
H = ins[0][0] if ins else 1e9
F = lambda a: a + sum(l for h, l in ins if a >= h)
mmss = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"
chapters, secs = [], []
for anchor, title, shift in pl.CHAPTERS:
    t = 0.0 if anchor == 0.0 else H if anchor == "HERO" else F(T(anchor) + shift)
    chapters.append([mmss(t), title]); secs.append(t)
text = "\n".join(f"{a} {b}" for a, b in chapters)
open(f"{E}/out/chapters.txt", "w").write(text + "\n")
print(text)
warn = ([] if secs and secs[0] == 0.0 else ["the first chapter must start at 0:00"]) + \
       ([] if len(secs) >= 3 else ["YouTube needs at least 3 chapters"]) + \
       [f"'{chapters[i][1]}' is under 10 s" for i in range(len(secs) - 1) if secs[i + 1] - secs[i] < 10]
for w in warn: print("⚠", w)
if os.path.exists(P):
    pub = json.load(open(P)); yt = pub.setdefault("youtube", {})
    block = "Chapters\n" + text
    if re.search(r"Chapters\n(?:\d+:\d\d [^\n]*\n?)+", yt.get("description", "")):
        yt["description"] = re.sub(r"Chapters\n(?:\d+:\d\d [^\n]*\n?)+", block + "\n", yt["description"])
    else:
        yt["description"] = yt.get("description", "").rstrip() + "\n\n" + block
    yt["chapters"] = chapters
    json.dump(pub, open(P, "w"), indent=1, ensure_ascii=False)
    print(f"→ {P}")
