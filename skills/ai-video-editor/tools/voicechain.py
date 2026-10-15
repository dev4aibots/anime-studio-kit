#!/usr/bin/env python3
"""voicechain.py — the voice, one way, in every video: a static lift and a peak catch, nothing else.

Why so little: a blind test of the same take at equal loudness ranked (best first) "a static gain, nothing else" above
"a compressor + two limiters pushed to −14 LUFS" and above any frequency-domain time-stretch. Most talking-head
recordings sound worse after heavy processing than after a clean lift. So:

  1. the take at its own speed — no speed-up (it opens a gap between the lips and the voice)
  2. NOTHING on the voice: no compressor, gate, expander, EQ / high-pass / low-pass, de-esser, noise reduction, loudnorm,
     speechnorm. One exception: `fanprint()` when a computer fan is audible — a per-bin gain learned from ≥ 20 s of the
     room's own tone (no speech), never deeper than −8 dB (deeper sounded "weird" in the same kind of blind test)
  3. `lift()`: a static gain to −16 LUFS and a look-ahead peak catch (5 ms ahead, 15 ms release, 4× oversampled) that only
     touches the hardest consonant pops. It prints how much it touched
  4. the bed and effects mixed under it; the master is `master_filter()`: a trim of a fraction of a dB and the same short
     catch for the sum. No push to −14, no second slow limiter
  5. ONE lossy encode at the end: ENC_AUDIO (Apple AAC 256k on macOS; ffmpeg's own AAC 256k where aac_at is missing)
If your microphone really needs more (a noisy room, a harsh mic), change it here, once, and listen blind before and after.

    voicechain.py lift  IN OUT [--lufs L]        static lift + the peak catch → a report of what it touched
    voicechain.py fanprint IN OUT --room ROOM [--floor -8]   a fan out, gently (before `lift`; ROOM = room tone, no speech)
    voicechain.py check FILE [--lufs L]          the release file: level (−16 ± 0.7 LUFS), true peak (≤ −1 dBTP), loudness range
    voicechain.py speed IN OUT [--speed 1.0]     only if you decide on a speed change: time domain (ffmpeg atempo), once
    voicechain.py audit                          the skill's tools that touch the voice: none of the banned processing in them
In Python (tools/ on sys.path):  from voicechain import lift, master_filter, ENC_AUDIO, TARGET_LUFS
"""
import argparse, os, re, subprocess, sys
import numpy as np

SR = 48000
TARGET_LUFS = -16.0          # release level of the voice (and of the finished mix)
CEILING_DBTP = -1.5          # the peak catch's ceiling; the encoded file then measures ≤ −1 dBTP
def _has_aac_at():
    try:
        return " aac_at " in subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    except Exception:
        return False


ENC_AUDIO = (["-c:a", "aac_at", "-aac_at_mode", "cvbr", "-b:a", "256k", "-ar", str(SR)] if _has_aac_at()
             else ["-c:a", "aac", "-b:a", "256k", "-ar", str(SR)])


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def measure(path, dual_mono=False):
    """Integrated loudness (LUFS), loudness range (LU) and true peak (dBTP) of a file's first audio stream.
    dual_mono: a mono voice measured the way viewers hear it, the same signal on both speakers (+3 LU over mono)."""
    pre = "pan=stereo|c0=c0|c1=c0," if dual_mono else ""
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", pre + "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr.split("Summary:")[-1]
    get = lambda pat: float(re.search(pat, e).group(1))
    return dict(lufs=get(r"I:\s+(-?[\d.]+) LUFS"), lra=get(r"LRA:\s+(-?[\d.]+) LU"), tp=get(r"Peak:\s+(-?[\d.]+) dBFS"))


def speed(src, out, factor=1.0):
    """The voice faster, pitch kept, in the time domain (ffmpeg atempo, WSOLA). The only stretcher allowed on the voice."""
    af = [] if abs(factor - 1.0) < 1e-6 else ["-af", f"atempo={factor}"]
    _run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:a:0", "-ac", "1"] + af + ["-ar", str(SR), "-c:a", "pcm_f32le", out])
    return out


