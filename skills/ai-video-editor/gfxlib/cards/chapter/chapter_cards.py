#!/usr/bin/env python3
"""chapter_cards.py — numbered chapter cards + the chapter pill, from one list of the speaker's words.

    chapter_cards.py <gfx dir> chapters.json [--theme warmcream|noir] [--accent "#E0703A"]
chapters.json: [["ch_cache", "Cache Tax", "know before a cold send costs you"], ["ch_blast", "Blast Radius", ""], …]
   name · title (the speaker's words, as said) · subtitle (their words, or "" for none). Numbered in order: 01, 02, …
   (example: templates/chapters.example.json)
→ <dir>/<name>/ a HyperFrames card (1.8 s; render each with tools/render.sh <dir>/<name> <name> --fonts "Geist,Instrument Serif")
→ <dir>/_pills/<NN>.png the pill for the corner while that chapter plays (transparent 1920×1080, top-left)
→ <dir>/_pills/pills.json {card name: "NN.png"}: tools/assemble.py lays each pill from the end of its card to the next card"""
import argparse, json, os, re, shutil, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
TPL = open(os.path.join(HERE, "chapter.tpl")).read()
GFX = os.environ.get("GFX_JS") or os.path.join(HERE, "..", "..", "gfx.js")   # the themed library (gfxlib/gfx.js)
PROJECT = os.path.join(HERE, "..", "..", "project")                          # hyperframes.json + package.json for every graphic
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools")); import theme as _theme, aie

def rgba(c, a=255):
    """'#RRGGBB' or 'rgba(r,g,b,a)' → (r, g, b, a 0..255)"""
    m = re.match(r"rgba?\(([^)]*)\)", c)
    if m:
        v = [float(x) for x in m.group(1).split(",")]
        return tuple(int(x) for x in v[:3]) + (int(round((v[3] if len(v) > 3 else 1) * 255)),)
    return _theme.hexrgb(c) + (a,)

def palette(name, accent=""):
    T = _theme.palette(name); ct = tuple(int(v) for v in T["contact"].split(","))
    surf = rgba(T["surf"])[:3] if T["light"] else (24, 24, 28)        # noir: the pill is dark glass, opaque enough to read over the face
    return dict(surf=surf, ink=rgba(T["ink"])[:3], accent=_theme.hexrgb(accent or T["accentT"]), line=rgba(T["line"])[:3] + (max(30, rgba(T["line"])[3]),),
                shadow=ct + ((46,) if T["light"] else (140,)), serif=T["serif"])
P = palette("warmcream")

def pill(num, title, path, x=48, y=44):
    serif = ImageFont.truetype(aie.ttf("InstrumentSerif.ttf" if P["serif"] else "Geist.ttf"), 44 if P["serif"] else 34)
    if not P["serif"]: serif.set_variation_by_axes([700])
    sans = ImageFont.truetype(aie.ttf("Geist.ttf"), 26); sans.set_variation_by_axes([600])
    tw = int(serif.getlength(title)); nw = int(sans.getlength(num) + 0.16 * 26 * len(num))
    w, h = 28 + nw + 18 + tw + 30, 72
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x, y + 8, x + w, y + h + 6], h // 2, fill=P["shadow"])
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], h // 2, fill=P["surf"] + (255,), outline=P["line"], width=2)
    cx = x + 28
    for ch in num:                                                     # tracked like the card's number
        d.text((cx, y + h / 2), ch, font=sans, fill=P["accent"], anchor="lm"); cx += sans.getlength(ch) + 0.16 * 26
    d.text((x + 28 + nw + 18, y + h / 2 + 2), title, font=serif, fill=P["ink"], anchor="lm")
    im.save(path)

if __name__ == "__main__":
    aie.usage(__doc__, need=2)
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("chapters"); ap.add_argument("--theme", default="warmcream")
    ap.add_argument("--accent", default="", help="the video's accent, e.g. #D97757 (default: the theme's)")
    a = ap.parse_args()
    out, chapters = aie.expand(a.out), json.load(open(aie.expand(a.chapters)))
    P.update(palette(a.theme, a.accent))
    os.makedirs(os.path.join(out, "_pills"), exist_ok=True); pills = {}
    for i, (name, title, sub) in enumerate(chapters, 1):
        d = os.path.join(out, name); os.makedirs(os.path.join(d, "assets"), exist_ok=True); os.makedirs(os.path.join(d, "renders"), exist_ok=True)   # render.sh writes there
        for f in ("hyperframes.json", "package.json"):
            shutil.copy2(os.path.join(PROJECT, f), os.path.join(d, f))
        json.dump({"id": name, "name": name}, open(os.path.join(d, "meta.json"), "w"), indent=2)
        shutil.copy2(GFX, os.path.join(d, "assets", "gfx.js"))
        open(os.path.join(d, "index.tpl"), "w").write(TPL.replace("%%THEME%%", a.theme).replace("%%ACCENT%%", a.accent).replace("%%NUM%%", f"{i:02d}").replace("%%WORD%%", title).replace("%%SUB%%", sub.replace("`", "'")))
        pill(f"{i:02d}", title, os.path.join(out, "_pills", f"{i:02d}.png")); pills[name] = f"{i:02d}.png"
        json.dump(pills, open(os.path.join(out, "_pills", "pills.json"), "w"), indent=1)
        print(f"{i:02d}  {name:14s} {title!r}  {sub!r}")
