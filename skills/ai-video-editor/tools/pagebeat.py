#!/usr/bin/env python3
"""pagebeat.py — a REAL page capture (a 2× PNG: capture.py's desktop_full@2x.png, or any 2× screenshot) as a Warm Cream beat:
the page as a window on the cream ground, the camera easing in on the line being quoted and an accent ring drawing around it,
the rest of the page dimmed a touch. For videos that read from real pages on camera. screenfollow.py does this for SCREEN
RECORDINGS; this one renders from the capture's full resolution every frame, so a 2.2× zoom on a paragraph stays crisp.

    pagebeat.py <capture.png> --dur 6.2 --out clip.mp4 --move 1.4,6.2,x,y,w,h[,fill] [--move …]
                [--source example.com] [--accent '#E0703A'] [--ground '#F2ECE1'] [--ocr "phrase" …]

  --move t0,t1,x,y,w,h[,fill]  from t0 to t1 (seconds into the clip) the camera holds on the box x,y,w,h (capture pixels)
                               so it fills `fill` of the frame width (default 0.78, at most --max-zoom); the ring draws
                               once the move lands and fades at t1. Between moves the camera eases back to the page.
  --ocr "phrase"               print the OCR'd lines of the capture that contain the phrase (to find a box), then exit (macOS)
  --source                     a small pill above the page with the site it came from (a credit; real, not the speaker's words)
→ clip.mp4 (1920×1080, 30 fps, silent) + clip.sheet.jpg (a frame per second)"""
import argparse, json, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, MOVE = 1920, 1080, 30, 0.75


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease(u):
    u = min(1.0, max(0.0, u)); return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def ocr(png, phrases):
    if not aie.ocr_bin(): sys.exit("--ocr needs macOS (Apple Vision) and swiftc; measure the box in an image viewer instead")
    for l in aie.ocr(png):
        if not phrases or any(p.lower() in l["text"].lower() for p in phrases):
            print(f'{l["x"]:7.0f},{l["y"]:6.0f},{l["w"]:6.0f},{l["h"]:5.0f}  {l["text"]}')


