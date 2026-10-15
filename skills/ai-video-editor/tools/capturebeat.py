#!/usr/bin/env python3
"""capturebeat.py — "it captures the real page": a browser window on the cream ground; the address bar types the real URL,
the real page (a capture: capture.py's desktop_hero@2x.png or any 2× screenshot) loads in top-down, a camera-shutter flash
and corner brackets close on the window ("captures"), then an accent ring draws around one thing on the page.

    capturebeat.py <page@2x.png> --url example.com/pricing --dur 7.2 --out clip.mp4
                   [--type 1.25,2.1] [--load 2.2] [--shutter 2.54] [--ring 4.95 --ring-box x0,y0,x1,y1] [--accent '#E0703A']
  times are seconds into the clip — put each on the word it illustrates (T("captures") − the clip's start, from words_out.json)
  --type a,b        the URL types from a to b        --load   the page starts loading
  --shutter         the flash + brackets             --ring   the ring draws around --ring-box (capture pixels: x0,y0,x1,y1)
→ clip.mp4 (1920×1080, 30 fps, silent) + clip.sheet.jpg (a frame a second). Only real pages: never a page made up for the shot."""
import argparse, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

W, H, FPS = 1920, 1080, 30
GROUND = (242, 236, 225); INK = (31, 27, 23)


def outq(u): u = min(1.0, max(0.0, u)); return 1 - (1 - u) ** 3


