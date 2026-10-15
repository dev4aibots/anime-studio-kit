#!/usr/bin/env python3
"""overlays.py — full-frame TRANSPARENT overlays laid over the FACE (assemble.py: cut(…, layout="sticker", pos="full")),
composited frame by frame with PIL, one ProRes 4444 encode.

    overlays.py logos <edit_dir> --from "first words" --to "last words" [--after S] --mark SLUG:"phrase":X,Y [--mark …] --out o.mov
        several 3D logos pop beside the speaker, each on the word that names it, and stay until the end of the span.
        SLUG = a clip rendered once by gfxlib/logo_clip.py (AI_EDITOR_HOME/logos3d/<slug>/renders/<slug>.mov);
        X,Y = where its centre sits in the 1920×1080 frame (keep clear of the face); times from work/words_out.json
    overlays.py ring --box X0,Y0,X1,Y1 --at S --dur S [--accent '#E0703A'] --out o.mov
        an accent ring draws itself around a box on screen (e.g. the chapter pill top-left) and a short arrow points at it

Cut it in from the span's first word: cut(name, "o.mov", T("first words"), T("last words"), layout="sticker", pos="full").
→ the .mov + <name>-sheet.png (frames on a grey ground, so the transparent parts read)."""
import argparse, json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

FPS, W, H = 30, 1920, 1080


def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def spring(t, k=300.0, d=24.0):
    if t <= 0: return 0.0
    w0 = math.sqrt(k); z = d / (2 * w0)
    if z < 1:
        wd = w0 * math.sqrt(1 - z * z)
        return 1 - math.exp(-z * w0 * t) * (math.cos(wd * t) + (z * w0 / wd) * math.sin(wd * t))
    return 1 - math.exp(-w0 * t) * (1 + w0 * t)


