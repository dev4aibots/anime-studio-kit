#!/usr/bin/env python3
"""assemble_aroll.py <edit_dir> — the cut as one A-roll file: every EDL segment trimmed from the take, audio crossfaded 8 ms at each
splice (no clicks), video hard-cut. One encode. → work/aroll.mp4 (video) + work/aroll.wav (voice, 48 kHz)

The picture is trimmed by FRAME COUNT from the take's real timestamps, the voice by time: one camera ran at
30.0006 fps, so its frames drift across the 1/30 s grid over a long take and a time-based trim gave some segments one frame
too many or too few — 12 segments in the last minute, the picture up to 3 frames (100 ms) behind the voice. Now each segment
starts on the frame nearest its src_in and holds exactly round((src_out − src_in) × 30) frames, so the picture and the voice
end every segment together. Reads work/edl.json (from island_cut.py or cut.py) and take/take.mp4 + work/audio/take48k.wav."""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)
os.chdir(os.path.abspath(sys.argv[1]))                 # usage: assemble_aroll.py <edit_dir>
e = json.load(open("work/edl.json"))
FPS = 30
pts = np.array(sorted(float(x) for x in subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time", "-of", "csv=p=0", "take/take.mp4"],
    capture_output=True, text=True, check=True).stdout.split() if x.strip() not in ("", "N/A")))
# optional holds (work/holds.json {segment: [head_frames, tail_frames]}, written by hand or by a video's own tool): frames in a
# segment's SILENT edges become a clone of the nearest good frame (a glance down at the laptop hidden, the voice untouched,
# the frame count unchanged)
holds = json.load(open("work/holds.json")) if os.path.exists("work/holds.json") else {}
fv, fa, total = [], [], 0
for k, s in enumerate(e):
    a, b = s["src_in"], s["src_out"]
    i0 = int(np.argmin(np.abs(pts - a))); nf = int(round((b - a) * FPS)); total += nf
    h, tl = holds.get(str(k), [0, 0])
    pad = f",tpad=start={h}:stop={tl}:start_mode=clone:stop_mode=clone" if (h or tl) else ""
    fv.append(f"[0:v]trim=start_frame={i0 + h}:end_frame={i0 + nf - tl},setpts=N/({FPS}*TB){pad},setpts=N/({FPS}*TB)[v{k}]")   # frame k at k/30 s
    fa.append(f"[1:a]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.008,areverse,afade=t=in:st=0:d=0.008,areverse[a{k}]")
n = len(e)
graph = ";".join(fv + fa) + ";" + "".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v];" + "".join(f"[a{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[a]"
open("work/aroll_graph.txt", "w").write(graph)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "take/take.mp4", "-i", "work/audio/take48k.wav", "-filter_complex_script", "work/aroll_graph.txt",
                "-map", "[v]", "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-an", "work/aroll.mp4", "-map", "[a]", "-c:a", "pcm_s24le", "work/aroll.wav"], check=True)
got = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                          "-of", "csv=p=0", "work/aroll.mp4"], capture_output=True, text=True).stdout.strip() or 0)
print("ok", n, "segments ·", got, "frames (cut:", total, ")")
assert got == total, f"the A-roll has {got} frames, the cut {total}: picture and voice would drift"
