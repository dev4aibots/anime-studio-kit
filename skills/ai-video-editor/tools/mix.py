#!/usr/bin/env python3
"""mix.py — the promo's sound: one music bed cut to the edit + sound effects on their cues, levelled for social.
  mix.py <cues.json> <video.mp4> <out.mp4>
cues.json: {"duration": s, "music": {"file", "start": s, "fade_in": s, "fade_out": s, "gain_db": 0},
            "sfx": [{"file", "at": s, "gain_db": -10, "align": "start"|"peak", "trim": [s0, s1], "fade_out": s}],
            "target_lufs": -14}
"peak" puts the effect's loudest 20 ms on the cue (a whoosh peaks on the cut, not 0.3 s before it). The mix is
measured once and brought to target_lufs with a 4× oversampled limiter at −1.0 dBTP; the picture is stream-copied."""
import json, os, re, subprocess, sys
import numpy as np

SR = 48000


def pcm(path, ss=None, to=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss}"] if ss is not None else []) + ["-i", path] + \
          (["-t", f"{to - (ss or 0)}"] if to is not None else []) + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def peak_offset(path, trim):
    x = pcm(path, *(trim or (None, None)))
    w = int(0.02 * SR)
    if len(x) < w:
        return 0.0
    e = np.convolve(x.astype(np.float64) ** 2, np.ones(w) / w, mode="valid")
    return float(np.argmax(e)) / SR


def lufs(path):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr.split("Summary:")[-1]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", e).group(1))


def main():
    if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip()); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
    cues_path, video, out = sys.argv[1:4]
    base = os.path.dirname(os.path.abspath(cues_path))
    c = json.load(open(cues_path))
    dur = float(c["duration"])
    inputs, chains, labels = [], [], []
    m = c.get("music")
    if m:
        inputs += ["-ss", f"{m.get('start', 0)}", "-t", f"{dur + 0.5}", "-i", os.path.join(base, m["file"])]
        fo = m.get("fade_out", 0.4)
        chains.append(f"[0:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,volume={m.get('gain_db', 0)}dB,"
                      f"afade=t=in:st=0:d={m.get('fade_in', 0.01)},afade=t=out:st={dur - fo:.3f}:d={fo}[m]")
        labels.append("[m]")
    for k, s in enumerate(c.get("sfx", [])):
        f = os.path.join(base, s["file"])
        trim = s.get("trim")
        off = peak_offset(f, trim) if s.get("align") == "peak" else 0.0
        start = max(0.0, s["at"] - off)
        idx = sum(1 for a in inputs if a == "-i")
        inputs += (["-ss", f"{trim[0]}", "-t", f"{trim[1] - trim[0]}"] if trim else []) + ["-i", f]
        ms = int(round(start * 1000))
        fo = s.get("fade_out", 0.05)
        chains.append(f"[{idx}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,volume={s.get('gain_db', -10)}dB,"
                      f"areverse,afade=t=in:st=0:d={fo},areverse,adelay={ms}|{ms}[s{k}]")
        labels.append(f"[s{k}]")
    tmp = out + ".mix.wav"
    graph = ";".join(chains) + f";anullsrc=r={SR}:cl=stereo,atrim=0:{dur:.3f}[bed];[bed]{''.join(labels)}amix=inputs={len(labels) + 1}:normalize=0:duration=first,atrim=0:{dur:.3f}[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", graph, "-map", "[o]", "-c:a", "pcm_f32le", tmp], check=True)
    g = c.get("target_lufs", -14) - lufs(tmp)
    lim = f"volume={g:.2f}dB,aresample={SR * 4},alimiter=limit={10 ** (-1.3 / 20):.4f}:attack=2:release=60:level=0,aresample={SR}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", tmp, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", lim, "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(tmp)
    print(f"→ {out}  ({len(labels)} layers, mix gain {g:+.1f} dB, {lufs(out):.1f} LUFS)")


if __name__ == "__main__":
    main()
