#!/usr/bin/env python3
"""qc.py <edit_dir> [every_s=6] — look at the whole video before anyone else does (after assemble.py).
   → out/qc_sheet_*.png (a frame every N s, labelled with what the plan says is there),
                               out/qc_cuts.png (the frame either side of every graphic switch), and a report:
                               durations (picture = sound), loudness, true peak, and EMPTY-STAGE frames at the switches:
                               black on noir, a blank cream page on Warm Cream (tools/theme.py blank())."""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)
from theme import blank

E = os.path.abspath(sys.argv[1]); OUT = f"{E}/out"; F = f"{OUT}/final.mp4"; FPS = 30
every = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
probe = lambda args: subprocess.run(["ffprobe", "-v", "error"] + args + [F], capture_output=True, text=True).stdout.strip()
vdur = float(probe(["-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0"]))
adur = float(probe(["-select_streams", "a:0", "-show_entries", "stream=duration", "-of", "csv=p=0"]))
plan = []
for line in open(f"{OUT}/plan.txt"):
    m = re.match(r"\s*([\d.]+)\s+([\d.]+)s\s+(.*)", line)
    if m: plan.append((float(m.group(1)), float(m.group(2)), m.group(3).split("  ←")[0].split("  @")[0].strip()))
what = lambda t: next((n for a, d, n in plan if a <= t < a + d), "?")

def frame(t, w=320):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", F, "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB")

# 1. the whole cut, every N seconds
ts = list(np.arange(0.5, vdur - 0.2, every)); cols, rows = 6, 8; per = cols * rows
for s in range(0, len(ts), per):
    chunk = ts[s:s + per]; R = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 322, R * 200), "black"); d = ImageDraw.Draw(sheet)
    for i, t in enumerate(chunk):
        x, y = (i % cols) * 322, (i // cols) * 200
        sheet.paste(frame(t), (x, y + 18)); d.text((x + 3, y + 3), f"{int(t // 60)}:{t % 60:04.1f}  {what(t)[:30]}", fill="yellow")
    sheet.save(f"{OUT}/qc_sheet_{s // per + 1}.png")
# 2. every switch to or from a graphic: the last frame before and the first frame after
sw = [a for a, d, n in plan if not n.startswith("face")] + [a + d for a, d, n in plan if not n.startswith("face")]
sw = sorted(set(round(x, 3) for x in sw if 0 < x < vdur - 0.05))
dark = []
pairs = Image.new("RGB", (8 * 242, ((len(sw) + 3) // 4) * 160), "black"); d = ImageDraw.Draw(pairs)
for k, t in enumerate(sw):
    a, b = frame(max(0, t - 1.5 / FPS), 240), frame(t + 0.5 / FPS, 240)
    for j, im in enumerate((a, b)):
        x, y = ((k % 4) * 2 + j) * 242, (k // 4) * 160
        pairs.paste(im, (x, y + 14))
        if blank(im): dark.append((round(t, 2), "before" if j == 0 else "after"))
    d.text((((k % 4) * 2) * 242 + 3, (k // 4) * 160 + 1), f"{int(t // 60)}:{t % 60:04.1f} > {what(t + 0.02)[:24]}", fill="yellow")
pairs.save(f"{OUT}/qc_cuts.png")
# 3. sound
e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", F, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
LI = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1]
print(f"picture {vdur:.3f}s · sound {adur:.3f}s · Δ {abs(vdur - adur) * 1000:.0f} ms · {LI} LUFS · true peak {TP} dBFS")
print(f"{len(sw)} switches checked · empty-stage frames at a switch (black or blank): {dark or 'none'}")
print("sheets:", " ".join(sorted(f for f in os.listdir(OUT) if f.startswith("qc_"))))
