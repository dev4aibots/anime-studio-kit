#!/usr/bin/env python3
"""assemble.py <edit_dir> [--plan] — the video, end to end, from the cut and the plan.

The A-roll with a punch-in on every other jump cut; every graphic cut in on the word it illustrates (edit/plan.py);
an insert (the hero promo) placed in a breath with its own sound; a low music bed; a sound effect on every cut-in;
mastered to −16 LUFS / ≤ −1 dBTP (tools/voicechain.py: the voice lifted, never compressed) measured on the ENCODED file.
  --plan   print what goes where (out/plan.txt) and the balance line, render nothing      → edit/out/final.mp4 otherwise

The plan (edit/plan.py, start from the skill's templates/plan.py) holds everything that is this video's: where the
graphics live, the hero and the breath it goes in, the beds, the punch-in framing, and cutins(cut, T, gfx, hero, aend).
Music beds come from AI_EDITOR_HOME/music/ (plan.BEDS), sound effects from AI_EDITOR_HOME/sfx/<whoosh|pop|shutter|riser>/
(any audio files; a kind with no files is simply silent).
Rules the engine keeps for you: a graphic not rendered yet is skipped (the face stays); a graphic touched in the last
90 s is skipped (a render may still be writing it) and the chosen file is snapshotted before encoding; switches snap to a
jump cut within 0.5 s; gaps under 1.3 s between graphics are closed; pieces are cached by content."""
import glob, hashlib, json, os, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)

FPS, SR = 30, 48000
E = os.path.abspath(sys.argv[1])
import importlib.util
_spec = importlib.util.spec_from_file_location("plan", f"{E}/plan.py"); pl = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(pl)
GFX = aie.expand(pl.GFX)
import theme as _theme
# the look: plan.THEME = "warmcream" (the default) | "noir". The face cards, the base under them and the empty-opening check
# all follow it; the graphics carry it themselves (<html data-theme>).
THEME = getattr(pl, "THEME", None) or "warmcream"
PAL = _theme.palette(THEME)
HERO = aie.expand(pl.HERO) if getattr(pl, "HERO", None) else None
# inserts that play with their OWN sound while the A-roll pauses: plan.HEROES = [(file, (last words before, first words
# after[, search from s])), …] — e.g. two ads back to back. plan.HERO + plan.HERO_AFTER is the one-insert form.
_HS = [(aie.expand(f), a) for f, a in getattr(pl, "HEROES", [])] or ([(HERO, pl.HERO_AFTER)] if HERO and os.path.exists(HERO) else [])
if HERO and not os.path.exists(HERO): print(f"hero insert not rendered yet ({HERO}): assembling without it")
SFXD = aie.SFX
MUSIC = aie.MUSIC
AV, AA = f"{E}/work/aroll.mp4", f"{E}/work/aroll.wav"
OUT = f"{E}/out"; PIECES = f"{OUT}/pieces"
os.makedirs(PIECES, exist_ok=True)

# ── the words ──────────────────────────────────────────────────────────────────────────────────────────────────────
W = [x for x in json.load(open(f"{E}/work/words_out.json")) if x["t"] is not None]
nw = lambda s: re.sub(r"[^a-z0-9$]", "", s.lower())


def T(phrase, after=0.0):
    """start of the first word of `phrase` (the words, as transcribed) at or after `after`"""
    toks = [nw(p) for p in phrase.split()]
    for i in range(len(W) - len(toks) + 1):
        if W[i]["t"] < after - 1e-6: continue
        if all(nw(W[i + j]["w"]).startswith(toks[j]) for j in range(len(toks))): return W[i]["t"]
    raise SystemExit(f"anchor not found: {phrase!r} after {after}")


fr = lambda t: int(round(t * FPS))                                  # seconds → frame index
dur = lambda f: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                     capture_output=True, text=True).stdout.strip() or 0)
AEND = fr(dur(AV))                                                  # A-roll frames

def gfx(name):
    """the newest finished render of an edit graphic (renders/<name>*.mp4, never raw/mix), or None. A file touched in the
    last 90 s may still be being written by a render (an assembly once died on a half-written render): skip it, and anything
    that doesn't probe, and fall back to the previous good one."""
    import time
    c = [f for f in glob.glob(f"{GFX}/{name}/renders/{name}*.mp4") if not re.search(r"/(raw|mix)\.mp4$", f)]
    exact = f"{GFX}/{name}/renders/{name}.mp4"                      # the shipped <name>.mp4 wins over newer drafts (<name>_v2.mp4)
    for f in sorted(c, key=lambda f: (f != exact, -os.path.getmtime(f))):
        if time.time() - os.path.getmtime(f) > 90 and dur(f) > 0:
            # encode from a private copy: a render rewriting the file mid-pass can kill an assembly
            os.makedirs(f"{OUT}/snap", exist_ok=True)
            snap = f"{OUT}/snap/{os.path.basename(f)[:-4]}-{int(os.path.getmtime(f))}-{os.path.getsize(f)}.mp4"
            if not os.path.exists(snap): shutil.copy2(f, snap)
            return snap
    return None


# ── the hero insert: in the breath after "made." ─────────────────────────────────────────────────────────────────
def voice_env():
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", AA, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, np.float32)
    hop = SR // 100; n = len(x) // hop
    return x, 20 * np.log10(np.sqrt((x[: n * hop].astype(np.float64).reshape(n, hop) ** 2).mean(axis=1) + 1e-12))

