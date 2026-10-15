"""plan.py — <slug> ("<working title>", <date>). Copy to <project>/edit/plan.py, next to gfx_slots.py, and fill in.
Read by tools/assemble.py (picture + sound) and tools/chapters.py (the chapters).

Every time is an ANCHOR on the spoken words: T("phrase") is the start of the first word of that phrase in the CUT
(work/words_out.json). Re-cut the take and every graphic moves with the words. Anchor on words, never on seconds.
The graphics themselves are listed ONCE, in gfx_slots.py (SLOTS + LOGOS): the helpers' briefs and this plan read the same table."""
import importlib.util, os
import aie                                           # tools/ is on the path when assemble.py / chapters.py load this plan

THEME = "warmcream"                                  # the room (STYLE.md "The theme"): "warmcream" (default) | "noir"
ACCENT = "#E0703A"                                   # ONE accent: the product's colour when the video is about one product
                                                     # (Claude #D97757, Gemini #8E75B2 …), else the theme's own. Every graphic of
                                                     # this video gets the same: <html data-theme=THEME data-accent=ACCENT>
GFX = "$AI_EDITOR_HOME/projects/<slug>/gfx"          # this video's graphics: <GFX>/<name>/renders/<name>*.mp4
HERO = None                                          # a beat-synced promo played as an insert with its own sound, e.g.
                                                     # "$AI_EDITOR_HOME/projects/<slug>/gfx/hero/renders/hero_v1.mp4"
HERO_AFTER = ("<last words before the breath>", "<first words after it>", 0)   # where it plays: in the breath between them
BEDS = []                                            # music beds: file names in AI_EDITOR_HOME/music/, played back to back
                                                     # ≈ 28 dB under the voice (e.g. ["track-one.mp3", "track-two.mp3"])
PUNCH = dict(zoom=1.12, fx=0.50, fy=0.40)            # the punch-in on every other jump cut: fx/fy = the face's centre (0..1)
# FANPRINT = (976.0, 38.0)                           # a computer fan audible? (start, length) s of PURE room tone in the take
                                                     # (≥ 20 s, no speech) → voicechain.fanprint at −8 dB before the lift
# FACE_CARD_ZOOM = 1.9; FACE_SIDE_ZOOM = 1.25        # how tight the face sits in the corner / side card
# PILLS = False                                      # no chapter pill (on when <GFX>/_pills/pills.json exists)
# MUSIC = [dict(file="$AI_EDITOR_HOME/music/x.mp3", out=0.0, src=12.0, dur=20.0, lufs=-17, duck=11, fout=1.6)]
#                                                    # a track at an OUTPUT time (a cold open's music), ducked under the voice

# (phrase that opens the chapter, title, seconds to shift) — 0.0 = the start, "HERO" = the hero insert.
# YouTube wants ≥ 3 chapters, the first at 0:00, each ≥ 10 s long.
CHAPTERS = [(0.0, "<what the video gives them>", 0),
            ("<first words of chapter 2>", "<chapter 2 title>", 0),
            ("<first words of chapter 3>", "<chapter 3 title>", 0)]

_s = importlib.util.spec_from_file_location("gfx_slots", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gfx_slots.py"))
_g = importlib.util.module_from_spec(_s); _s.loader.exec_module(_g)


def cutins(cut, T, gfx, HERO, AEND):
    """cut(name, file, at_s, end_s=None, src=0.0, sfx="whoosh", layout="graphic", pos="right", size=360)
      a graphic from at_s to end_s (A-roll seconds); end_s=None: as long as the clip runs; src: where in the clip to start;
      sfx: "whoosh" | "pop" (chapter cards, stickers) | "shutter" (flashes) | None (a follow-on shot that shouldn't whoosh again);
      layout: "graphic" (full frame) | "side" (the graphic at 65 % + the face card) | "corner" (the face card over the
      graphic's bottom-right) | "sticker" (a transparent clip over the FACE: pos "right"/"left"/"tr"/"tl"/"full", size px).
    gfx(name) → the newest finished render of <GFX>/<name>, or None: a graphic not rendered yet is skipped (the face stays).
    THE BALANCE (STYLE.md): FACE / BOTH / GRAPHIC about a third each, the face on screen ≥ 60 %, never > 12 s without it.
    `assemble.py <edit> --plan` prints the shares: fix the plan until the balance line ends in ✓."""
    for name, (a, b, cuts, who, what) in sorted(_g.SLOTS.items(), key=lambda x: x[1][0]):
        f = gfx(name)
        for k, (c0, c1, lay) in enumerate(cuts):
            if lay == "overlay":                             # a full-frame transparent clip over the face (tools/overlays.py)
                ov = os.path.join(aie.expand(GFX), name, "renders", f"{name}.mov")
                cut(name, ov, c0, c1, src=c0 - a, layout="sticker", pos="full", sfx="pop"); continue
            sfx = ("pop" if name.startswith("ch_") else "whoosh") if k == 0 else None   # a chapter card pops; a layout change is silent
            if name == "end_card": c0, c1 = AEND, None
            # src = how far into the graphic this span starts: the graphic's clock starts at its slot (a), so it stays on the words
            cut(name if k == 0 else f"{name}~{k}", f, c0, c1, src=(c0 - a) if name != "end_card" else 0.0, sfx=sfx, layout=lay)
    # LOGOS (STYLE.md "Logos"): the 3D mark beside the head while the brand is named on the FACE (gfxlib/logo_clip.py, once per brand)
    for slug, phrase, after, dur, pos in _g.LOGOS:
        clip = os.path.join(aie.LOGOS3D, slug, "renders", f"{slug}.mov")
        t = T(phrase, after)
        cut(f"logo_{slug}_{int(t)}", clip, t - 0.1, t + dur, layout="sticker", pos=pos, size=360)
