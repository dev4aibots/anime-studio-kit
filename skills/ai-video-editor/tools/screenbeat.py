#!/usr/bin/env python3
"""screenbeat.py — show HOW the screen is read: a REAL page capture (2×, capture.py or any screenshot) as a window on the
cream ground, then the four moves the editor can make on a line of it:
  1. a scan line sweeps the page and an on-device OCR box (Apple Vision, macOS) pops over every line it passes;
  2. the view eases in on one line and an accent ring draws around it ("zoom in and circle");
  3. everything else dims to a soft spotlight on that line ("spotlight it");
  4. the spotlight lifts and an accent underline draws under it ("underline it").
Built on tools/pagebeat.py's window, push and ring (same look). → clip.mp4 + clip.sheet.jpg

    screenbeat.py <capture.png> --dur 13.9 --out clip.mp4 --line x,y,w,h --scan 0.4,3.6 --zoom 6.6 --ring 8.2
                  --spot 11.4 --under 12.5 [--source example.com] [--accent '#E0703A']
  --line x,y,w,h  the line to zoom on, in capture pixels (pagebeat.py --ocr "phrase" prints boxes on macOS)
  times (s into the clip): --scan from,to · --zoom · --ring · --spot · --under — put each on the word it illustrates
Without OCR (not macOS) the scan line still sweeps, without the per-line boxes."""
import argparse, json, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

W, H, FPS = 1920, 1080, 30


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease(u):
    u = min(1.0, max(0.0, u)); return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def outq(u):
    u = min(1.0, max(0.0, u)); return 1 - (1 - u) ** 3