VOICE, DB = voice_env()
QTHR = min(-40.0, float(np.percentile(DB, 95)) - 20.0)               # "the voice has stopped": follows a quiet take's level (cut.py)
HS = []                                                              # (A-roll frame the insert starts at, its length in frames, file)
CUTS_S = sorted(set(x["out_in"] for x in json.load(open(f"{E}/work/edl.json"))))   # jump cuts, A-roll seconds
MUTED = set()                                                        # inserts whose own sound is not mixed (a plan.MUSIC cue carries it)
for hf, ha in _HS:                       # (last words before the breath, first words after it[, search from s])
    if isinstance(ha, dict):             # {"at": A-roll s, "len": s, "mute": bool} — e.g. a cold open's first 2.5 s before the first word
        HS.append((fr(ha.get("at", 0.0)), fr(ha["len"]) if ha.get("len") else fr(dur(hf)), hf))
        if ha.get("mute"): MUTED.add(hf)
        continue
    after = ha[2] if len(ha) > 2 else 0.0
    t_made, t_and = T(ha[0], after), T(ha[1], after)
    lo = t_made if t_made < t_and else t_and - 1.0                 # (a "last word" found AFTER the next one was cut away: look back 1 s)
    c = [x for x in CUTS_S if lo < x <= t_and]
    if c: at = c[-1]                                                # a jump cut in the gap: the insert starts ON it (else 0.2 s of room tone)
    else:
        q = next((f for f in range(int((t_made + 0.25) * 100), int(t_and * 100)) if (DB[f:f + 8] < QTHR).all()), None)   # the voice has stopped
        at = q / 100 + 0.1 if q is not None else t_and - 0.02       # a breath after it, or just before the next word
    HS.append((fr(at), fr(dur(hf)), hf))                            # the insert starts here (A-roll frame); the A-roll pauses
HS.sort()
HFR = [h for h, _, _ in HS]
H, HL = (HS[0][0], HS[0][1]) if HS else (AEND + 1, 0)               # the first insert (kept for the one-insert code paths)
HOUT = [h + sum(l for h2, l, _ in HS if h2 < h) for h, _, _ in HS]   # where each insert starts in the OUTPUT (frames)

# ── the plan: (A-roll seconds) at, [end], file, src_in, sfx ────────────────────────────────────────────────────
P = []
LAYOUTS = ("graphic", "corner", "side", "sticker")   # a cut-in is the graphic alone, or the graphic WITH the face — a card over
                                          # its corner, or the graphic beside the face card. "sticker": a transparent clip (a 3D logo
                                          # from gfxlib/logo_clip.py) laid OVER the face while it is named; the face stays full frame
STK = []
def cut(name, file, at, end=None, src=0.0, sfx="whoosh", layout=None, pos="right", size=360):
    layout = layout or getattr(pl, "LAYOUT", {}).get(name) or getattr(pl, "LAYOUT_DEFAULT", "graphic")
    assert layout in LAYOUTS, f"{name}: layout {layout!r} not in {LAYOUTS}"
    if layout == "sticker":
        if file and os.path.exists(file):
            STK.append(dict(name=name, file=file, a=fr(at), e=fr(end) if end is not None else fr(at) + 75, src=src, pos=pos, size=size,
                            sfx="pop" if sfx == "whoosh" else sfx))
        return
    if file and os.path.exists(file): P.append(dict(name=name, file=file, a=fr(at), e=None if end is None else fr(end), src=src, sfx=sfx, layout=layout))
    else: P.append(dict(name=name, file=None, a=fr(at), e=None if end is None else fr(end), src=src, sfx=None, layout=layout))

pl.cutins(cut, T, gfx, HERO, AEND / FPS)
P.sort(key=lambda c: c["a"])

# lengths: a cut-in runs to its `end`, or as long as its clip lasts, and never into the next one
live = [c for c in P if c["file"]]
for k, c in enumerate(live):
    still = c["file"].lower().endswith((".jpg", ".jpeg", ".png", ".webp"))   # a still holds as long as it is asked to (flashes, frames)
    room = 3600.0 if still else (dur(c["file"]) - c["src"])
    e = c["e"] if c["e"] is not None else c["a"] + fr(room)
    e = min(e, c["a"] + int(room * FPS))                            # never past the clip's last frame
    if k + 1 < len(live): e = min(e, live[k + 1]["a"])
    c["e"] = e
live = [c for c in live if c["e"] - c["a"] >= 3]
# a graphic's first frames are often the EMPTY STAGE before its first element lands; cutting into them from the face reads as
# a dip (noir: 8–18 frames at luma ~4, a dip to black; on Warm Cream it would be a blank cream page). Start such a
# graphic on its first frame with something on it instead, later by the same amount in the clip, so it stays on the words.
# tools/theme.py empty_lead(): a dark stage uses the luma rule; a light stage uses edge energy.
DARK_F = f"{OUT}/dark_lead.json"; DARK = json.load(open(DARK_F)) if os.path.exists(DARK_F) else {}
def dark_lead(f, src):
    key = f"{f}|{os.path.getmtime(f):.0f}|{src:.3f}"
    if key not in DARK: DARK[key] = _theme.empty_lead(f, src)
    return DARK[key]
for c in live:
    if c["file"].lower().endswith((".jpg", ".jpeg", ".png", ".webp")): continue
    d = dark_lead(c["file"], c["src"])
    if d and c["e"] - c["a"] - d >= 15: c["a"] += d; c["src"] += d / FPS; c["trim"] = d
json.dump(DARK, open(DARK_F, "w"))
EDL0 = json.load(open(f"{E}/work/edl.json")); CUT0 = sorted(set(fr(x["out_in"]) for x in EDL0))
for c in live:                                                      # a switch lands on a jump cut when one is within 0.5 s:
    before = [x for x in CUT0 if c["a"] - 15 < x < c["a"]]           # no 0.3 s sliver of the face between a cut and a graphic
    if before and not c.get("trim") and not any(before[-1] <= h < c["a"] for h in HFR):  # (never back into a trimmed dark lead-in)
        c["src"] = max(0.0, c["src"] - (c["a"] - before[-1]) / FPS); c["a"] = before[-1]
    after = [x for x in CUT0 if c["e"] < x < c["e"] + 15]
    if after and not any(c["e"] <= h < after[0] for h in HFR): c["e"] = after[0]