def main():
    aie.usage(__doc__)
    ap = argparse.ArgumentParser()
    ap.add_argument("png"); ap.add_argument("--dur", type=float); ap.add_argument("--out")
    ap.add_argument("--move", action="append", default=[]); ap.add_argument("--source", default="")
    ap.add_argument("--accent", default="#E0703A"); ap.add_argument("--ground", default="#F2ECE1")
    ap.add_argument("--max-zoom", dest="max_zoom", type=float, default=2.3); ap.add_argument("--ocr", action="append")
    ap.add_argument("--start", type=float, default=0.0, help="seconds of the slot already gone (keeps the drift continuous)")
    a = ap.parse_args()
    if a.ocr is not None:
        ocr(a.png, [p for p in a.ocr if p]); return
    cap = cv2.imread(a.png, cv2.IMREAD_COLOR)
    ch, cw = cap.shape[:2]
    lvl = cv2.resize(cap, (int(cw * 0.6), int(ch * 0.6)), interpolation=cv2.INTER_AREA)     # the overview level
    ground, ring = np.array(hexrgb(a.ground)[::-1], np.float32), hexrgb(a.accent)[::-1]
    top = 70 if a.source else 0                                             # room for the source pill
    k = min(W * 0.86 / cw, (H - top) * 0.84 / ch)
    wx0, wy0 = W / 2, top / 2 + H / 2                                       # the window's centre on screen at zoom 1
    moves = []
    for m in a.move:
        v = [float(x) for x in m.split(",")]
        t0, t1, x, y, w, h = v[:6]; fill = v[6] if len(v) > 6 else 0.78
        z = min(a.max_zoom, max(1.0, min(W * fill / (w * k), H * 0.62 / (h * k))))
        moves.append(dict(t0=t0, t1=t1, box=(x, y, w, h), z=z))

    def target(t):
        for m in moves:
            if m["t0"] <= t < m["t1"]:
                x, y, w, h = m["box"]; return (x + w / 2, y + h / 2, m["z"], m)
        return (cw / 2, ch / 2, 1.0, None)

    n = int(round(a.dur * FPS))
    # camera keys: a new target whenever the active move changes
    keys, prev = [], "start"
    for i in range(n):
        tg = target(i / FPS)
        if prev == "start" or tg[3] is not prev:
            keys.append((i, tg))
        prev = tg[3]
    font = ImageFont.truetype(aie.ttf("Geist.ttf"), 26); font.set_variation_by_axes([600])
    pill = None
    if a.source:
        tw = int(font.getlength(a.source)); pw, ph = tw + 64, 46
        from PIL import ImageFilter
        shl = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0))
        ImageDraw.Draw(shl).rounded_rectangle([20, 24, 20 + pw, 24 + ph], ph // 2, fill=(70, 45, 20, 40))
        im = shl.filter(ImageFilter.GaussianBlur(6)); d = ImageDraw.Draw(im)       # a soft warm shadow, then the pill on it
        d.rounded_rectangle([20, 18, 20 + pw, 18 + ph], ph // 2, fill=(255, 252, 247, 255), outline=(70, 45, 20, 34), width=2)
        d.ellipse([38, 18 + ph // 2 - 6, 50, 18 + ph // 2 + 6], fill=hexrgb(a.accent) + (255,))
        d.text((60, 18 + ph // 2), a.source, font=font, fill=(31, 27, 23, 255), anchor="lm")
        pill = np.array(im)[..., [2, 1, 0, 3]].astype(np.float32)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                            "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    cur = (cw / 2, ch / 2, 1.0); frm, ki = cur, 0
    sheet = []
    for i in range(n):
        t = i / FPS
        while ki + 1 < len(keys) and keys[ki + 1][0] <= i:
            ki += 1; frm = cur
        k0, tg = keys[ki]
        u = ease((i - k0) / FPS / MOVE)
        cur = tuple(frm[j] + (tg[j] - frm[j]) * u for j in range(3))
        cx, cy, z = cur
        z *= 1.0 + 0.018 * (a.start + t) / max(1.0, a.start + a.dur)       # a slow push, so the page is never frozen
        s = k * z
        # where the window centre sits: at zoom 1 the page is centred under the pill; zoomed in, the camera centres the box
        blend = min(1.0, (z - 1.0) / 0.35) if z > 1 else 0.0
        sx = (1 - blend) * wx0 + blend * W / 2; sy = (1 - blend) * wy0 + blend * H / 2
        tx, ty = sx - cx * s, sy - cy * s
        if s < 0.9:
            sl = s / 0.6; M = np.float32([[sl, 0, tx], [0, sl, ty]]); src = lvl
        else:
            M = np.float32([[s, 0, tx], [0, s, ty]]); src = cap
        page = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC if s >= 0.9 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        # the window: rounded rect in screen space + its contact shadow
        X0, Y0, X1, Y1 = tx, ty, tx + cw * s, ty + ch * s
        r = max(10, int(22 * z))
        mask = np.zeros((H, W), np.uint8)
        x0, y0, x1, y1 = int(round(X0)), int(round(Y0)), int(round(X1)), int(round(Y1))
        cv2.rectangle(mask, (x0 + r, y0), (x1 - r, y1), 255, -1); cv2.rectangle(mask, (x0, y0 + r), (x1, y1 - r), 255, -1)
        for ccx, ccy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
            cv2.circle(mask, (ccx, ccy), r, 255, -1, cv2.LINE_AA)
        sh = np.zeros((H // 4, W // 4), np.float32)
        cv2.rectangle(sh, (int(X0 / 4), int((Y0 + 16) / 4)), (int(X1 / 4), int((Y1 + 12) / 4)), 1.0, -1)
        sh = cv2.resize(cv2.GaussianBlur(sh, (0, 0), 7), (W, H)) * 0.17
        out = np.empty((H, W, 3), np.float32); out[:] = ground
        out *= (1 - sh[..., None])
        m3 = (mask.astype(np.float32) / 255)[..., None]
        out = out * (1 - m3) + page.astype(np.float32) * m3
        mv = tg[3]
        if mv is not None:
            age = (i - k0) / FPS
            ra = min(1.0, max(0.0, (age - MOVE * 0.8) / 0.35)) * min(1.0, max(0.0, (mv["t1"] - t) / 0.25))
            if ra > 0.005:
                bx, by, bw, bh = mv["box"]; pad = 10
                RX0, RY0 = (bx - pad) * s + tx, (by - pad) * s + ty; RX1, RY1 = (bx + bw + pad) * s + tx, (by + bh + pad) * s + ty
                dim = np.ones((H, W), np.float32) * (1 - 0.07 * ra)
                dim[max(0, int(RY0)):int(RY1), max(0, int(RX0)):int(RX1)] = 1.0
                out *= dim[..., None]
                # the ring draws along its perimeter, then stays
                ov = out.copy(); rr = int(min(16, (RY1 - RY0) / 2)); th = 6
                pts = []
                for (ax, ay, a0) in ((RX0 + rr, RY0 + rr, 180), (RX1 - rr, RY0 + rr, 270), (RX1 - rr, RY1 - rr, 0), (RX0 + rr, RY1 - rr, 90)):
                    for q in range(0, 91, 10):
                        ang = np.radians(a0 + q); pts.append((ax + rr * np.cos(ang), ay + rr * np.sin(ang)))
                pts.append(pts[0])
                pts = np.array(pts, np.float32)
                seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1)); L = seg.sum(); upto = L * min(1.0, ra * 1.15)
                acc, keep = 0.0, [pts[0]]
                for j in range(len(seg)):
                    if acc + seg[j] <= upto: keep.append(pts[j + 1]); acc += seg[j]
                    else:
                        f = (upto - acc) / max(seg[j], 1e-6); keep.append(pts[j] + (pts[j + 1] - pts[j]) * f); break
                cv2.polylines(ov, [np.int32(np.round(np.array(keep) * 4))], False, ring, th * 4 // 2, cv2.LINE_AA, shift=2)
                out = ov
        if pill is not None:
            pa = max(0.0, 1.0 - blend * 1.4)
            if pa > 0.01:
                ph_, pw_ = pill.shape[:2]; X, Y = 60, 12
                al = pill[..., 3:4] / 255 * pa
                out[Y:Y + ph_, X:X + pw_] = out[Y:Y + ph_, X:X + pw_] * (1 - al) + pill[..., :3] * al
        frame = np.clip(out, 0, 255).astype(np.uint8)
        enc.stdin.write(frame.tobytes())
        if i % FPS == 0: sheet.append(cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA))
    enc.stdin.close(); enc.wait()
    cols = 4; rows = (len(sheet) + cols - 1) // cols
    grid = np.full((rows * 270, cols * 480, 3), 255, np.uint8)
    for j, im in enumerate(sheet): grid[(j // cols) * 270:(j // cols + 1) * 270, (j % cols) * 480:(j % cols + 1) * 480] = im
    cv2.imwrite(a.out[:-4] + ".sheet.jpg", grid, [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(a.out, f"{a.dur:.2f}s", f"{len(moves)} moves")


if __name__ == "__main__":
    main()
