#!/usr/bin/env python3
"""theme.py — the graphics' themes, for the tools that composite and check them (assemble.py, qc.py).

The palettes live ONCE, in gfxlib/gfx.js (the strict-JSON block between the /*THEMES*/ markers); this parses it, so a
colour changed there changes the face cards, the base under them and the checks too.
  palette(name)        → the theme dict (bg, ink, line, light, contact, …) + "name"
  hexrgb("#F2ECE1")    → (242, 236, 225)
  activity(f, src, n)  → per-frame edge energy of a clip's first n frames from src (ground + vignette + grain score low)
  empty_lead(f, src)   → how many frames at src are the EMPTY STAGE before the first element lands (0 if none):
                         dark stage → the luma rule; light stage → the edge rule
  blank(pil_image)     → is a frame an empty stage (black on noir, a blank cream page on Warm Cream)

  theme.py <clip> [src]   prints the activity of the first 24 frames (to check a graphic's opening by eye)"""
import json, os, re, subprocess, sys
import numpy as np

GFX_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gfxlib", "gfx.js")
DEFAULT = "warmcream"


def themes():
    s = open(GFX_JS).read()
    return json.loads(re.search(r"/\*THEMES\*/(.*?)/\*/THEMES\*/", s, re.S).group(1))


def palette(name=None):
    t = themes(); name = name or DEFAULT
    if name not in t: raise SystemExit(f"theme {name!r} not in gfxlib/gfx.js THEMES ({', '.join(t)})")
    return dict(t[name], name=name)


hexrgb = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
W_, H_ = 192, 108


def grey(f, src=0.0, n=24):
    """the first n frames from src, grey, 192×108 (area-scaled, so grain averages out)"""
    still = f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    inp = ["-loop", "1", "-i", f] if still else ["-ss", f"{src:.3f}", "-i", f]
    r = subprocess.run(["ffmpeg", "-v", "error"] + inp + ["-frames:v", str(n), "-vf", f"scale={W_}:{H_}:flags=area,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8); k = len(a) // (W_ * H_)
    return a[: k * W_ * H_].reshape(k, H_, W_).astype(np.float32)


def edges(g):
    """edge energy per frame: mean |dx| + |dy| of grey frames (k, 108, 192)"""
    return np.abs(np.diff(g, axis=2)).mean(axis=(1, 2)) + np.abs(np.diff(g, axis=1)).mean(axis=(1, 2))


def activity(f, src=0.0, n=24):
    g = grey(f, src, n)
    return edges(g) if len(g) else np.array([])


# calibrated on real renders. A DARK stage (noir): near-black (mean luma < 6) until the first
# element lights it (≥ 6.5 and +2). Its grain scores 1.2–1.3 on edges, so edges can't tell it from content there. A LIGHT stage
# (Warm Cream) is never dark: its empty opening scores ~0.5 on edges (ground, vignette, grain) and the first card or word
# landing lifts it past 0.85 within a frame or two.
LIGHT_EMPTY = 0.75


def empty_lead(f, src=0.0, n=24):
    """frames of EMPTY STAGE at src before the first element lands; the clip should start there instead (cutting into an
    empty stage from the face reads as a dip: to black on noir, to a blank page on Warm Cream). 0 when the clip opens on content."""
    g = grey(f, src, n)
    if not len(g): return 0
    lum = g.mean(axis=(1, 2))
    if lum[0] < 40:                                                   # a dark stage: the luma rule
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{src:.3f}", "-i", f, "-frames:v", str(n), "-vf", "scale=96:54,format=gray",
                            "-f", "rawvideo", "-"], capture_output=True)
        a = np.frombuffer(r.stdout, np.uint8); k = len(a) // (96 * 54)
        lum = a[: k * 96 * 54].reshape(k, -1).mean(axis=1) if k else np.array([])
        if not len(lum) or lum[0] >= 6.0: return 0
        return int(next((i for i, v in enumerate(lum) if v >= max(6.5, lum[0] + 2.0)), len(lum)))
    act = edges(g)                                                    # a light stage
    if act[0] >= LIGHT_EMPTY: return 0
    return int(next((i for i, v in enumerate(act) if v >= max(act[0] * 1.6, act[0] + 0.3)), 0))   # no rise: a quiet still, not a lead


def blank(img):
    """is this frame (a PIL image) an empty stage? — qc.py's check at every switch, on any theme"""
    from PIL import Image
    g = np.asarray(img.convert("L").resize((W_, H_), Image.BOX), np.float32)[None]
    m = float(g.mean())
    return m < 6 or (m > 150 and float(edges(g)[0]) < LIGHT_EMPTY)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip()); sys.exit(0 if len(sys.argv) > 1 else 2)
    f = sys.argv[1]; src = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    act = activity(f, src)
    print(" ".join(f"{v:.2f}" for v in act)); print(f"empty lead: {empty_lead(f, src)} frames")