for k in range(len(live) - 1):
    if live[k]["e"] > live[k + 1]["a"]: live[k]["e"] = live[k + 1]["a"]                                      # no 1–14-frame flash of the face between two graphics:
    gap = live[k + 1]["a"] - live[k]["e"]                           # the first one holds (its last frame) up to the next
    if 0 < gap < 39 and not any(live[k]["e"] <= h < live[k + 1]["a"] for h in HFR):   # (up to 1.3 s — a 0.6–1.1 s face
        live[k]["e"] = live[k + 1]["a"]                             # between two graphics reads as flicker): the first one holds. Not the
                                                                    # next one's lead-in: that is an empty stage while the speaker talks
for c in live:                                                      # no sliver of the face between an insert and a graphic:
    for h in HFR:                                                   # a cut-in that starts just after an insert starts ON it,
        if 0 < c["a"] - h < 15:                                     # one that ends just before an insert runs up to it
            c["src"] = max(0.0, c["src"] - (c["a"] - h) / FPS); c["a"] = h
        if 0 < h - c["e"] < 15: c["e"] = h
assert not any(c["a"] < h < c["e"] for c in live for h in HFR), "a cut-in straddles an insert"

# ── picture: a list of pieces in output order ────────────────────────────────────────────────────────────────────
EDL = json.load(open(f"{E}/work/edl.json"))
CUTS = sorted(set(fr(e["out_in"]) for e in EDL))                   # jump cuts (A-roll frames)
seg_of = lambda f: max(0, np.searchsorted(CUTS, f, side="right") - 1)
PUNCH = dict(dict(zoom=1.12, fx=0.48, fy=0.40), **getattr(pl, "PUNCH", {}))   # punch-in: centred on the face
FX, FY, Z = PUNCH["fx"], PUNCH["fy"], PUNCH["zoom"]

def aroll_pieces(a, b):
    out, s = [], a
    for c in [x for x in CUTS if a < x < b] + [b]:
        if c - s >= 1: out.append(dict(kind="aroll", file=AV, src=s / FPS, n=c - s, zoom=Z if seg_of(s) % 2 else 1.0))
        s = c
    for k in range(1, len(out)):                                    # a zoom change on a sliver reads as a glitch: keep the framing
        if out[k]["n"] < 15 or out[k - 1]["n"] < 15: out[k]["zoom"] = out[k - 1]["zoom"]
    return out

pieces, t = [], 0
events = []                                                          # (output frame, sfx kind, name) for the sound
out_f = lambda a: a + sum(l for h, l, _ in HS if h <= a)            # A-roll frame → output frame
heroes = [dict(name=f"HERO{k + 1}" if len(HS) > 1 else "HERO", a=h, e=h, file=f, src=0.0, sfx="hero", n=l, out=o, hero=True)
          for k, ((h, l, f), o) in enumerate(zip(HS, HOUT))]
for c in sorted(live + heroes, key=lambda c: (c["a"], not c.get("hero"))):
    if c["a"] > t: pieces += aroll_pieces(t, min(c["a"], AEND))
    if c.get("hero"):                                                # the A-roll pauses; the insert plays with its own sound
        pieces.append(dict(kind="clip", file=c["file"], src=0.0, n=c["n"], name=c["name"]))
        if c["file"] not in MUTED: events.append((c["out"], "hero", c["name"]))
        t = max(t, c["a"]); continue
    pieces.append(dict(kind="clip", file=c["file"], src=c["src"], n=c["e"] - c["a"], name=c["name"], layout=c["layout"], aroll=c["a"] / FPS))
    if c["sfx"]: events.append((out_f(c["a"]), c["sfx"], c["name"]))
    t = c["e"]
if t < AEND: pieces += aroll_pieces(t, AEND)
# logo stickers: split the FACE pieces at each sticker's edges and lay the clip over the ones inside it (the face stays full)
STK.sort(key=lambda x: x["a"])
if STK:
    out_p, shown = [], set()
    for p in pieces:
        if p["kind"] != "aroll": out_p.append(p); continue
        a0 = fr(p["src"]); a1 = a0 + p["n"]
        edges = sorted({a0, a1} | {x for k in STK for x in (k["a"], k["e"]) if a0 < x < a1})
        for u, v in zip(edges, edges[1:]):
            q = dict(p, src=u / FPS, n=v - u)
            k = next((k for k in STK if k["a"] <= u and v <= k["e"]), None)
            if k:
                q["sticker"] = dict(file=k["file"], at=(u - k["a"]) / FPS + k["src"], pos=k["pos"], size=k["size"], fin=u == k["a"], fout=v == k["e"], name=k["name"])
                if k["name"] not in shown and k["sfx"]: events.append((out_f(k["a"]), k["sfx"], k["name"])); shown.add(k["name"])
            out_p.append(q)
    pieces = out_p
