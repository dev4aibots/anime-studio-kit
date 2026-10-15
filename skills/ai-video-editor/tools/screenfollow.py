#!/usr/bin/env python3
"""screenfollow.py — a screen recording as a graphic whose camera follows the speaker's words: when they say something
that is written on the screen, the view eases in on it and a ring draws around it; when they move on, it eases out.
The look is Warm Cream: the screen sits as a window on the cream ground, the ring in the accent. Reading the screen uses
Apple's on-device text recognition (macOS); elsewhere only hand-set zooms (--zoom) are made.

    screenfollow.py <screen.mp4> <words.json> --from S --to S --out clip.mp4 [--crop x,y,w,h] [--script script.txt]
                    [--ring '#E0703A'] [--ground '#F2ECE1'] [--max-zoom 2.4] [--zoom t0,t1,x,y,w,h …] [--plan-only]

  screen.mp4   the screen track at NORMAL speed, on the same clock as words.json (record camera and screen together, e.g. as
               two tracks of one recording, so they share a clock)
  words.json   the words with times: work/audio/words.json [{w, t, e}], or [{text, startTimeMs, endTimeMs}], or [{w, t}]
  --crop       the app's region in the recording (leave out the Dock, the menu bar, a second window)
  --script     your script: any stretch where the screen shows it (a teleprompter) is REFUSED, never rendered
  --zoom       a zoom set by hand (repeatable): from t0 to t1 (the recording's clock), on the box x,y,w,h in the CROPPED frame's pixels,
               filling ~90 % of the frame — for what OCR can't anchor ("these little dots right here", a chart, a bar
               being hovered). It replaces any automatic zoom it overlaps. Set its end before the screen under it changes.

What it guards:
  - a teleprompter or the desktop never reaches the clip (--script: a frame whose text is mostly the script stops the run)
  - a ring never stays on something that changed: when the region under it changes (a scroll, the next slide),
    the zoom ends there
  - a zoom never lands on a guess: it needs two of the spoken content words, or one distinctive token (a number, a name), in
    the same on-screen line, at that moment
→ clip.mp4 (1920×1080, 30 fps, the span's own length) + clip.plan.json (every zoom: when, the words said, what it matched)
  + clip.sheet.jpg (a frame from each zoom)"""
import argparse, json, os, re, subprocess, sys, tempfile
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, ANIM = 1920, 1080, 30, 0.6
STOP = set("""a an and are as at be but by can could did do does for from had has have he her his how i if in into is it its
just let like me more my no not now of on or our out over so some than that the their them then there these they this
those to up us very was we were what when where which who why will with would you your yeah okay ok gonna going get got
right here see look go one two three really actually basically also all any""".split())


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def words_of(path):
    raw = json.load(open(path))
    if isinstance(raw, dict):
        raw = raw.get("words") or raw.get("details", {}).get("clips", [{}])[0].get("words", [])
    out = []
    for x in raw:
        w = x.get("w") or x.get("word") or x.get("text") or ""
        t = x["t"] if "t" in x else (x["start"] if "start" in x else x.get("startTimeMs", 0) / 1000)
        e = x["e"] if "e" in x else (x["end"] if "end" in x else (x["endTimeMs"] / 1000 if "endTimeMs" in x else None))
        if t is not None and w.strip():
            out.append(dict(w=w.strip(), t=float(t), e=float(e) if e is not None else None))
    for i, x in enumerate(out):
        if x["e"] is None:
            x["e"] = out[i + 1]["t"] if i + 1 < len(out) else x["t"] + 0.3
    return out


