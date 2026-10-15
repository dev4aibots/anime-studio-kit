#!/usr/bin/env python3
"""stickers.py — transparent stickers for the FACE (assemble.py: cut(…, layout="sticker")), drawn with PIL, ProRes 4444 (alpha).

    stickers.py subscribe [--out file.mov] [--label Subscribe] [--done Subscribed]
        a red Subscribe button pops in, is pressed (a ripple), turns grey "Subscribed" with a bell — for "make sure you're subscribed"
    stickers.py slash <icon.png> [--name not_x] [--out file.mov]
        a real app icon (a transparent PNG you rasterised from its official SVG) pops in, tilts, and a red slash draws across it
        — for "I didn't use X"

600×600, 30 fps, 3.0 s. Default output: AI_EDITOR_HOME/logos3d/<name>/renders/<name>.mov (+ <name>-sheet.png on grey), where the
plan's sticker helper finds logo clips too."""
import argparse, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

FPS, S, DUR = 30, 600, 3.0
N = int(DUR * FPS)


def spring(t, k=300.0, d=22.0):
    if t <= 0: return 0.0
    w0 = math.sqrt(k); z = d / (2 * w0); wd = w0 * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w0 * t) * (math.cos(wd * t) + (z * w0 / wd) * math.sin(wd * t))


def write(frames, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{S}x{S}", "-r", str(FPS), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", out], stdin=subprocess.PIPE)
    keep = []
    for i, im in enumerate(frames):
        p.stdin.write(im.tobytes())
        if i in (10, 30, 60, N - 2): keep.append(im.copy())
    p.stdin.close(); p.wait()
    sh = Image.new("RGB", (S * 4, S), (110, 110, 110))
    for k, im in enumerate(keep): sh.paste(im, (k * S, 0), im)
    sh.save(out[:-4] + "-sheet.png"); print("→", out)


def slash(icon_png, out):
    """the icon in its own colours, tilting gently in perspective with a soft shadow, popping in, then a red slash across it"""
    ico = Image.open(icon_png).convert("RGBA")
    bb = ico.getbbox(); ico = ico.crop(bb); iw, ih = ico.size
    k0 = min(1.0, 430 / max(iw, ih)); ico = ico.resize((max(2, int(iw * k0)), max(2, int(ih * k0))), Image.LANCZOS); iw, ih = ico.size
    T0 = 0.42                                                       # the slash draws ~0.4 s in: start the sticker just before the name
    def frames():
        for i in range(N):
            t = i / FPS
            im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            k = max(0.02, spring(t, 260, 20)); a = 0.16 * math.sin(t * 1.3)          # pop in, then a slow swing (a fake turn)
            w = iw * 0.86 * k; h = ih * 0.86 * k; cx, cy = S / 2, S / 2 - 6
            dx = w / 2 * math.cos(a); sk = h * 0.08 * math.sin(a)
            quad = [(cx - dx, cy - h / 2 - sk), (cx - dx, cy + h / 2 + sk), (cx + dx, cy + h / 2 - sk), (cx + dx, cy - h / 2 + sk)]
            sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle([cx - dx + 6, cy - h / 2 + 22, cx + dx + 6, cy + h / 2 + 22], int(42 * k), fill=(0, 0, 0, 120))
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
            x0 = int(min(q[0] for q in quad)); y0 = int(min(q[1] for q in quad)); x1 = int(max(q[0] for q in quad)) + 1; y1 = int(max(q[1] for q in quad)) + 1
            loc = [(q[0] - x0, q[1] - y0) for q in quad]
            src = [(0, 0), (0, ih), (iw, ih), (iw, 0)]                   # a perspective fit (8 coefficients) mapping out → in
            A, B = [], []
            for (X, Y), (u, v) in zip(loc, src):
                A.append([X, Y, 1, 0, 0, 0, -u * X, -u * Y]); B.append(u)
                A.append([0, 0, 0, X, Y, 1, -v * X, -v * Y]); B.append(v)
            coef = np.linalg.solve(np.array(A, float), np.array(B, float))
            warped = ico.transform((max(1, x1 - x0), max(1, y1 - y0)), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC)
            im.alpha_composite(warped, (max(0, x0), max(0, y0)))
            p = min(1.0, max(0.0, (t - T0) / 0.28)); p = 1 - (1 - p) ** 3
            if p > 0:
                sx0, sy0, sx1, sy1 = cx - w * 0.5, cy - h * 0.5, cx + w * 0.5, cy + h * 0.5
                ex, ey = sx0 + (sx1 - sx0) * p, sy0 + (sy1 - sy0) * p
                sl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ImageDraw.Draw(sl).line([(sx0, sy0 + 10), (ex, ey + 10)], fill=(40, 10, 10, 120), width=30)
                im.alpha_composite(sl.filter(ImageFilter.GaussianBlur(8)))
                d2 = ImageDraw.Draw(im)
                d2.line([(sx0, sy0), (ex, ey)], fill=(232, 40, 52, 255), width=26)
                for (qx, qy) in ((sx0, sy0), (ex, ey)): d2.ellipse([qx - 13, qy - 13, qx + 13, qy + 13], fill=(232, 40, 52, 255))
            yield im
    write(frames(), out)