# the chapter pill: "03 Chapter title" in the top-left while that chapter plays, from the end of its
# chapter card to the next card (or the end card), over the face, the face cards and the graphics; never over a chapter card,
# an insert or the end card; 0.3 s fades where a stretch starts and ends; a stretch under 2 s gets none.
# gfxlib/cards/chapter/chapter_cards.py writes <GFX>/_pills/ (NN.png + pills.json {card name: png}); plan.PILLS = False: none.
PILLS_F = f"{GFX}/_pills/pills.json"
PILLS = json.load(open(PILLS_F)) if getattr(pl, "PILLS", True) and os.path.exists(PILLS_F) else {}
if PILLS:
    hidden = lambda p: p.get("name") in PILLS or str(p.get("name", "")).startswith("HERO") or p.get("name") == "end_card"
    cur = None
    for p in pieces:
        if p.get("name") in PILLS: cur = f"{GFX}/_pills/{PILLS[p['name']]}"
        if p.get("name") == "end_card": cur = None
        if cur and not hidden(p) and os.path.exists(cur): p["pill"] = dict(png=cur)
    k = 0
    while k < len(pieces):
        if not pieces[k].get("pill"): k += 1; continue
        j = k
        while j + 1 < len(pieces) and pieces[j + 1].get("pill", {}).get("png") == pieces[k]["pill"]["png"]: j += 1
        long_enough = sum(pieces[i]["n"] for i in range(k, j + 1)) >= 2 * FPS
        for i in range(k, j + 1):
            if long_enough: pieces[i]["pill"].update(fin=i == k, fout=i == j, mt=os.path.getmtime(pieces[i]["pill"]["png"]))
            else: pieces[i].pop("pill")
        k = j + 1
TOTAL = sum(p["n"] for p in pieces)

with open(f"{OUT}/plan.txt", "w") as fp:
    acc = 0
    for p in pieces:
        what = p["name"] + f"  ← {os.path.basename(p['file'])} @{p['src']:.2f}" + (f"  [{p['layout']}]" if p.get("layout", "graphic") != "graphic" else "") \
               if p["kind"] == "clip" else "face" + ("  (punch-in)" if p["zoom"] > 1 else "") + f"  @{p['src']:.2f}" + \
               (f"  + logo {p['sticker']['name']}" if p.get("sticker") else "")
        what += f"  · pill {os.path.basename(p['pill']['png'])[:-4]}" if p.get("pill") else ""
        fp.write(f"{acc / FPS:8.2f}  {p['n'] / FPS:6.2f}s  {what}\n")
        acc += p["n"]
skipped = [c["name"] for c in P if not c["file"]]
# the balance: FACE (the speaker alone) · BOTH (the speaker + a graphic) · GRAPHIC (a graphic alone) — each about a third,
# the face on screen (face + both) at least 60 %, and never more than ~12 s without the face
state = lambda p: "face" if p["kind"] == "aroll" else ("both" if p.get("layout") in ("corner", "side") else "graphic")
share = {k: sum(p["n"] for p in pieces if state(p) == k) / max(1, TOTAL) for k in ("face", "both", "graphic")}
run, longest, at_, acc = 0, (0, 0), 0, 0
for p in pieces:
    if state(p) == "graphic": run += p["n"]; longest = max(longest, (run, acc - run + p["n"]))
    else: run = 0
    acc += p["n"]
warn = [m for ok, m in ((share["face"] + share["both"] >= 0.60, "the face on screen under 60 %"), (0.20 <= share["face"] <= 0.45, "face alone outside 20–45 %"),
                        (0.20 <= share["both"] <= 0.45, "face + graphic outside 20–45 %"), (share["graphic"] <= 0.45, "graphic alone over 45 %"),
                        (longest[0] <= 12 * FPS, f"{longest[0] / FPS:.0f} s without the face from {(longest[1]) / FPS:.0f} s")) if not ok]
BALANCE = (f"balance · face {share['face']:.0%} · both {share['both']:.0%} · graphic {share['graphic']:.0%} · face on screen "
           f"{share['face'] + share['both']:.0%} · longest without the face {longest[0] / FPS:.1f}s" + ("  ⚠ " + "; ".join(warn) if warn else "  ✓"))
print(f"inserts at {', '.join(f'{h / FPS:.2f}s ({l / FPS:.1f}s)' for h, l, _ in HS) or 'none'} (A-roll) · {len(pieces)} pieces · {TOTAL / FPS:.1f}s total · "
      f"{len(live)} cut-ins · not rendered yet: {', '.join(skipped) or 'none'}")
print(BALANCE)
if "--plan" in sys.argv: print(open(f"{OUT}/plan.txt").read()); sys.exit()

# ── encode the pieces (cached by content) and join them ────────────────────────────────────────────────────────────
GRADE = getattr(pl, "GRADE", "eq=contrast=1.04:saturation=1.05")      # plan.GRADE overrides (a dark take gets a gentle lift)
def vf(p):
    if p["kind"] == "aroll":
        z = p["zoom"]
        if z > 1:
            w, h = int(round(1920 / z / 2) * 2), int(round(1080 / z / 2) * 2)
            x = min(max(0, int(FX * 1920 - w / 2)), 1920 - w); y = min(max(0, int(FY * 1080 - h / 2)), 1080 - h)
            return f"crop={w}:{h}:{x}:{y},scale=1920:1080:flags=lanczos,{GRADE},format=yuv420p"
        return f"{GRADE},format=yuv420p"
    return "scale=1920:1080:flags=lanczos,fps=30,format=yuv420p"

# ── the face WITH a graphic (layouts "corner" / "side"): glass cards drawn once, composited per piece ─────────────
LAY = f"{OUT}/layout"
CARD = dict(corner=dict(w=512, h=288, x=1920 - 40 - 512, y=1080 - 40 - 288, r=22),     # over the floor, where the graphics leave room
            side_g=dict(w=1248, h=702, x=56, y=189, r=22),                             # the graphic at 65 %, left …
            side_f=dict(w=520, h=702, x=1344, y=189, r=22))                            # … the face card on the right
