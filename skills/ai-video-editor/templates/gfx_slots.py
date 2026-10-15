#!/usr/bin/env python3
"""gfx_slots.py — every graphic of ONE video: its slot on the spoken words, its layout(s), who builds it, what it shows.
Copy to <project>/edit/gfx_slots.py and replace the example slots in S_() with your video's (keep the shape).

    python gfx_slots.py      prints the table and writes GRAPHICS.md next to it (what the helper agents get in their brief)

plan.py imports SLOTS and LOGOS from here, so the briefs and the edit can never disagree. Times are A-roll seconds from
work/words_out.json: T("phrase") = the start of that phrase's first word (T("phrase", after=120.0) finds it after 120 s).
A slot (start, end) is the whole time the graphic may be on screen, and its data-duration; `cuts` says how plan.py shows
it — (from, to, layout) inside the slot: "graphic" full frame · "side" the graphic at 65 % beside the face card ·
"corner" the face card over the graphic's bottom-right · "overlay" a transparent clip over the face (tools/overlays.py).
Builders: A = the cards helper, B = the diagrams helper, M = the main session (3D scenes, chapter cards, real pages).
Lines with NO slot stay on the face (opinions, reactions, asks, the CTA) — about a third of the video."""
import json, os, re, sys

E = os.path.dirname(os.path.abspath(__file__))
if "-h" in sys.argv or "--help" in sys.argv or not os.path.exists(f"{E}/work/words_out.json"):
    print(__doc__.strip())
    sys.exit(0 if ("-h" in sys.argv or "--help" in sys.argv) else "no work/words_out.json next to this file: copy it into the video's edit/ folder first")
W = [x for x in json.load(open(f"{E}/work/words_out.json")) if x["t"] is not None]
nw = lambda s: re.sub(r"[^a-z0-9$%]", "", s.lower())


def T(phrase, after=0.0):
    toks = [nw(p) for p in phrase.split()]
    for i in range(len(W) - len(toks) + 1):
        if W[i]["t"] < after - 1e-6: continue
        if all(nw(W[i + j]["w"]).startswith(toks[j]) for j in range(len(toks))): return W[i]["t"]
    raise SystemExit(f"anchor not found: {phrase!r} after {after} — gfx_slots.py still has an example line, or the words differ")


def words(a, b):
    return " ".join(x["w"] for x in W if a - 0.05 <= x["t"] < b - 0.05)


AEND = W[-1]["e"]
G, S, C = "graphic", "side", "corner"


def S_():
    s = {}
    t = T
    # ── EXAMPLE (a video that opens "Claude Code edits my videos now…"): replace every slot with your own ────────────────
    a, b = t("Claude Code edits"), t("Here is how")                  # the hook stays on the face; the claim gets a card beside it
    s["claim"] = (a, b, [(a, b, S)], "A",
        "words card: 'Claude Code edits my videos' lands on 'edits'; 'end to end' in the accent with the underline")
    a, b = t("Here is how"), t("The first job")
    s["ch_01"] = (a, b, [(a, b, G)], "M", "chapter card 01 'How it works' (gfxlib chapter_cards.py) — 1.8 s, then the pill stays")
    a, b = t("The first job"), t("And that is")
    s["seven_jobs"] = (a, b, [(a, a + 6.0, G), (a + 6.0, b, S)], "B",
        "line icons (make_icons.py, --flow): each job's icon draws on the word that names it; full frame for the first 6 s, then beside the face")
    s["end_card"] = (AEND, AEND + 4.0, [(AEND, AEND + 4.0, G)], "A", "the end card after the last word")
    return s


SLOTS = S_()
# 3D logo stickers beside the head while a brand is named on the FACE: (slug, phrase, search from s, seconds, "right"|"left")
LOGOS = [("claude", "Claude Code", 0.0, 2.4, "right")]

if __name__ == "__main__":
    rows = ["| # | name | builder | slot (A-roll s) | dur | layout(s) | the words in the slot | what it shows |", "|---|---|---|---|---|---|---|---|"]
    for k, (n, (a, b, cuts, who, what)) in enumerate(sorted(SLOTS.items(), key=lambda x: x[1][0]), 1):
        lay = " + ".join(f"{l} {c0 - a:.1f}–{c1 - a:.1f}" for c0, c1, l in cuts)
        rows.append(f"| {k} | {n} | {who} | {a:.2f}–{b:.2f} | {b - a:.2f} | {lay} | {words(a, b)} | {what} |")
    open(f"{E}/GRAPHICS.md", "w").write("# Graphics\n\nTimes: A-roll seconds (work/words_out.json). A graphic's clock starts at its slot "
                                        "start; data-duration = the slot's length. Layout offsets are seconds INTO the graphic.\n\n" + "\n".join(rows) + "\n")
    print("\n".join(r[:200] for r in rows))