def subscribe(out, label="Subscribe", done="Subscribed"):
    f = ImageFont.truetype(aie.ttf("Geist.ttf"), 60); f.set_variation_by_axes([600])
    TP = 0.95                                                       # the press
    bell = lambda d, cx, cy, c: (d.pieslice([cx - 26, cy - 30, cx + 26, cy + 22], 180, 360, fill=c), d.rectangle([cx - 26, cy - 5, cx + 26, cy + 14], fill=c),
                                 d.rectangle([cx - 32, cy + 10, cx + 32, cy + 18], fill=c), d.ellipse([cx - 8, cy + 18, cx + 8, cy + 32], fill=c))
    def frames():
        for i in range(N):
            t = i / FPS
            im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            k = spring(t, 260, 20)                                      # the button pops in
            if t > TP - 0.07: k *= 1 - 0.07 * math.sin(min(1, (t - TP + 0.07) / 0.3) * math.pi)   # the press dips it
            on = t >= TP
            text = done if on else label
            tw = f.getlength(text) + (70 if on else 0)
            w, h = int(tw + 110), 128
            btn = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
            sh = Image.new("RGBA", btn.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([40, 52, 40 + w, 52 + h], h // 2, fill=(0, 0, 0, 120))
            btn.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
            fill = (242, 242, 242, 255) if on else (255, 0, 51, 255)
            ink = (15, 15, 15, 255) if on else (255, 255, 255, 255)
            d.rounded_rectangle([40, 40, 40 + w, 40 + h], h // 2, fill=fill)
            x = 40 + 55
            if on: bell(d, x + 28, 40 + h // 2 - 4, ink); x += 70
            d.text((x, 40 + h / 2 + 2), text, font=f, fill=ink, anchor="lm")
            if on and t - TP < 0.5:                                      # the tap ripple
                r = 30 + 260 * (t - TP) / 0.5; a = int(110 * (1 - (t - TP) / 0.5))
                rp = Image.new("RGBA", btn.size, (0, 0, 0, 0)); ImageDraw.Draw(rp).ellipse([btn.size[0] / 2 - r, btn.size[1] / 2 - r, btn.size[0] / 2 + r, btn.size[1] / 2 + r], fill=(255, 255, 255, a))
                m = Image.new("L", btn.size, 0); ImageDraw.Draw(m).rounded_rectangle([40, 40, 40 + w, 40 + h], h // 2, fill=255)
                rp.putalpha(Image.fromarray(np.minimum(np.array(rp.getchannel("A")), np.array(m))))
                btn.alpha_composite(rp)
            sc = max(0.02, k) * min(1.0, (S - 20) / btn.size[0])
            b2 = btn.resize((max(2, int(btn.size[0] * sc)), max(2, int(btn.size[1] * sc))), Image.LANCZOS)
            im.alpha_composite(b2, ((S - b2.size[0]) // 2, (S - b2.size[1]) // 2))
            yield im
    write(frames(), out)


if __name__ == "__main__":
    aie.usage(__doc__)
    ap = argparse.ArgumentParser(); ap.add_argument("kind", choices=["subscribe", "slash"]); ap.add_argument("icon", nargs="?")
    ap.add_argument("--name"); ap.add_argument("--out"); ap.add_argument("--label", default="Subscribe"); ap.add_argument("--done", default="Subscribed")
    a = ap.parse_args()
    name = a.name or ("subscribe" if a.kind == "subscribe" else "not_" + os.path.splitext(os.path.basename(a.icon or "icon"))[0])
    out = a.out or os.path.join(aie.LOGOS3D, name, "renders", f"{name}.mov")
    if a.kind == "subscribe": subscribe(out, a.label, a.done)
    else:
        if not a.icon: sys.exit("slash needs an icon PNG (transparent): stickers.py slash path/to/icon.png")
        slash(a.icon, out)