FACEZ, SIDEZ = getattr(pl, "FACE_CARD_ZOOM", 1.9), getattr(pl, "FACE_SIDE_ZOOM", 1.25)    # how tight the face sits in each card

# the card frames follow the theme: noir = a white hairline at 60/255 and a black shadow (200, blur 28); a light theme = an ink
# hairline (the theme's contact colour at 46/255) and a softer, warmer, lower shadow, like the graphics' own cards
_ct = tuple(int(v) for v in PAL["contact"].split(","))
CARD_LOOK = (dict(edge=(255, 255, 255, 60), shade=(0, 0, 0), a=200, blur=28, dy=16) if not PAL["light"] else
             dict(edge=_ct + (46,), shade=_ct, a=96, blur=34, dy=22))
def card_assets():
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(LAY, exist_ok=True)
    for k, c in CARD.items():
        if not os.path.exists(f"{LAY}/mask_{k}.png"):
            m = Image.new("L", (c["w"], c["h"]), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, c["w"] - 1, c["h"] - 1), c["r"], fill=255); m.save(f"{LAY}/mask_{k}.png")
    L = CARD_LOOK
    for name, keys in (("corner", ["corner"]), ("side", ["side_g", "side_f"])):
        if os.path.exists(f"{LAY}/shadow_{name}_{THEME}.png") and os.path.exists(f"{LAY}/border_{name}_{THEME}.png"): continue
        A = Image.new("L", (1920, 1080), 0); B = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        for k in keys:
            c = CARD[k]
            ImageDraw.Draw(A).rounded_rectangle((c["x"], c["y"] + L["dy"], c["x"] + c["w"], c["y"] + c["h"] + L["dy"]), c["r"], fill=L["a"])
            ImageDraw.Draw(B).rounded_rectangle((c["x"], c["y"], c["x"] + c["w"] - 1, c["y"] + c["h"] - 1), c["r"], outline=L["edge"], width=2)
        r_, g_, b_ = (Image.new("L", (1920, 1080), v) for v in L["shade"])
        Image.merge("RGBA", (r_, g_, b_, A.filter(ImageFilter.GaussianBlur(L["blur"])))).save(f"{LAY}/shadow_{name}_{THEME}.png")
        B.save(f"{LAY}/border_{name}_{THEME}.png")

def face_crop(w, h, z, dy=0.0):
    ch = int(1080 / z) // 2 * 2; cw = int(ch * w / h) // 2 * 2
    if cw > 1920: cw = 1920; ch = int(1920 * h / w) // 2 * 2
    x = min(max(0, int(FX * 1920 - cw / 2)), 1920 - cw); y = min(max(0, int((FY + dy) * 1080 - ch / 2)), 1080 - ch)
    return f"crop={cw}:{ch}:{x}:{y},scale={w}:{h}:flags=lanczos"

def both_cmd(p, out):
    still = p["file"].lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    gin = ["-loop", "1", "-framerate", str(FPS), "-i", p["file"]] if still else ["-ss", f"{max(0.0, p['src'] - 0.005):.4f}", "-i", p["file"]]
    ins = gin + ["-ss", f"{max(0.0, p['aroll'] - 0.005):.4f}", "-i", AV]
    img = lambda f: ["-loop", "1", "-framerate", str(FPS), "-i", f"{LAY}/{f}"]
    base = f"color=c=0x{PAL['bg'].lstrip('#')}:s=1920x1080:r={FPS}[bg];"   # a solid base in the theme's ground: a graphic that ends early holds its last frame,
    if p["layout"] == "corner":                                      # and the face keeps moving
        c = CARD["corner"]; ins += img("mask_corner.png") + img(f"shadow_corner_{THEME}.png") + img(f"border_corner_{THEME}.png")
        fc = (base + f"[0:v]setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,fps={FPS}[g];[bg][g]overlay=0:0:eof_action=repeat[b0];"
              f"[1:v]setpts=PTS-STARTPTS,{face_crop(c['w'], c['h'], FACEZ)},{GRADE},format=rgba[f0];[2:v]format=gray[m];[f0][m]alphamerge[fm];"
              f"[b0][3:v]overlay=0:0[b1];[b1][fm]overlay={c['x']}:{c['y']}[b2];[b2][4:v]overlay=0:0,format=yuv420p[v]")
    else:
        g, c = CARD["side_g"], CARD["side_f"]; ins += img("mask_side_g.png") + img("mask_side_f.png") + img(f"shadow_side_{THEME}.png") + img(f"border_side_{THEME}.png")
        fc = (base + f"[0:v]setpts=PTS-STARTPTS,scale={g['w']}:{g['h']}:flags=lanczos,fps={FPS},format=rgba[g0];[2:v]format=gray[mg];[g0][mg]alphamerge[gm];"
              f"[1:v]setpts=PTS-STARTPTS,{face_crop(c['w'], c['h'], SIDEZ, 0.04)},{GRADE},format=rgba[f0];[3:v]format=gray[mf];[f0][mf]alphamerge[fm];"
              f"[bg][4:v]overlay=0:0[b0];[b0][gm]overlay={g['x']}:{g['y']}:eof_action=repeat[b1];[b1][fm]overlay={c['x']}:{c['y']}[b2];"
              f"[b2][5:v]overlay=0:0,format=yuv420p[v]")
    return ["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[v]", "-frames:v", str(p["n"]), "-an", "-c:v", "libx264",
            "-threads", "4", "-preset", "medium", "-crf", "16", "-g", "60", "-bf", "2", "-r", "30", "-video_track_timescale", "15360",
            "-pix_fmt", "yuv420p", out]

if any(p.get("layout") in ("corner", "side") for p in pieces): card_assets()