def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    aie.usage(__doc__)
    ap = argparse.ArgumentParser()
    ap.add_argument("png"); ap.add_argument("--url", required=True); ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--type", default="1.25,2.1"); ap.add_argument("--load", type=float, default=2.2)
    ap.add_argument("--shutter", type=float, default=2.54); ap.add_argument("--ring", type=float); ap.add_argument("--ring-box", dest="ring_box")
    ap.add_argument("--accent", default="#E0703A")
    a = ap.parse_args()
    ACC = hexrgb(a.accent); T_TYPE0, T_TYPE1 = [float(v) for v in a.type.split(",")]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    page = Image.open(a.png).convert("RGB")
    BW, BH = 1500, 900                                              # the browser window on screen at zoom 1
    BAR = 74
    pv = page.resize((BW, int(page.size[1] * BW / page.size[0])), Image.LANCZOS)    # the page at the window's width
    f_url = ImageFont.truetype(aie.ttf("Geist.ttf"), 30); f_url.set_variation_by_axes([500])
    f_ph = ImageFont.truetype(aie.ttf("Geist.ttf"), 30); f_ph.set_variation_by_axes([400])
    sc = BW / page.size[0]
    RB = tuple(float(v) * sc for v in a.ring_box.split(",")) if a.ring_box else None
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    n = int(round(a.dur * FPS)); sheet = []
    for i in range(n):
        t = i / FPS
        win = Image.new("RGB", (BW, BH + BAR), (255, 255, 255)); d = ImageDraw.Draw(win)
        # chrome: the bar, three dots, the address pill
        d.rectangle([0, 0, BW, BAR], fill=(246, 243, 238)); d.line([0, BAR, BW, BAR], fill=(228, 222, 212), width=2)
        for k, c in enumerate([(236, 106, 94), (245, 191, 79), (98, 197, 84)]): d.ellipse([28 + k * 30, BAR / 2 - 9, 46 + k * 30, BAR / 2 + 9], fill=c)
        d.rounded_rectangle([170, 16, BW - 170, BAR - 16], 21, fill=(255, 255, 255), outline=(228, 222, 212), width=2)
        nch = 0 if t < T_TYPE0 else min(len(a.url), int((t - T_TYPE0) / max(0.05, T_TYPE1 - T_TYPE0) * len(a.url)) + 1)
        if nch == 0: d.text((200, BAR / 2), "Search or enter address", font=f_ph, fill=(160, 152, 140), anchor="lm")
        else:
            d.text((200, BAR / 2), a.url[:nch], font=f_url, fill=INK, anchor="lm")
            if t < a.load + 0.1 and int(t / 0.3) % 2 == 0:
                cx = 200 + f_url.getlength(a.url[:nch]) + 3; d.line([cx, BAR / 2 - 17, cx, BAR / 2 + 17], fill=INK, width=3)
        # the page: loads top-down after the URL is in, with a thin accent progress line in the bar
        if t >= a.load:
            u = outq((t - a.load) / 0.45)
            h = int(BH * u)
            if h > 0: win.paste(pv.crop((0, 0, BW, h)), (0, BAR))
            if u < 1: d.line([0, BAR - 2, int(BW * min(1, (t - a.load) / 0.3)), BAR - 2], fill=ACC, width=5)
        # the ring around --ring-box, drawn along its perimeter
        if RB and a.ring is not None:
            ra = outq((t - a.ring) / 0.45)
            if ra > 0:
                x0, y0, x1, y1 = RB[0], RB[1] + BAR, RB[2], RB[3] + BAR
                per = 2 * ((x1 - x0) + (y1 - y0)); upto = per * min(1, ra * 1.1)
                pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]; acc, keep = 0.0, [pts[0]]
                for j in range(4):
                    sl = abs(pts[j + 1][0] - pts[j][0]) + abs(pts[j + 1][1] - pts[j][1])
                    if acc + sl <= upto: keep.append(pts[j + 1]); acc += sl
                    else:
                        f = (upto - acc) / sl; keep.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f)); break
                d.line(keep, fill=ACC, width=8, joint="curve")
        # the window on the ground: rounded, a soft shadow, a slow push (and a little more after the shutter)
        z = 0.94 + 0.04 * t / a.dur + 0.03 * outq((t - a.shutter) / 0.6)
        ww, wh = int(BW * z), int((BH + BAR) * z)
        wim = win.resize((ww, wh), Image.LANCZOS)
        m = Image.new("L", (ww, wh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, ww - 1, wh - 1], int(24 * z), fill=255)
        fr = Image.new("RGB", (W, H), GROUND)
        x, y = (W - ww) // 2, (H - wh) // 2 + 8
        sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle([x + 4, y + 22, x + ww + 4, y + wh + 22], 30, fill=70)
        fr = Image.composite(Image.new("RGB", (W, H), (110, 80, 50)), fr, sh.filter(ImageFilter.GaussianBlur(26)))
        fr.paste(wim, (x, y), m)
        # the shutter: a quick flash and four corner brackets closing on the window
        fa = max(0.0, 1 - (t - a.shutter) / 0.22) if t >= a.shutter else 0.0
        if 0 < fa: fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 0.55 * fa)
        ba = outq((t - a.shutter) / 0.3) * (1 - outq((t - a.shutter - 0.9) / 0.3))
        if ba > 0.01:
            dd = ImageDraw.Draw(fr); pad = int(60 * (1 - outq((t - a.shutter) / 0.3))) + 14; L = 70
            for (cx, cy, sx, sy) in ((x - pad, y - pad, 1, 1), (x + ww + pad, y - pad, -1, 1), (x - pad, y + wh + pad, 1, -1), (x + ww + pad, y + wh + pad, -1, -1)):
                col = tuple(int(GROUND[k] + (ACC[k] - GROUND[k]) * ba) for k in range(3))
                dd.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=7); dd.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=7)
        arr = np.asarray(fr, np.uint8); enc.stdin.write(arr.tobytes())
        if i % FPS == 0: sheet.append(cv2.resize(arr[..., ::-1], (480, 270)))
    enc.stdin.close(); enc.wait()
    grid = np.full((((len(sheet) + 3) // 4) * 270, 1920, 3), 255, np.uint8)
    for j, im in enumerate(sheet): grid[(j // 4) * 270:(j // 4 + 1) * 270, (j % 4) * 480:(j % 4 + 1) * 480] = im
    cv2.imwrite(a.out[:-4] + ".sheet.jpg", grid); print(a.out, f"{a.dur}s")


if __name__ == "__main__":
    main()
