#!/usr/bin/env python3
"""logo_clip.py — a REAL logo as a transparent, slowly turning 3D clip (ProRes 4444 with alpha), to lay beside the speaker's
head while they name the brand (assemble.py: cut(…, layout="sticker")) or to drop into a graphic. Render it ONCE per brand:
every later video reuses it.

    logo_clip.py claude                       a slug from logos/logos.json — or a word it lists under "says" ("ChatGPT")
    logo_clip.py path/to/brand.svg --name acme        a brand's own SVG (its press kit), in its own colours
    options: --color '#hex'  --dur 6 (a seamless loop)  --size 600 (px, square)  --width 0.42 (of 0.6 = the frame)
             --swing 0.6 (rad each way)  --tilt 0.08  --out DIR (default AI_EDITOR_HOME/logos3d)  --no-render
→ <out>/<name>/renders/<name>.mov (+ <name>-sheet.png). Renders through tools/render.sh --alpha (one render at a time)."""
import argparse, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import aie

aie.usage(__doc__)
ap = argparse.ArgumentParser(); ap.add_argument("logo"); ap.add_argument("--name"); ap.add_argument("--color")
ap.add_argument("--dur", type=float, default=6.0); ap.add_argument("--size", type=int, default=600); ap.add_argument("--width", type=float, default=0.42)
ap.add_argument("--swing", type=float, default=0.6); ap.add_argument("--tilt", type=float, default=0.08)
ap.add_argument("--out", default=aie.LOGOS3D); ap.add_argument("--no-render", action="store_true")
a = ap.parse_args()
LIB = json.load(open(f"{HERE}/logos/logos.json"))
if a.logo.lower().endswith(".svg"): svg, name, color = aie.expand(a.logo), a.name or os.path.basename(a.logo)[:-4], a.color
else:
    key = a.logo.lower()
    if key not in LIB:                                               # a spoken name ("ChatGPT") → its slug ("openai")
        key = next((k for k, v in LIB.items() if any(s.lower() == a.logo.lower() for s in v["says"])), None)
    if not key: sys.exit(f"no logo for {a.logo!r} in logos.json — get the brand's own SVG (press kit, its site, Wikimedia Commons) and pass its path")
    svg, name, color = f"{HERE}/{LIB[key]['file']}", a.name or key, a.color or LIB[key]["color"]
d = f"{aie.expand(a.out)}/{name}"
os.makedirs(f"{d}/assets/logos", exist_ok=True); os.makedirs(f"{d}/renders", exist_ok=True)
for f in ("hyperframes.json", "package.json"): shutil.copy2(f"{HERE}/project/{f}", f"{d}/{f}")
json.dump({"id": name, "name": name}, open(f"{d}/meta.json", "w"), indent=2)
shutil.copy2(f"{HERE}/gfx.js", f"{d}/assets/gfx.js"); shutil.copy2(svg, f"{d}/assets/logos/{os.path.basename(svg)}")
cfg = dict(dur=a.dur, logo=f"assets/logos/{os.path.basename(svg)}", color=color, width=a.width * a.size / 600, swing=a.swing, tilt=a.tilt)
t = open(f"{HERE}/logo_clip.tpl").read().replace("/*CFG*/", json.dumps(cfg)).replace("/*DUR*/", str(a.dur)).replace("/*W*/", str(a.size)).replace("/*H*/", str(a.size))
open(f"{d}/index.tpl", "w").write(t)
print(f"{name}: {d}  ({cfg['logo']}, colour {color or 'its own'}, {a.dur}s loop, {a.size}px)")
if not a.no_render:
    env = dict(os.environ, PY=aie.python())
    r = subprocess.run(["bash", os.path.join(aie.TOOLS, "render.sh"), d, name, "--alpha"], env=env)
    sys.exit(r.returncode)