STICK_POS = {"right": (1480, 330), "left": (440, 330), "tr": (1920 - 60, 60), "tl": (60, 60)}   # centre (right/left: beside the head) or corner
def sticker_cmd(p, out):
    k = p["sticker"]; S = int(k["size"]); n = p["n"]
    cx, cy = STICK_POS.get(k["pos"], STICK_POS["right"])
    x, y = (cx - S, cy) if k["pos"] == "tr" else (cx, cy) if k["pos"] == "tl" else (cx - S // 2, cy - S // 2)
    full = k["pos"] == "full"                                        # a 1920×1080 transparent overlay laid at 0,0
    if full: x, y = 0, 0
    L = dur(k["file"]) or 6.0
    fades = (",fade=t=in:st=0:d=0.22:alpha=1" if k["fin"] else "") + (f",fade=t=out:st={max(0.0, n / FPS - 0.22):.3f}:d=0.22:alpha=1" if k["fout"] else "")
    fc = (f"[0:v]setpts=PTS-STARTPTS,{vf(p)}[b];[1:v]setpts=PTS-STARTPTS,scale={'1920:1080' if full else f'{S}:{S}'}:flags=lanczos,format=yuva444p{fades}[s];"
          f"[b][s]overlay={x}:{y}:eof_action=pass:format=auto,format=yuv420p[v]")
    return ["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, p['src'] - 0.005):.4f}", "-i", AV, "-stream_loop", "-1", "-ss", f"{k['at'] % L:.4f}",
            "-i", k["file"], "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n), "-an", "-c:v", "libx264", "-threads", "4", "-preset", "medium",
            "-crf", "16", "-g", "60", "-bf", "2", "-r", "30", "-video_track_timescale", "15360", "-pix_fmt", "yuv420p", out]

def with_pill(cmd, p):
    """lay the chapter pill (a looped transparent PNG, alpha fades at a stretch's ends) over a piece's [v]"""
    if not p.get("pill"): return cmd
    q = p["pill"]; n = p["n"]
    fades = (",fade=t=in:st=0:d=0.3:alpha=1" if q["fin"] else "") + (f",fade=t=out:st={max(0.0, n / FPS - 0.3):.3f}:d=0.3:alpha=1" if q["fout"] else "")
    i = cmd.index("-filter_complex"); fc = cmd[i + 1]; n_in = cmd[:i].count("-i")
    assert fc.endswith("[v]"), fc[-40:]
    fc = fc[:-3] + f"[v0];[{n_in}:v]format=rgba{fades}[pl];[v0][pl]overlay=0:0:format=auto,format=yuv420p[v]"
    return cmd[:i] + ["-loop", "1", "-framerate", str(FPS), "-i", q["png"], "-filter_complex", fc] + cmd[i + 2:]

def enc(k_p):
    k, p = k_p
    lay = p.get("layout", "graphic")
    extra = [lay, p.get("aroll"), CARD, FACEZ, SIDEZ, FX, FY, GRADE, "both-v2"] + ([THEME, CARD_LOOK] if THEME != "noir" else []) if lay != "graphic" else []   # v2: inputs start at 0 (frame 1 had an empty card)
    if p.get("sticker"): extra = [p["sticker"], os.path.getmtime(p["sticker"]["file"]), "sticker-v1"]
    if p.get("pill"): extra = extra + ["pill-v1", p["pill"]]
    key = hashlib.md5(json.dumps([p["file"], os.path.getmtime(p["file"]), p["src"], p["n"], vf(p)] + extra).encode()).hexdigest()[:10]
    f = f"{PIECES}/{key}.mp4"                                         # named by content only: a new insert must not invalidate the rest
    if not os.path.exists(f):
        if p.get("sticker"): subprocess.run(with_pill(sticker_cmd(p, f + ".tmp.mp4"), p), check=True)
        elif lay != "graphic": subprocess.run(with_pill(both_cmd(p, f + ".tmp.mp4"), p), check=True)
        else:
            still = p["file"].lower().endswith((".jpg", ".jpeg", ".png", ".webp"))   # one image through fps= gives NO frames: loop it
            inp = ["-loop", "1", "-framerate", str(FPS), "-i", p["file"]] if still else ["-ss", f"{max(0.0, p['src'] - 0.005):.4f}", "-i", p["file"]]
            filt = ["-filter_complex", f"[0:v]{vf(p)}[v]", "-map", "[v]"] if p.get("pill") else ["-vf", vf(p)]
            # output options go after ALL the inputs: with_pill() adds the pill as one more input
            subprocess.run(with_pill(["ffmpeg", "-v", "error", "-y"] + inp + filt + ["-frames:v", str(p["n"]), "-an", "-c:v", "libx264",
                            "-threads", "4", "-preset", "medium", "-crf", "16", "-g", "60", "-bf", "2", "-r", "30",
                            "-video_track_timescale", "15360", "-pix_fmt", "yuv420p", f + ".tmp.mp4"], p), check=True)
        got = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                              "stream=nb_read_frames", "-of", "csv=p=0", f + ".tmp.mp4"], capture_output=True, text=True).stdout.strip()
        if not got.isdigit():                                       # name the piece instead of dying on int('')
            raise SystemExit(f"piece {k} ({p.get('name', p['kind'])}) from {p['file']} @{p['src']:.3f} × {p['n']} frames encoded to nothing ({got!r})")
        got = int(got)
        if got != p["n"]:                                           # a clip shorter than asked: hold its last frame
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f + ".tmp.mp4", "-vf", f"tpad=stop_mode=clone:stop={p['n'] - got}",
                            "-frames:v", str(p["n"]), "-c:v", "libx264", "-threads", "4", "-preset", "medium", "-crf", "16", "-g", "60", "-bf", "2",
                            "-r", "30", "-video_track_timescale", "15360", "-pix_fmt", "yuv420p", f], check=True)
            os.remove(f + ".tmp.mp4")
        else: os.rename(f + ".tmp.mp4", f)
    return f