def _catch(gain_db, ceiling=CEILING_DBTP):
    return (f"volume={gain_db:.3f}dB,aresample={SR * 4},"
            f"alimiter=limit={10 ** (ceiling / 20):.5f}:attack=5:release=15:level=0:latency=1,aresample={SR}")


def _pcm(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def lift(src, out, lufs=TARGET_LUFS, ceiling=CEILING_DBTP, quiet=False):
    """A mono voice: a static gain so it plays at `lufs` on both speakers + the look-ahead peak catch (the catch takes
    a little loudness off, so the gain is trimmed until it lands within 0.2 LU). Returns (and prints) what it touched."""
    m = measure(src, dual_mono=True)
    g = lufs - m["lufs"]
    for _ in range(4):
        _run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:a:0", "-ac", "1", "-af", _catch(g, ceiling), "-c:a", "pcm_f32le", out])
        got = measure(out, dual_mono=True)["lufs"]
        if abs(got - lufs) <= 0.2:
            break
        g += lufs - got
    a, b = _pcm(src) * 10 ** (g / 20), _pcm(out)
    n = min(len(a), len(b)); hop = SR // 100; k = n // hop
    ea = np.sqrt((a[: k * hop].reshape(k, hop) ** 2).mean(1)) + 1e-12
    eb = np.sqrt((b[: k * hop].reshape(k, hop) ** 2).mean(1)) + 1e-12
    gr = (20 * np.log10(ea / eb))[ea > 10 ** ((lufs - 27) / 20)]          # 10 ms windows with speech in them (mono level)
    r = dict(gain=g, src_lufs=m["lufs"], touched_1db=float((gr > 1).mean() * 100), touched_3db=float((gr > 3).mean() * 100),
             max_db=float(gr.max()) if len(gr) else 0.0, out=measure(out, dual_mono=True))
    if not quiet:
        print(f"voice: {m['lufs']:.1f} → {r['out']['lufs']:.1f} LUFS ({g:+.1f} dB) · true peak {r['out']['tp']:.1f} dBTP · "
              f"peak catch touched {r['touched_1db']:.1f}% of speech > 1 dB, {r['touched_3db']:.1f}% > 3 dB (max {r['max_db']:.1f} dB)")
    return r


FANPRINT_FLOOR_DB = -8.0     # the blind pick: −14 dB "sounded weird", −8 dB kept the voice natural. Never lower


def fanprint(src, out, room, floor_db=FANPRINT_FLOOR_DB):
    """A computer fan out of the voice, gently. The print is the fan's power per STFT bin (2048-point Hann, hop 512)
    measured on `room` — at least 20 s of the room's own tone, no speech (a long wait in the take). Each bin of the voice is
    turned down only as far as the fan dominates it (Wiener-style 1 − print/power, print +2 dB), never below floor_db,
    smoothed over frequency (±2 bins) and time (instant up, slow down) so nothing chirps. Bins with speech pass at 1.0.
    Sample-aligned, no latency: picture sync is untouched. Writes 24-bit mono at 48 kHz."""
    if floor_db < FANPRINT_FLOOR_DB:
        raise ValueError(f"fanprint floor {floor_db} dB is deeper than the limit ({FANPRINT_FLOOR_DB} dB)")
    N, H = 2048, 512
    win = np.hanning(N)
    x, r = _pcm(src), _pcm(room)
    if len(r) < 20 * SR:
        raise ValueError("fanprint needs at least 20 s of room tone")

    def stft(y):
        pad = np.concatenate([np.zeros(N), y, np.zeros(N)])
        return np.stack([np.fft.rfft(pad[i * H: i * H + N] * win) for i in range((len(pad) - N) // H + 1)])

    noise = np.mean(np.abs(stft(r)) ** 2, axis=0) * 1.6
    X = stft(x)
    g = np.maximum(np.maximum(1 - noise / np.maximum(np.abs(X) ** 2, 1e-20), 0.0), 10 ** (floor_db / 20))
    k = np.ones(5) / 5
    g = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, g)
    for i in range(1, g.shape[0]):
        g[i] = np.where(g[i] > g[i - 1], g[i], 0.7 * g[i - 1] + 0.3 * g[i])
    S = X * g
    y = np.zeros((S.shape[0] - 1) * H + N); w = np.zeros_like(y)
    for i in range(S.shape[0]):
        y[i * H: i * H + N] += np.fft.irfft(S[i], N) * win; w[i * H: i * H + N] += win ** 2
    y = (y / np.maximum(w, 1e-8))[N: N + len(x)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", out],
                   input=y.tobytes(), check=True)
    return out


def master_filter(current_lufs, target=TARGET_LUFS, ceiling=CEILING_DBTP):
    """The finished mix: a trim (a fraction of a dB once the voice is lifted) + the same short catch for the sum."""
    return _catch(target - current_lufs, ceiling)


def check(path, lufs=TARGET_LUFS):
    """The release file: on level (±0.7 LU), true peak ≤ −1 dBTP. Returns True when it passes."""
    m = measure(path)
    ok = abs(m["lufs"] - lufs) <= 0.7 and m["tp"] <= -1.0
    print(f"{os.path.basename(path)}: {m['lufs']:.1f} LUFS (target {lufs}), true peak {m['tp']:.1f} dBTP, LRA {m['lra']:.1f} LU → "
          + ("OK" if ok else "FAIL"))
    return ok


# The tools that carry the voice, and what must never come back in them (code lines, not comments).
HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_TOOLS = ["assemble.py", "assemble_aroll.py", "aroll_audio.py", "transcribe.py"]   # the chain itself (this file) names the banned filters in prose
BANNED = [r"rubberband", r"acompressor", r"\bcompand", r"loudnorm\s*=", r"loudnorm[,:\]\"']", r"\bagate\b", r"speechnorm",
          r"release=60", r"deesser", r"afftdn", r"(high|low)pass=(f=|\d|frequency)", r"firequalizer",   # the filters, not a `lowpass=None` argument
          r"atempo=1\.[1-9]", r"PTS/1\.[1-9]"]                                    # normal speed: no fixed speed-up


def audit(root=HERE):
    bad = []
    for rel in VOICE_TOOLS:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        for n, line in enumerate(open(path), 1):
            code = line.split("#", 1)[0] if not line.lstrip().startswith(("#", "\"\"\"")) else ""
            for pat in BANNED:
                if re.search(pat, code):
                    bad.append(f"{rel}:{n}: {pat} → {line.strip()[:110]}")
    print("voice tools: " + ("clean" if not bad else f"{len(bad)} banned line(s)"))
    for b in bad:
        print("  " + b)
    return not bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("speed"); s.add_argument("src"); s.add_argument("out"); s.add_argument("--speed", type=float, default=1.0)
    l = sub.add_parser("lift"); l.add_argument("src"); l.add_argument("out"); l.add_argument("--lufs", type=float, default=TARGET_LUFS)
    c = sub.add_parser("check"); c.add_argument("file"); c.add_argument("--lufs", type=float, default=TARGET_LUFS)
    f = sub.add_parser("fanprint"); f.add_argument("src"); f.add_argument("out"); f.add_argument("--room", required=True)
    f.add_argument("--floor", type=float, default=FANPRINT_FLOOR_DB)
    sub.add_parser("audit")
    a = ap.parse_args()
    if a.cmd == "speed":
        speed(a.src, a.out, a.speed); print(f"→ {a.out} (time-domain ×{a.speed})")
    elif a.cmd == "lift":
        lift(a.src, a.out, a.lufs)
    elif a.cmd == "fanprint":
        fanprint(a.src, a.out, a.room, a.floor); print(f"→ {a.out} (fan print, floor {a.floor} dB)")
    elif a.cmd == "audit":
        sys.exit(0 if audit() else 1)
    else:
        sys.exit(0 if check(a.file, a.lufs) else 1)
