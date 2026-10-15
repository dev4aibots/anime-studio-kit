#!/usr/bin/env python3
"""sheet.py — a labelled contact sheet of a render at given times (look before you show).
  sheet.py <video> <out.png> <t1> <t2> … [--w 216] [--cols 11]"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip()); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
a = sys.argv[1:]
w = int(a[a.index("--w") + 1]) if "--w" in a else 216
cols = int(a[a.index("--cols") + 1]) if "--cols" in a else 11
a = [x for i, x in enumerate(a) if not (x in ("--w", "--cols") or (i > 0 and a[i - 1] in ("--w", "--cols")))]
video, out, ts = a[0], a[1], a[2:]
ims = []
tmp = tempfile.mkdtemp(prefix="sheet_")
for t in ts:
    p = os.path.join(tmp, f"{t}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", video, "-frames:v", "1", "-vf", f"scale={w}:-2", p], check=True)
    ims.append(Image.open(p).convert("RGB"))
iw, ih = ims[0].size; rows = (len(ims) + cols - 1) // cols
s = Image.new("RGB", (cols * (iw + 4), rows * (ih + 22)), (30, 30, 30)); d = ImageDraw.Draw(s)
for i, (im, t) in enumerate(zip(ims, ts)):
    x, y = (i % cols) * (iw + 4), (i // cols) * (ih + 22); s.paste(im, (x, y + 20)); d.text((x + 4, y + 4), f"{t} s", fill=(255, 220, 0))
s.save(out); print(out, s.size)