for old in glob.glob(f"{PIECES}/*.tmp.mp4"): os.remove(old)
with ThreadPoolExecutor(2) as ex: files = list(ex.map(enc, enumerate(pieces)))   # gentle: other renders share this Mac
keep = set(files)
for old in glob.glob(f"{PIECES}/*.mp4"):
    if old not in keep: os.remove(old)
with open(f"{OUT}/pieces.txt", "w") as fp:
    for f in files: fp.write(f"file '{f}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/pieces.txt", "-c", "copy", f"{OUT}/picture.mp4"], check=True)

# ── sound ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def pcm(path, ch=2, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + (["-t", str(t)] if t is not None else []) + \
          ["-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, ch).astype(np.float64)

def lufs_of(x):
    tmp = f"{OUT}/_m.wav"; write_wav(tmp, x)
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", tmp, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    os.remove(tmp); return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])

def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-", path],
                   input=x.astype(np.float32).tobytes(), check=True)

N = int(round(TOTAL / FPS * SR))
S = lambda f: int(round(f / FPS * SR))                               # frames → samples
mix = np.zeros((N, 2))
# THE VOICE (tools/voicechain.py — the chain won a blind test against compressed versions): the take's own pace; here ONLY a
# static lift to −16 LUFS with the 5 ms look-ahead peak catch. No compressor, gate, EQ, de-esser, loudnorm. A gap wherever
# an insert plays.
from voicechain import lift, fanprint, master_filter, ENC_AUDIO, TARGET_LUFS
# a computer fan in the room: plan.FANPRINT = (start_s, length_s) of PURE room tone in the take (work/audio/take48k.wav,
# ≥ 20 s, a long wait) → voicechain.fanprint() at its −8 dB floor on the A-roll voice, before the lift. Sample-aligned.
# No FANPRINT in the plan: the voice untouched.
VSRC, FP = AA, getattr(pl, "FANPRINT", None)
if FP:
    room, VSRC = f"{OUT}/_room.wav", f"{OUT}/_voice_fp.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(FP[0]), "-t", str(FP[1]), "-i", f"{E}/work/audio/take48k.wav",
                    "-ac", "1", "-c:a", "pcm_s24le", room], check=True)
    fanprint(AA, VSRC, room); os.remove(room)
    print(f"voice: fan print from {FP[1]:.0f} s of room tone at {FP[0]:.0f} s of the take (floor −8 dB)")
VL = f"{OUT}/_voice.wav"; lift(VSRC, VL, lufs=TARGET_LUFS)
v = pcm(VL, 1)[:, 0]; os.remove(VL)
if FP: os.remove(VSRC)
vo = np.zeros(N); src = dst = 0
for h, l, _ in HS:
    n = S(h) - src; seg = v[src: src + n][: max(0, N - dst)]; vo[dst: dst + len(seg)] = seg; src += n; dst += n + S(l)
rest = v[src:][: max(0, N - dst)]; vo[dst: dst + len(rest)] = rest
mix[:, 0] += vo; mix[:, 1] += vo
# each insert's own sound (its music + effects), a touch under the voice
for (h, l, f), o in zip(HS, HOUT):
    if f in MUTED: continue
    hx = pcm(f, 2)[:S(l)]; hx = hx * 10 ** ((-17 - lufs_of(hx)) / 20); a = S(o); hx = hx[: max(0, N - a)]; mix[a: a + len(hx)] += hx
# the bed: your tracks back to back (3 s crossfades), ~28 dB under the voice; out before an insert, back after it
beds = []
for name in getattr(pl, "BEDS", []):                                 # file names in AI_EDITOR_HOME/music/ (or full paths)
    raw = os.path.expanduser(os.path.expandvars(name))
    f = raw if os.path.isabs(raw) else os.path.join(MUSIC, name)
    if os.path.exists(f): beds.append(f)
    else: print(f"music bed not found, skipped: {f}")