def clip_frames(path, size, n):
    """the first n frames of a transparent clip, RGBA, size×size (looped if shorter)"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={size}:{size}:flags=lanczos,format=rgba", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, size, size, 4)
    return [Image.fromarray(fr[i % len(fr)].copy(), "RGBA") for i in range(n)]


def encode(frames_iter, n, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", out], stdin=subprocess.PIPE)
    sheet = []
    for i, im in enumerate(frames_iter):
        p.stdin.write(im.tobytes())
        if i in (int(n * 0.25), int(n * 0.5), int(n * 0.75), max(0, n - 4)): sheet.append(im.copy())
    p.stdin.close(); p.wait()
    sh = Image.new("RGB", (W, H), (110, 110, 110))
    for k, im in enumerate(sheet[:4]):
        t = Image.new("RGB", (W, H), (110, 110, 110)); t.paste(im, (0, 0), im)
        sh.paste(t.resize((W // 2, H // 2)), ((k % 2) * W // 2, (k // 2) * H // 2))
    sh.save(out[:-4] + "-sheet.png")
    print("→", out, f"{n / FPS:.2f}s")


def words_T(edit):
    W_ = [x for x in json.load(open(os.path.join(edit, "work", "words_out.json"))) if x["t"] is not None]
    nw = lambda s: re.sub(r"[^a-z0-9$]", "", s.lower())
    def T(phrase, after=0.0):
        toks = [nw(p) for p in phrase.split()]
        for i in range(len(W_) - len(toks) + 1):
            if W_[i]["t"] < after - 1e-6: continue
            if all(nw(W_[i + j]["w"]).startswith(toks[j]) for j in range(len(toks))): return W_[i]["t"]
        raise SystemExit(f"anchor not found: {phrase!r} after {after}")
    return T


def logos(a):
    T = words_T(os.path.abspath(a.edit))
    t0, t1 = T(a.frm, a.after), T(a.to, a.after); n = int(round((t1 - t0) * FPS))
    if n <= 0: sys.exit("--to must come after --from")
    S = 300
    marks = []
    for m in a.mark:
        mm = re.match(r'([^:]+):(.+):(\d+),(\d+)$', m)
        if not mm: sys.exit(f"--mark {m!r}: write it SLUG:phrase:X,Y (e.g. openai:OpenAI:1570,300)")
        slug, phrase, x, y = mm.group(1), mm.group(2).strip('"'), int(mm.group(3)), int(mm.group(4))
        clip = os.path.join(aie.LOGOS3D, slug, "renders", f"{slug}.mov")
        if not os.path.exists(clip): sys.exit(f"no 3D logo clip for {slug}: python gfxlib/logo_clip.py {slug}")
        marks.append((slug, T(phrase, t0 - 0.5) - t0, (x, y), clip_frames(clip, S, n)))
    def frames():
        for i in range(n):
            t = i / FPS
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for slug, tm, (cx, cy), src in marks:
                u = t - (tm - 0.06)
                if u <= 0: continue
                k = max(0.02, spring(u, 300, 22))                      # a pop with a little overshoot
                fr = src[min(n - 1, int(u * FPS))]
                sz = max(2, int(S * k)); fr = fr.resize((sz, sz), Image.LANCZOS)
                if u < 0.08: fr.putalpha(fr.getchannel("A").point(lambda v, u=u: int(v * u / 0.08)))
                im.alpha_composite(fr, (int(cx - sz / 2), int(cy - sz / 2)))
            yield im
    encode(frames(), n, a.out)


def ring(a):
    ACC = hexrgb(a.accent); n = int(round(a.dur * FPS))
    x0, y0, x1, y1 = [float(v) for v in a.box.split(",")]
    r = (y1 - y0) / 2
    pts = []
    def arc(cx, cy, a0, a1, steps=24):
        for j in range(steps + 1):
            th = a0 + (a1 - a0) * j / steps; pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    pts.append((x0 + r, y0)); pts.append((x1 - r, y0)); arc(x1 - r, y0 + r, -math.pi / 2, math.pi / 2)
    pts.append((x0 + r, y1)); arc(x0 + r, y0 + r, math.pi / 2, 3 * math.pi / 2)
    seg = [math.dist(pts[j], pts[j + 1]) for j in range(len(pts) - 1)]; L = sum(seg)
    def frames():
        for i in range(n):
            t = i / FPS
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            p = min(1.0, max(0.0, (t - a.at) / 0.55)); p = 1 - (1 - p) ** 3     # draw on, ease out
            if p > 0:
                want, acc, path = p * L, 0.0, [pts[0]]
                for j, s_ in enumerate(seg):
                    if acc + s_ >= want:
                        f = (want - acc) / s_; q0, q1 = pts[j], pts[j + 1]
                        path.append((q0[0] + (q1[0] - q0[0]) * f, q0[1] + (q1[1] - q0[1]) * f)); break
                    acc += s_; path.append(pts[j + 1])
                glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).line(path, fill=ACC + (150,), width=14, joint="curve")
                im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(7)))
                ImageDraw.Draw(im).line(path, fill=ACC + (255,), width=5, joint="curve")
                q = min(1.0, max(0.0, (t - a.at - 0.45) / 0.35)); q = 1 - (1 - q) ** 3      # the arrow, after the ring closes
                if q > 0:
                    ax1, ay1 = x1 + 26, y1 + 18; ax0, ay0 = ax1 + 150, ay1 + 95
                    ex, ey = ax0 + (ax1 - ax0) * q, ay0 + (ay1 - ay0) * q
                    d_ = ImageDraw.Draw(im); d_.line([(ax0, ay0), (ex, ey)], fill=ACC + (255,), width=6)
                    if q > 0.95:
                        ang = math.atan2(ay1 - ay0, ax1 - ax0)
                        for s_ in (-1, 1):
                            d_.line([(ax1, ay1), (ax1 - 30 * math.cos(ang + s_ * 0.5), ay1 - 30 * math.sin(ang + s_ * 0.5))], fill=ACC + (255,), width=6)
            yield im
    encode(frames(), n, a.out)


if __name__ == "__main__":
    aie.usage(__doc__)
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="kind", required=True)
    p = sp.add_parser("logos"); p.add_argument("edit"); p.add_argument("--from", dest="frm", required=True); p.add_argument("--to", required=True)
    p.add_argument("--after", type=float, default=0.0); p.add_argument("--mark", action="append", default=[]); p.add_argument("--out", required=True)
    p = sp.add_parser("ring"); p.add_argument("--box", required=True); p.add_argument("--at", type=float, default=0.3)
    p.add_argument("--dur", type=float, required=True); p.add_argument("--accent", default="#E0703A"); p.add_argument("--out", required=True)
    a = ap.parse_args()
    logos(a) if a.kind == "logos" else ring(a)
