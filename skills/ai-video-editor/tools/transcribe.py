#!/usr/bin/env python3
"""transcribe.py <edit_dir> <take file> — step 1: the raw take becomes words with times.

  edit/take/take.mp4                 a copy of the recording (Downloads folders get cleaned; the edit keeps its own)
  edit/work/audio/take16k.wav        for whisper            take48k.wav  the voice we edit (one decode, 24-bit)
  edit/work/audio/take_medium.json   whisper.cpp with DTW token times (-ojf)
  edit/work/audio/words.json         [{w, t, s, e, p}]  t = the DTW onset (what the cut anchors on), s/e = token span
  edit/work/audio/read.txt           the transcript, one sentence a line, prefixed with its first word's INDEX and time —
                                     what you read to fact-check and to choose what to keep
A take that isn't 1920×1080 at 30 fps (4K, 24/25/60 fps, vertical) is conformed to it once, here. Long-form 16:9 only.

Whisper's word times are good to ~0.1 s and sometimes wrong by up to 1 s, and over a long file it writes a repeated
phrase once. So the cut is made on the WAVEFORM (island_cut.py / cut.py), and checked by re-transcribing the cut."""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__, need=2)
edit, take = os.path.abspath(sys.argv[1]), aie.expand(sys.argv[2])
MODEL = aie.need_model()
DTW = os.path.basename(MODEL)[5:-4] if os.path.basename(MODEL).startswith("ggml-") else "medium.en"   # ggml-medium.en.bin → medium.en
A = f"{edit}/work/audio"; os.makedirs(A, exist_ok=True); os.makedirs(f"{edit}/take", exist_ok=True)
dst = f"{edit}/take/take.mp4"


def video_info(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,avg_frame_rate",
                        "-of", "json", f], capture_output=True, text=True)
    s = (json.loads(r.stdout or "{}").get("streams") or [{}])[0]
    num, _, den = (s.get("avg_frame_rate") or "0/1").partition("/")
    return s.get("width"), s.get("height"), float(num) / float(den or 1) if float(den or 1) else 0.0


if not os.path.exists(dst):
    w, h, fps = video_info(take)
    if (w, h) != (1920, 1080) or abs(fps - 30) > 0.05:
        # every later step works at 1920×1080 and 30 fps (the A-roll is cut by frame count): a 4K, vertical, 24/25/60 fps
        # take is conformed ONCE here (scaled to fit, padded, 30 fps CFR, visually lossless crf 14)
        print(f"conforming the take ({w}×{h} @ {fps:.3f} fps) to 1920×1080 @ 30 fps — once, it takes a while on a long take")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", take, "-map", "0:v:0", "-map", "0:a:0", "-vf",
                        "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", dst], check=True)
    elif take.lower().endswith(".mp4"): shutil.copy2(take, dst)
    elif subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", take, "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", dst]).returncode:
        # a camera .mov with PCM audio can't be stream-copied into MP4: keep the picture, carry the sound as AAC (the voice we
        # edit is decoded from the ORIGINAL below, so nothing is lost where it matters)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", take, "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "320k", dst], check=True)
src = take if os.path.exists(take) else dst
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-map", "0:a:0", "-ac", "1", "-ar", "16000", f"{A}/take16k.wav"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-map", "0:a:0", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", f"{A}/take48k.wav"], check=True)
nice = ["nice", "-n", "10"] if shutil.which("nice") else []
subprocess.run(nice + [aie.whisper_cli(), "-m", MODEL, "-f", f"{A}/take16k.wav", "--dtw", DTW, "-nfa", "-ojf",
                       "-of", f"{A}/take_medium", "-np"], check=True, stdout=subprocess.DEVNULL)

# tokens → words: a token that starts with a space starts a word; punctuation and word pieces join the current one
words = []
for seg in json.load(open(f"{A}/take_medium.json"))["transcription"]:
    for tk in seg.get("tokens", []):
        txt = tk["text"]
        if txt.startswith("[_") or not txt.strip(): continue
        s, e = tk["offsets"]["from"] / 1000, tk["offsets"]["to"] / 1000
        t = tk["t_dtw"] / 100 if tk.get("t_dtw", -1) >= 0 else s
        if txt.startswith(" ") or not words:
            words.append({"w": txt.strip(), "t": t, "s": s, "e": e, "p": tk.get("p", 0)})
        else:
            words[-1]["w"] += txt; words[-1]["e"] = e
json.dump(words, open(f"{A}/words.json", "w"))

lines, cur, first = [], [], 0
for i, w in enumerate(words):
    if not cur: first = i
    cur.append(w["w"])
    if w["w"].endswith((".", "?", "!")) or len(cur) > 30:
        lines.append(f"{first:5d} @{words[first]['t']:7.2f}  {' '.join(cur)}"); cur = []
if cur: lines.append(f"{first:5d} @{words[first]['t']:7.2f}  {' '.join(cur)}")
open(f"{A}/read.txt", "w").write("\n".join(lines) + "\n")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout)
print(f"{len(words)} words · {dur:.1f} s · {len(words) / max(dur, 1e-6) * 60:.0f} wpm overall → {A}/read.txt")