def toks(s):
    return [t for t in re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", s.lower())]


def content(tokens):
    return [t for t in tokens if t not in STOP and (len(t) >= 3 or t.isdigit())]


def distinctive(t):
    return bool(re.fullmatch(r"\d+(?:[.,]\d+)?", t)) or len(t) >= 7


def ocr_samples(screen, t0, t1, crop, step=0.5):
    """OCR every `step` s: [{t, lines:[{text,x,y,w,h,conf}], thumb}] in the CROPPED frame's pixels."""
    OCR = aie.ocr_bin()
    if not OCR:
        print("no on-screen text recognition here (macOS + swiftc only): automatic zooms off, --zoom boxes still work")
    tmp = tempfile.mkdtemp(prefix="sf_")
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "") + f"fps={1 / step}"
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", screen, "-vf", vf, f"{tmp}/%05d.png"], check=True)
    files = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
    p = subprocess.Popen([OCR, "--serve"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) if OCR else None
    out = []
    for i, f in enumerate(files):
        r = {}
        if p:
            p.stdin.write(os.path.join(tmp, f) + "\n"); p.stdin.flush()
            r = json.loads(p.stdout.readline())
        img = cv2.imread(os.path.join(tmp, f), cv2.IMREAD_GRAYSCALE)
        out.append(dict(t=t0 + i * step, lines=r.get("lines", []), img=img))
    if p: p.stdin.close(); p.wait()
    for f in files:
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return out


def script_check(samples, script_path):
    """Times where the screen shows the script (a teleprompter): mostly the script's words, and a lot of them."""
    vocab = set(content(toks(open(script_path).read())))
    bad = []
    for s in samples:
        ws = content(toks(" ".join(l["text"] for l in s["lines"])))
        if len(ws) >= 25 and sum(w in vocab for w in ws) / len(ws) >= 0.5:
            bad.append(s["t"])
    return bad


def phrases(words, t0, t1):
    """The spoken words in the span, grouped at pauses (> 0.35 s) and sentence ends, at most 8 words."""
    ps, cur = [], []
    for i, x in enumerate(words):
        if x["t"] < t0 or x["t"] >= t1:
            continue
        if cur and (x["t"] - cur[-1]["e"] > 0.35 or len(cur) >= 8 or cur[-1]["w"].endswith((".", "?", "!"))):
            ps.append(cur); cur = []
        cur.append(x)
    if cur:
        ps.append(cur)
    return [dict(t=p[0]["t"], e=p[-1]["e"], text=" ".join(x["w"] for x in p)) for p in ps]


def match(ph, sample, near=()):
    """The on-screen line being talked about, or None. It needs two shared content words or one distinctive token; numbers
    count as often as they are said, a number on the line that was NOT said counts against it, and a tie between two different
    lines is no zoom at all (never a guess)."""
    from collections import Counter
    said = content(toks(ph["text"])); sc = Counter(said)
    scored = []
    for l in sample["lines"]:
        if l.get("conf", 1) < 0.3:
            continue
        lc = Counter(content(toks(l["text"])))
        shared = [t for t in sc if t in lc]
        if not (len(shared) >= 2 or any(distinctive(t) for t in shared)):
            continue
        digits_said = sum(min(sc[t], lc[t]) for t in shared if t[0].isdigit())
        digits_not = sum(n for t, n in lc.items() if t[0].isdigit() and t not in sc and t not in near)   # "49/50": "out of 50" is said next
        bare = 1.5 if len(lc) == 1 and next(iter(lc))[0].isdigit() and len(sc) > 1 else 0                 # a lone number: a list index?
        score = len(shared) + sum(1 for t in shared if distinctive(t)) + digits_said - digits_not - bare + 0.002 * l["h"]
        scored.append((score, l, shared))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    if len(scored) > 1 and scored[1][0] > scored[0][0] - 0.5 and scored[1][1]["text"] != scored[0][1]["text"]:
        return None                                                # two lines fit as well: ambiguous
    _, l, shared = scored[0]
    return dict(box=[l["x"], l["y"], l["w"], l["h"]], text=l["text"], shared=shared)


def plan(samples, phs, t0, t1, step=0.5, change=14.0):
    at = lambda t: samples[min(len(samples) - 1, max(0, int(round((t - t0) / step))))]
    ev = []
    for ph in phs:
        near = {t for q in phs if q["t"] < ph["e"] + 4 and q["e"] > ph["t"] - 4 for t in toks(q["text"]) if t[0].isdigit()}
        m = match(ph, at(ph["t"] + 0.3), near)
        if not m:
            continue
        x, y, w, h = m["box"]; pad = max(10, h * 0.35)
        box = [x - pad, y - pad * 0.8, w + 2 * pad, h + 1.6 * pad]
        start, end = max(t0, ph["t"] - 0.15), min(t1, ph["e"] + 1.2)
        # the stale guard: the region under the ring must not change while it is up
        s0 = at(start)["img"]; X0, Y0 = max(0, int(box[0])), max(0, int(box[1])); X1, Y1 = int(box[0] + box[2]), int(box[1] + box[3])
        ref = s0[Y0:Y1, X0:X1].astype(np.float32)
        t = start + step
        while t < end and ref.size:
            cur = at(t)["img"][Y0:Y1, X0:X1].astype(np.float32)
            if cur.shape != ref.shape or np.abs(cur - ref).mean() > change:
                end = t - 0.1; break
            t += step
        if end - start < 0.8:
            continue
        if ev and start < ev[-1]["end"]:                      # one at a time: the earlier one hands over
            if abs(ev[-1]["box"][1] - box[1]) < 4 and abs(ev[-1]["box"][0] - box[0]) < 4:
                ev[-1]["end"] = max(ev[-1]["end"], end); continue
            ev[-1]["end"] = start
        ev.append(dict(start=round(start, 3), end=round(end, 3), box=[round(v, 1) for v in box], said=ph["text"], screen=m["text"], shared=m["shared"]))
    return [e for e in ev if e["end"] - e["start"] >= 0.8]


def ease(u):
    u = min(1.0, max(0.0, u)); return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def render(a, ev, src_wh):
    sw, sh = src_wh
    ground, ring = hexrgb(a.ground), hexrgb(a.ring)
    k = min(W * 0.88 / sw, H * 0.86 / sh)                    # the window on the ground, with a margin all round
    ww, wh = int(sw * k), int(sh * k); wx, wy = (W - ww) // 2, (H - wh) // 2
    base_bg = np.full((H, W, 3), ground[::-1], np.uint8)
    mask = np.zeros((wh, ww), np.uint8); cv2.rectangle(mask, (0, 0), (ww - 1, wh - 1), 255, -1)
    r = 22; mask[:r, :r] = 0; mask[:r, -r:] = 0; mask[-r:, :r] = 0; mask[-r:, -r:] = 0
    for cx, cy in ((r, r), (ww - r - 1, r), (r, wh - r - 1), (ww - r - 1, wh - r - 1)):
        cv2.circle(mask, (cx, cy), r, 255, -1)
    shadow = np.zeros((H, W), np.float32); shadow[wy + 14: wy + wh + 10, wx: wx + ww] = 1
    shadow = cv2.GaussianBlur(shadow, (0, 0), 24) * 0.16
    base_bg = (base_bg.astype(np.float32) * (1 - shadow[..., None])).astype(np.uint8)
    m3 = (mask.astype(np.float32) / 255)[..., None]

    def target(t):
        for e in ev:
            if e["start"] <= t < e["end"]:
                x, y, w, h = e["box"]
                bx, by, bw, bh = wx + x * k, wy + y * k, w * k, h * k
                f = e.get("fill", 0.5)                           # a line fills half the frame, a hand-set box ~90 %
                s = min(a.max_zoom, max(1.0, min(W * f / max(bw, 1), H * f / max(bh, 1))))
                return (bx + bw / 2, by + bh / 2, s, (bx, by, bw, bh), e)
        return (W / 2, H / 2, 1.0, None, None)

    # the camera: eased between targets, ANIM seconds per move
    n = int(round((a.to - a.frm) * FPS)); keys, prev = [], None
    for i in range(n):
        tg = target(a.frm + i / FPS)
        if prev is None or tg[4] is not prev[4]:
            keys.append((i, tg))
        prev = tg
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a.frm}", "-t", f"{a.to - a.frm}", "-i", a.screen, "-vf",
                            (f"crop={a.crop[2]}:{a.crop[3]}:{a.crop[0]}:{a.crop[1]}," if a.crop else "") + f"fps={FPS},scale={ww}:{wh}:flags=lanczos",
                            "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                            "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    cur = (W / 2, H / 2, 1.0); frm_from, ki, last = cur, 0, None
    for i in range(n):
        raw = dec.stdout.read(ww * wh * 3)
        if len(raw) < ww * wh * 3:
            raw = last if last is not None else np.zeros(ww * wh * 3, np.uint8).tobytes()
        last = raw
        win = np.frombuffer(raw, np.uint8).reshape(wh, ww, 3)
        base = base_bg.copy()
        roi = base[wy:wy + wh, wx:wx + ww].astype(np.float32)
        base[wy:wy + wh, wx:wx + ww] = (roi * (1 - m3) + win.astype(np.float32) * m3).astype(np.uint8)
        while ki + 1 < len(keys) and keys[ki + 1][0] <= i:
            ki += 1; frm_from = cur
        k0, tg = keys[ki]
        u = ease((i - k0) / FPS / ANIM)
        cur = tuple(frm_from[j] + (tg[j] - frm_from[j]) * u for j in range(3))
        cx, cy, s = cur
        ox, oy = min(max(cx - W / (2 * s), 0), W - W / s), min(max(cy - H / (2 * s), 0), H - H / s)
        M = np.float32([[s, 0, -ox * s], [0, s, -oy * s]])
        out = cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        if tg[3] is not None:                                  # the ring draws once the move has landed
            age = (i - k0) / FPS; ra = min(1.0, max(0.0, (age - ANIM * 0.7) / 0.25))
            e = tg[4]; t = a.frm + i / FPS
            ra *= min(1.0, max(0.0, (e["end"] - t) / 0.2))
            if ra > 0.01:
                bx, by, bw, bh = tg[3]
                X0, Y0 = int((bx - ox) * s), int((by - oy) * s); X1, Y1 = int((bx + bw - ox) * s), int((by + bh - oy) * s)
                ov = out.copy(); rr = int(min(18, (Y1 - Y0) / 2))
                th = 5
                cv2.rectangle(ov, (X0 + rr, Y0), (X1 - rr, Y0 + th), ring[::-1], -1); cv2.rectangle(ov, (X0 + rr, Y1 - th), (X1 - rr, Y1), ring[::-1], -1)
                cv2.rectangle(ov, (X0, Y0 + rr), (X0 + th, Y1 - rr), ring[::-1], -1); cv2.rectangle(ov, (X1 - th, Y0 + rr), (X1, Y1 - rr), ring[::-1], -1)
                for (ccx, ccy, a0) in ((X0 + rr, Y0 + rr, 180), (X1 - rr, Y0 + rr, 270), (X1 - rr, Y1 - rr, 0), (X0 + rr, Y1 - rr, 90)):
                    cv2.ellipse(ov, (ccx, ccy), (rr, rr), 0, a0, a0 + 90, ring[::-1], th, cv2.LINE_AA)
                out = cv2.addWeighted(ov, ra, out, 1 - ra, 0)
        enc.stdin.write(out.tobytes())
    enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.kill()


