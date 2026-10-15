#!/usr/bin/env python3
"""aroll_audio.py <edit_dir> — the cut's VOICE only (same trims and 8 ms fades as assemble_aroll.py), in seconds, for checking
splices before the picture is rendered. → work/aroll_check.wav (48 kHz) + work/aroll_check16k.wav (for whisper)
Run after island_cut.py (or cut.py); then words_out.py, cut_diff.py, hear.py."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
aie.usage(__doc__)
os.chdir(os.path.abspath(sys.argv[1]))
e = json.load(open("work/edl.json"))
fa = [f"[0:a]atrim=start={s['src_in']:.4f}:end={s['src_out']:.4f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.008,areverse,afade=t=in:st=0:d=0.008,areverse[a{k}]" for k, s in enumerate(e)]
g = ";".join(fa) + ";" + "".join(f"[a{k}]" for k in range(len(e))) + f"concat=n={len(e)}:v=0:a=1[a]"
open("work/aroll_check_graph.txt", "w").write(g)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/audio/take48k.wav", "-filter_complex_script", "work/aroll_check_graph.txt",
                "-map", "[a]", "-c:a", "pcm_s24le", "work/aroll_check.wav"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/aroll_check.wav", "-ac", "1", "-ar", "16000", "work/aroll_check16k.wav"], check=True)
print("ok", len(e), "segments")