b = None
for f in beds:
    x = pcm(f, 2)
    if b is None: b = x
    else:
        xf = min(int(3 * SR), len(b) // 2, len(x) // 2); r = np.linspace(0, 1, xf)[:, None]
        b = np.concatenate([b[:-xf], b[-xf:] * (1 - r) + x[:xf] * r, x[xf:]])
if b is None: b = np.zeros((N, 2)); print("no music bed (plan.BEDS empty or missing): voice and effects only")
b = b[:N] if len(b) >= N else np.concatenate([b, np.zeros((N - len(b), 2))])
if np.abs(b).max() > 0: b = b * 10 ** ((-44 - lufs_of(b[: int(120 * SR)])) / 20)
g = np.ones(N)
f1, f2 = int(1.2 * SR), int(2.5 * SR)
for (h, l, f), o in zip(HS, HOUT):                                   # the bed steps out for every insert and comes back after it
    a, z = S(o), S(o) + S(l); a0 = max(0, a - f1)
    g[a0: a] = np.minimum(g[a0: a], np.linspace(1, 0, f1)[f1 - (a - a0):]); g[a: z] = 0
    up = np.linspace(0, 1, f2)[: len(g[z: z + f2])]; g[z: z + len(up)] = np.minimum(g[z: z + len(up)], up)
# plan.MUSIC: [dict(file, out=output s, src=s in the file, dur=s, lufs=-17, duck=11, fin=0.0, fout=0.8)] — a track (a cold open's
# music, a replay's) laid at an OUTPUT time, levelled to `lufs` over its own span, ducked `duck` dB wherever the voice is present
# (20 ms RMS > −42 dBFS, 40 ms attack / 350 ms release), faded at its ends; the bed steps out for it like for an insert.
MUSIC = getattr(pl, "MUSIC", [])
for m in MUSIC:
    a, z = int(m["out"] * SR), int((m["out"] + m["dur"]) * SR); a0 = max(0, a - f1)
    g[a0: a] = np.minimum(g[a0: a], np.linspace(1, 0, f1)[f1 - (a - a0):]); g[a: z] = 0
    up = np.linspace(0, 1, f2)[: len(g[z: z + f2])]; g[z: z + len(up)] = np.minimum(g[z: z + len(up)], up)
g[:int(0.5 * SR)] = np.minimum(g[:int(0.5 * SR)], np.linspace(0, 1, int(0.5 * SR))); g[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR))
mix += b * g[:, None]
for m in MUSIC:
    x = pcm(aie.expand(m["file"]), 2, ss=m.get("src", 0.0), t=m["dur"])
    x = x * 10 ** ((m.get("lufs", -17.0) - lufs_of(x)) / 20)
    a = int(round(m["out"] * SR)); n = min(len(x), N - a); x = x[:n]
    hop = int(0.02 * SR); nb = n // hop + 1
    seg = np.concatenate([vo[a: a + n], np.zeros(nb * hop - n)]).reshape(nb, hop)
    on = (20 * np.log10(np.sqrt((seg ** 2).mean(axis=1)) + 1e-9) > -42).astype(float)
    sm = np.zeros(nb); cur_ = 0.0
    for i in range(nb):                                              # 40 ms attack, 350 ms release
        k = 0.5 if on[i] > cur_ else 0.055; cur_ += (on[i] - cur_) * k; sm[i] = cur_
    gain = 10 ** (-m.get("duck", 11.0) * np.repeat(sm, hop)[:n] / 20)
    fi, fo = int(m.get("fin", 0.0) * SR), int(m.get("fout", 0.8) * SR)
    if fi: gain[:fi] *= np.linspace(0, 1, fi)
    if fo: gain[-fo:] *= np.linspace(1, 0, fo)
    mix[a: a + n] += x * gain[:, None]
    print(f"music cue {os.path.basename(m['file'])} @{m['out']:.2f}s out ({m['dur']:.1f}s from {m.get('src', 0):.2f}s) at {m.get('lufs', -17)} LUFS, ducked {m.get('duck', 11)} dB under the voice")
# effects: peak-aligned on the cut, from AI_EDITOR_HOME/sfx/<kind>/ (your own files, rotated in name order)
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".aif", ".aiff", ".flac", ".ogg")
FX = {k: sorted(os.path.join(SFXD, k, f) for f in (os.listdir(os.path.join(SFXD, k)) if os.path.isdir(os.path.join(SFXD, k)) else [])
                if f.lower().endswith(AUDIO_EXT)) for k in ("whoosh", "pop", "shutter", "riser")}
silent = [k for k, v in FX.items() if not v]
if silent: print(f"no sound effects for: {', '.join(silent)} (add files to {SFXD}/<kind>/ to hear them)")
PEAK = {"whoosh": -27, "pop": -27, "shutter": -30, "riser": -28}
cache, rot = {}, {}
def sfx_at(kind, at_s, align_peak=True, max_s=0.9):
    files = FX.get(kind) or []
    if not files: return
    i = rot.get(kind, 0); rot[kind] = i + 1; f = files[i % len(files)]
    if f not in cache: cache[f] = pcm(f, 2)
    x = cache[f][: int((3.2 if kind == "riser" else max_s) * SR)]
    if kind == "riser": x = cache[f][-int(3.2 * SR):]                # the tail peaks on the payoff
    env = np.convolve((x ** 2).mean(1), np.ones(960) / 960, "same")
    pk = int(np.argmax(env)) if align_peak else 0
    x = x * 10 ** ((PEAK[kind] - 20 * np.log10(np.abs(x).max() + 1e-9)) / 20)
    fo = int(0.05 * SR); x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    s = int(at_s * SR) - pk
    a, z = max(0, s), min(N, s + len(x)); mix[a:z] += x[a - s: z - s]
for at_f, kind, name in events:
    if kind == "hero": sfx_at("riser", at_f / FPS); continue
    if kind: sfx_at(kind, at_f / FPS)
# master (voicechain): a trim of a fraction of a dB to −16 LUFS + the same short catch for the sum — no push to −14, no slow
# limiter; ONE lossy encode (ENC_AUDIO: Apple AAC 256k on macOS, ffmpeg's AAC elsewhere)
tmp = f"{OUT}/_mix.wav"; write_wav(tmp, mix)
cur, ceil = lufs_of(mix), -1.5
for _ in range(4):        # measured on the ENCODED file (AAC can overshoot the catch's ceiling) and corrected
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/picture.mp4", "-i", tmp, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", master_filter(cur, TARGET_LUFS, ceil)] + ENC_AUDIO + ["-shortest", "-movflags", "+faststart", f"{OUT}/final.mp4"], check=True)
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{OUT}/final.mp4", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    got = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    if abs(got - TARGET_LUFS) <= 0.3 and tp <= -1.0: break
    if tp > -1.0: ceil -= tp + 1.0 + 0.3
    cur += got - TARGET_LUFS
gain = TARGET_LUFS - cur
os.remove(tmp)
e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{OUT}/final.mp4", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
LI = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1]
print(f"→ {OUT}/final.mp4  {dur(OUT + '/final.mp4'):.2f}s · {LI} LUFS · true peak {TP} dBFS · mix gain {gain:+.1f} dB")