def main():
    aie.usage(__doc__)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("screen"); ap.add_argument("words"); ap.add_argument("--from", dest="frm", type=float, required=True)
    ap.add_argument("--to", type=float, required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--crop"); ap.add_argument("--script"); ap.add_argument("--ring", default="#E0703A")
    ap.add_argument("--ground", default="#F2ECE1"); ap.add_argument("--max-zoom", dest="max_zoom", type=float, default=2.4)
    ap.add_argument("--zoom", action="append", default=[])
    ap.add_argument("--plan-only", action="store_true")
    a = ap.parse_args()
    a.crop = [int(v) for v in a.crop.split(",")] if a.crop else None
    samples = ocr_samples(a.screen, a.frm, a.to, a.crop)
    if a.script:
        bad = script_check(samples, a.script)
        if bad:
            sys.exit(f"REFUSED: the script is on the screen at {', '.join(f'{t:.1f}s' for t in bad[:12])}"
                     f"{' …' if len(bad) > 12 else ''} — pick another span, or crop it out (--crop)")
    phs = phrases(words_of(a.words), a.frm, a.to)
    ev = plan(samples, phs, a.frm, a.to)
    for z in a.zoom:                                             # zooms set by hand win over the automatic ones they overlap
        t0, t1, x, y, w, h = [float(v) for v in z.split(",")]
        ev = [e for e in ev if e["end"] <= t0 or e["start"] >= t1]
        ev.append(dict(start=t0, end=t1, box=[x, y, w, h], said="(set by hand)", screen=f"box {x:.0f},{y:.0f},{w:.0f},{h:.0f}",
                       shared=[], fill=0.9))
    ev.sort(key=lambda e: e["start"])
    json.dump(dict(screen=a.screen, span=[a.frm, a.to], crop=a.crop, zooms=ev), open(os.path.splitext(a.out)[0] + ".plan.json", "w"), indent=1)
    print(f"{len(phs)} phrases · {len(ev)} zooms")
    for e in ev:
        print(f"  {e['start']:8.2f}–{e['end']:8.2f}  said {e['said'][:46]!r:50} → on screen {e['screen'][:46]!r}")
    if a.plan_only:
        return
    h0, w0 = samples[0]["img"].shape
    render(a, ev, (w0, h0))
    # a frame from each zoom, to look at before it goes in
    times = [((e["start"] + e["end"]) / 2 - a.frm) for e in ev][:12] or [(a.to - a.frm) / 2]
    sheet = os.path.splitext(a.out)[0] + ".sheet.jpg"; tiles = []
    for t in times:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", a.out, "-frames:v", "1", "-vf", "scale=480:-1", "-f", "image2pipe",
                            "-vcodec", "png", "-"], capture_output=True)
        tiles.append(cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR))
    rows = [np.hstack(tiles[i:i + 4] + [np.zeros_like(tiles[0])] * (4 - len(tiles[i:i + 4]))) for i in range(0, len(tiles), 4)]
    cv2.imwrite(sheet, np.vstack(rows))
    print(f"→ {a.out} · {a.out.rsplit('.', 1)[0]}.plan.json · {sheet}")


if __name__ == "__main__":
    main()
