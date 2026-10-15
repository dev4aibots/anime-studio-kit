#!/usr/bin/env python3
"""make_icons.py — a line-icon graphic from the speaker's words: icons drawn stroke by stroke in the theme's accent.
    make_icons.py <out dir> --items '[["search","find the leads",0.2],["bot","the agent replies",1.1]]' [--flow] [--dur 4]
                  [--theme warmcream|noir] [--accent "#E0703A"]
icon = a Lucide name (icons/lucide/*.svg — 96 included, ISC licence; more at lucide.dev); label = the spoken words;
t = when they are said (seconds into this clip). --flow joins the icons with a line drawn between them.
Then: bash <skill>/tools/render.sh <out dir> <name> --fonts "Geist,Instrument Serif" (one render at a time)."""
import argparse, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools")); import aie
aie.usage(__doc__)
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--items", required=True); ap.add_argument("--flow", action="store_true")
ap.add_argument("--dur", type=float, default=4.0); ap.add_argument("--gfx", default=os.environ.get("GFX_JS") or os.path.join(HERE, "..", "..", "gfx.js"))
ap.add_argument("--theme", default="warmcream"); ap.add_argument("--accent", default="", help="the video's accent, e.g. #D97757 (default: the theme's)")
a = ap.parse_args()
items = [dict(icon=i, label=l, t=float(t)) for i, l, t in json.loads(a.items)]
def as_paths(svg):
    """Every shape as a <path>, so each stroke has a reliable length to draw along (a rounded <rect> didn't draw)."""
    A = lambda tag: dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
    def f(x): return float(x)
    def rep(m):
        tag, a = m.group(1), A(m.group(0))
        if tag == "circle":
            cx, cy, r = f(a["cx"]), f(a["cy"]), f(a["r"]); d = f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0"
        elif tag == "ellipse":
            cx, cy, rx, ry = f(a["cx"]), f(a["cy"]), f(a["rx"]), f(a["ry"]); d = f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 {-2 * rx} 0"
        elif tag == "line":
            d = f"M{a['x1']} {a['y1']}L{a['x2']} {a['y2']}"
        elif tag in ("polyline", "polygon"):
            pts = re.findall(r"-?[\d.]+", a["points"]); xy = [f"{pts[i]} {pts[i + 1]}" for i in range(0, len(pts) - 1, 2)]
            d = "M" + "L".join(xy) + ("Z" if tag == "polygon" else "")
        elif tag == "rect":
            x, y, w, h = f(a.get("x", 0)), f(a.get("y", 0)), f(a["width"]), f(a["height"])
            r = min(f(a.get("rx", a.get("ry", 0))), w / 2, h / 2)
            d = (f"M{x + r} {y}H{x + w - r}" + (f"A{r} {r} 0 0 1 {x + w} {y + r}" if r else "") + f"V{y + h - r}"
                 + (f"A{r} {r} 0 0 1 {x + w - r} {y + h}" if r else "") + f"H{x + r}" + (f"A{r} {r} 0 0 1 {x} {y + h - r}" if r else "")
                 + f"V{y + r}" + (f"A{r} {r} 0 0 1 {x + r} {y}" if r else "") + "Z")
        else:
            return m.group(0)
        return f'<path d="{d}" />'
    return re.sub(r"<(circle|ellipse|line|polyline|polygon|rect)\b[^>]*/>", rep, svg)

icons = {}
for it in items:
    svg = open(os.path.join(HERE, "lucide", f"{it['icon']}.svg")).read()
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
    svg = re.sub(r'\s(width|height|class)="[^"]*"', "", svg, count=3)               # sized and coloured by the tile's CSS
    icons[it["icon"]] = as_paths(svg)
os.makedirs(os.path.join(a.out, "assets"), exist_ok=True); os.makedirs(os.path.join(a.out, "renders"), exist_ok=True)   # render.sh writes there
for f in ("hyperframes.json", "package.json"):
    shutil.copy2(os.path.join(HERE, "..", "..", "project", f), os.path.join(a.out, f))
json.dump({"id": os.path.basename(os.path.abspath(a.out)), "name": os.path.basename(os.path.abspath(a.out))}, open(os.path.join(a.out, "meta.json"), "w"), indent=2)
shutil.copy2(a.gfx, os.path.join(a.out, "assets", "gfx.js"))
t = open(os.path.join(HERE, "icons.tpl")).read()
t = t.replace("%%THEME%%", a.theme).replace("%%ACCENT%%", a.accent).replace("%%DUR%%", str(a.dur)).replace("%%ITEMS%%", json.dumps(items)).replace("%%FLOW%%", "true" if a.flow else "false").replace("%%ICONS%%", json.dumps(icons))
open(os.path.join(a.out, "index.tpl"), "w").write(t)
print(f"{a.out}: {len(items)} icons ({', '.join(i['icon'] for i in items)}), {a.dur}s, flow={a.flow}")