def main():
    aie.usage(__doc__)
    ap = argparse.ArgumentParser()
    ap.add_argument("png"); ap.add_argument("--dur", type=float, required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--line", required=True); ap.add_argument("--scan", default="0.4,3.6")
    ap.add_argument("--zoom", type=float, required=True); ap.add_argument("--ring", type=float, required=True)
    ap.add_argument("--spot", type=float, required=True); ap.add_argument("--under", type=float, required=True)
    ap.add_argument("--source", default=""); ap.add_argument("--accent", default="#E0703A"); ap.add_argument("--ground", default="#F2ECE1")
    a = ap.parse_args()
    cap = cv2.imread(a.png, cv2.IMREAD_COLOR); ch, cw = cap.shape[:2]
    lvl = cv2.resize(cap, (int(cw * 0.6), int(ch * 0.6)), interpolation=cv2.INTER_AREA)
    ocr = [l for l in aie.ocr(a.png) if l["w"] > 30 and l["h"] > 12]
    ground = np.array(hexrgb(a.ground)[::-1], np.float32); acc = hexrgb(a.accent)[::-1]
    LX, LY, LW, LH = [float(v) for v in a.line.split(",")]
    s0, s1 = [float(v) for v in a.scan.split(",")]
    top = 70 if a.source else 0
    k = min(W * 0.86 / cw, (H - top) * 0.84 / ch)
    wx0, wy0 = W / 2, top / 2 + H / 2
    ZL = min(2.4, W * 0.62 / (LW * k))                                      # the zoom that makes the line fill ~62 % of the width
    font = ImageFont.truetype(aie.ttf("Geist.ttf"), 26); font.set_variation_by_axes([600])
    pill = None
    if a.source:
        from PIL import ImageFilter
        tw = int(font.getlength(a.source)); pw, ph = tw + 64, 46
        shl = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0))
        ImageDraw.Draw(shl).rounded_rectangle([20, 24, 20 + pw, 24 + ph], ph // 2, fill=(70, 45, 20, 40))
        im = shl.filter(ImageFilter.GaussianBlur(6)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 18, 20 + pw, 18 + ph], ph // 2, fill=(255, 252, 247, 255), outline=(70, 45, 20, 34), width=2)
        d.ellipse([38, 18 + ph // 2 - 6, 50, 18 + ph // 2 + 6], fill=hexrgb(a.accent) + (255,))
        d.text((60, 18 + ph // 2), a.source, font=font, fill=(31, 27, 23, 255), anchor="lm")
        pill = np.array(im)[..., [2, 1, 0, 3]].astype(np.float32)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    n = int(round(a.dur * FPS)); sheet = []
    for i in range(n):
        t = i / FPS
        # the camera: the page, then in on the line (from --zoom over 0.8 s), held through ring, spotlight and underline
        u = ease((t - a.zoom) / 0.8)
        cx = cw / 2 + (LX + LW / 2 - cw / 2) * u; cy = ch / 2 + (LY + LH / 2 - ch / 2) * u
        z = 1.0 + (ZL - 1.0) * u
        z *= 1.0 + 0.02 * t / a.dur
        s = k * z
        blend = min(1.0, (z - 1.0) / 0.35) if z > 1 else 0.0
        sx = (1 - blend) * wx0 + blend * W / 2; sy = (1 - blend) * wy0 + blend * H / 2
        tx, ty = sx - cx * s, sy - cy * s
        if s < 0.9: M = np.float32([[s / 0.6, 0, tx], [0, s / 0.6, ty]]); src = lvl
        else: M = np.float32([[s, 0, tx], [0, s, ty]]); src = cap
        page = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC if s >= 0.9 else cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        X0, Y0, X1, Y1 = tx, ty, tx + cw * s, ty + ch * s
        r = max(10, int(22 * z)); mask = np.zeros((H, W), np.uint8)
        x0, y0, x1, y1 = int(round(X0)), int(round(Y0)), int(round(X1)), int(round(Y1))
        cv2.rectangle(mask, (x0 + r, y0), (x1 - r, y1), 255, -1); cv2.rectangle(mask, (x0, y0 + r), (x1, y1 - r), 255, -1)
        for ccx, ccy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)): cv2.circle(mask, (ccx, ccy), r, 255, -1, cv2.LINE_AA)
        shd = np.zeros((H // 4, W // 4), np.float32)
        cv2.rectangle(shd, (int(X0 / 4), int((Y0 + 16) / 4)), (int(X1 / 4), int((Y1 + 12) / 4)), 1.0, -1)
        shd = cv2.resize(cv2.GaussianBlur(shd, (0, 0), 7), (W, H)) * 0.17
        out = np.empty((H, W, 3), np.float32); out[:] = ground; out *= (1 - shd[..., None])
        m3 = (mask.astype(np.float32) / 255)[..., None]; out = out * (1 - m3) + page.astype(np.float32) * m3
        ov = out.copy()
        # 1. the scan line and the OCR boxes (out by the zoom)
        box_a = 1.0 - outq((t - (a.zoom - 0.1)) / 0.45)
        if box_a > 0.01 and t > s0 - 0.05:
            ysc = (min(t, s1) - s0) / (s1 - s0) * ch                         # the scan line, in page px
            for l in ocr:
                if l["y"] > ysc: continue
                age = (t - (s0 + l["y"] / ch * (s1 - s0)))
                aa = min(1.0, max(0.0, age / 0.18)) * box_a
                if aa <= 0: continue
                bx0, by0 = l["x"] * s + tx - 4, l["y"] * s + ty - 3; bx1, by1 = (l["x"] + l["w"]) * s + tx + 4, (l["y"] + l["h"]) * s + ty + 3
                fill = ov.copy(); cv2.rectangle(fill, (int(bx0), int(by0)), (int(bx1), int(by1)), acc, -1)
                ov = ov * (1 - 0.13 * aa) + fill * 0.13 * aa
                lay = ov.copy(); cv2.rectangle(lay, (int(bx0 * 4), int(by0 * 4)), (int(bx1 * 4), int(by1 * 4)), acc, 2 * 4 // 2, cv2.LINE_AA, shift=2)
                ov = ov * (1 - aa) + lay * aa
            if t < s1 + 0.2:
                yl = ysc * s + ty
                band = np.exp(-(((np.arange(H) - yl) / 7.0) ** 2))[:, None, None] * (m3 > 0)
                ov = ov * (1 - 0.55 * band) + np.array(acc, np.float32) * 0.55 * band
        out = ov
        RX0, RY0 = (LX - 12) * s + tx, (LY - 10) * s + ty; RX1, RY1 = (LX + LW + 12) * s + tx, (LY + LH + 10) * s + ty
        # 3. the spotlight: everything but the line dims (soft edge), from --spot until --under + 0.3
        sp = outq((t - a.spot) / 0.35) * (1 - outq((t - a.under - 0.25) / 0.4))
        if sp > 0.005:
            hole = np.zeros((H, W), np.float32); cv2.rectangle(hole, (int(RX0 - 10), int(RY0 - 10)), (int(RX1 + 10), int(RY1 + 10)), 1.0, -1)
            hole = cv2.GaussianBlur(hole, (0, 0), 18)
            out = out * (1 - (0.62 * sp * (1 - hole))[..., None]) + np.array([24, 22, 20], np.float32) * (0.62 * sp * (1 - hole))[..., None] * 0.0
        # 2. the ring: draws from --ring, fades as the spotlight comes in
        ra = outq((t - a.ring) / 0.45) * (1 - outq((t - a.spot - 0.2) / 0.3))
        if ra > 0.005:
            rr = int(min(18, (RY1 - RY0) / 2)); pts = []
            for (ax, ay, a0) in ((RX0 + rr, RY0 + rr, 180), (RX1 - rr, RY0 + rr, 270), (RX1 - rr, RY1 - rr, 0), (RX0 + rr, RY1 - rr, 90)):
                for q in range(0, 91, 10):
                    ang = np.radians(a0 + q); pts.append((ax + rr * np.cos(ang), ay + rr * np.sin(ang)))
            pts.append(pts[0]); pts = np.array(pts, np.float32)
            seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1)); L = seg.sum(); upto = L * min(1.0, outq((t - a.ring) / 0.45) * 1.1)
            acc_, keep = 0.0, [pts[0]]
            for j in range(len(seg)):
                if acc_ + seg[j] <= upto: keep.append(pts[j + 1]); acc_ += seg[j]
                else: f = (upto - acc_) / max(seg[j], 1e-6); keep.append(pts[j] + (pts[j + 1] - pts[j]) * f); break
            lay = out.copy(); cv2.polylines(lay, [np.int32(np.round(np.array(keep) * 4))], False, acc, 7 * 4 // 2, cv2.LINE_AA, shift=2)
            fa = 1 - outq((t - a.spot - 0.2) / 0.3); out = out * (1 - fa) + lay * fa
        # 4. the underline: draws left to right under the line from --under
        ua = outq((t - a.under) / 0.5)
        if ua > 0.005:
            uy = RY1 + 6; ux1 = RX0 + 12 + (RX1 - RX0 - 24) * ua
            lay = out.copy(); cv2.line(lay, (int((RX0 + 12) * 4), int(uy * 4)), (int(ux1 * 4), int(uy * 4)), acc, 8 * 4 // 2, cv2.LINE_AA, shift=2)
            out = lay
        if pill is not None:
            pa = max(0.0, 1.0 - blend * 1.4)
            if pa > 0.01:
                ph_, pw_ = pill.shape[:2]; X, Y = 60, 12; al = pill[..., 3:4] / 255 * pa
                out[Y:Y + ph_, X:X + pw_] = out[Y:Y + ph_, X:X + pw_] * (1 - al) + pill[..., :3] * al
        frame = np.clip(out, 0, 255).astype(np.uint8); enc.stdin.write(frame.tobytes())
        if i % FPS == 0: sheet.append(cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA))
    enc.stdin.close(); enc.wait()
    cols = 4; rows = (len(sheet) + cols - 1) // cols
    grid = np.full((rows * 270, cols * 480, 3), 255, np.uint8)
    for j, im in enumerate(sheet): grid[(j // cols) * 270:(j // cols + 1) * 270, (j % cols) * 480:(j % cols + 1) * 480] = im
    cv2.imwrite(a.out[:-4] + ".sheet.jpg", grid, [cv2.IMWRITE_JPEG_QUALITY, 82]); print(a.out, f"{a.dur:.2f}s")


if __name__ == "__main__":
    main()
