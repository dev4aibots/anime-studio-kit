#!/usr/bin/env python3
"""beats.py — the beat grid of a music track, so cuts land on the beat (numpy only).
  beats.py <audio> [--out beats.json] [--start <s>] [--length <s>] [--anchor <s>]
Prints: tempo (BPM), beat period, the first downbeat, a loudness curve per bar (to pick the strongest section to start
from — a library track often opens on a quiet build that drains a 20 s promo), the DROPS (bar lines where the next two
bars are ≥3 dB louder than the two before — where a promo's reveal should land), and writes beats.json:
  {tempo, period, beats: [s…], downbeats: [s…], bars: [{t, rms_db}], best_start: s, drops: [{t, bar, rise_db}]}
Method: log-spectral flux onset envelope (hop 10 ms) → tempo from the autocorrelation peak in 80–170 BPM (weighted
toward 120) → beat phase that maximises onset energy on the grid → downbeat = the beat phase (of 4) with the most
low-end (kick) energy → PHASE REFINEMENT: a fine (5 ms, window-centred) kick/onset envelope, the nearest onset to every
grid beat within ±70 ms, the median offset applied to the whole grid. Frame times are window CENTRES: stamping a frame
by its start put every beat 46 ms early (on one track the drop hit 40 ms after the grid)."""
import json, subprocess, sys
import numpy as np

SR, HOP, WIN = 22050, 220, 2048


def load(path, start=0.0, length=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start}", "-i", path] + (["-t", f"{length}"] if length else []) + \
          ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)


def stft_mag(x):
    n = 1 + (len(x) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    frames = x[idx] * np.hanning(WIN)[None, :]
    return np.abs(np.fft.rfft(frames, axis=1))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip()); sys.exit(0 if args else 2)
    path = args[0]
    out = args[args.index("--out") + 1] if "--out" in args else None
    start = float(args[args.index("--start") + 1]) if "--start" in args else 0.0
    length = float(args[args.index("--length") + 1]) if "--length" in args else None
    anchor = float(args[args.index("--anchor") + 1]) if "--anchor" in args else None   # this moment is a downbeat
    x = load(path, start, length)
    S = stft_mag(x)
    L = np.log1p(100 * S)
    flux = np.maximum(0, np.diff(L, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(41) / 41, mode="same")          # remove the slow trend
    env = np.maximum(flux, 0)
    env /= env.max() + 1e-9
    fps = SR / HOP
    # tempo
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    lags = np.arange(len(ac))
    bpm = 60 * fps / np.maximum(lags, 1)
    ok = (bpm >= 80) & (bpm <= 170)
    w = np.exp(-0.5 * (np.log2(bpm / 120.0) / 0.9) ** 2)               # a soft prior around 120 BPM
    score = np.where(ok, ac * w, 0)
    lag = int(np.argmax(score))
    # refine the lag to sub-frame precision with a parabola
    if 1 <= lag < len(score) - 1:
        a, b, c = score[lag - 1], score[lag], score[lag + 1]
        lagf = lag + 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    else:
        lagf = float(lag)
    period = lagf / fps
    tempo = 60 / period
    # phase
    best, phase = -1, 0.0
    for ph in np.linspace(0, period, 200, endpoint=False):
        ts = np.arange(ph, len(env) / fps, period)
        v = env[np.clip((ts * fps).round().astype(int), 0, len(env) - 1)].sum()
        if v > best:
            best, phase = v, ph
    phase += WIN / 2 / SR                                              # a frame's time is its window's centre
    beats = np.arange(phase, len(x) / SR, period)
    # refine the phase on a fine, centred onset envelope (kicks first, all onsets as a fallback)
    fh, fw = 110, 1024
    nf = 1 + (len(x) - fw) // fh
    fidx = np.arange(fw)[None, :] + fh * np.arange(nf)[:, None]
    F = np.abs(np.fft.rfft(x[fidx] * np.hanning(fw)[None, :], axis=1))
    ft = (np.arange(1, nf) * fh + fw / 2) / SR
    kick = np.maximum(0, np.diff(np.log1p(100 * F[:, : max(2, int(150 / (SR / fw)))].sum(axis=1))))
    allf = np.maximum(0, np.diff(np.log1p(100 * F), axis=0)).sum(axis=1)
    offs = []
    for env2 in (kick, allf):
        thr = np.percentile(env2, 90)
        for bt in beats:
            m = (ft > bt - 0.07) & (ft < bt + 0.07)
            if m.any():
                k = np.argmax(np.where(m, env2, -1))
                if env2[k] > thr:
                    offs.append(ft[k] - bt)
        if len(offs) >= max(8, len(beats) // 4):
            break
    refine = float(np.median(offs)) if offs else 0.0
    beats = beats + refine
    # downbeat: the beat-in-bar with the most low-end energy
    low = S[:, : int(150 / (SR / WIN))].sum(axis=1)
    # DOWNBEAT. Sections start on a downbeat, and the clearest marker of a section is the kick/bass entering or leaving.
    # Per beat: energy in three bands (low < 150 Hz, mid, high > 2 kHz); novelty = how much the next bar differs from
    # the previous bar, low band weighted most. Each of the 4 phases scores the novelty on its beats; the best wins.
    # (Full-band loudness hid deep-urban's drop — its kick enters +24 dB at 15.235 s but the mix only rises ~4 dB —
    # and a kicks-only test can't tell beat 1 from beat 2 when every beat has a kick. Both failed on real tracks.)
    def band_db(t0, t1):
        seg = x[max(0, int(t0 * SR)): int(t1 * SR)]
        if len(seg) < 256:
            return np.array([-120.0, -120.0, -120.0])
        Fb = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
        fq = np.fft.rfftfreq(len(seg), 1 / SR)
        return np.array([10 * np.log10(Fb[(fq >= lo) & (fq < hi)].sum() + 1e-9) for lo, hi in ((20, 150), (150, 2000), (2000, 11000))])
    E = np.array([band_db(t, t + period) for t in beats])
    W = np.array([1.0, 0.6, 0.4])
    nov, rise = np.zeros(len(beats)), np.zeros(len(beats))
    for j in range(4, len(beats) - 4):
        dlt = E[j:j + 4].mean(axis=0) - E[j - 4:j].mean(axis=0)
        nov[j] = float((np.abs(dlt) * W).sum())                       # a drop IN or a breakdown OUT both mark a bar line
        rise[j] = float((dlt * W).sum())
    # only PEAKS count: the beats next to a change score high too (their windows overlap it), which smeared the phases
    peaks = [j for j in range(5, len(beats) - 5) if nov[j] >= 8.0 and nov[j] >= nov[j - 1] and nov[j] > nov[j + 1]]
    sec = np.array([sum(nov[j] for j in peaks if j % 4 == k) for k in range(4)])
    srt = np.sort(sec)
    if srt[-1] > 6.0 and srt[-1] > 1.25 * srt[-2]:
        d0, downbeat_by = int(np.argmax(sec)), "sections"
    else:
        ci = lambda ts: np.clip((ts * fps - (WIN / 2) / HOP).round().astype(int), 0, len(low) - 1)   # frame CENTRED on t
        d0, downbeat_by = int(np.argmax([low[ci(beats[k::4])].mean() for k in range(4)])), "kicks"
    # the bar phase: an explicit --anchor wins; else the biggest arrangement change (sections nearly always change on
    # a downbeat — but in funk/hip-hop beats 1 and 3 both carry kicks, so the statistics alone can be a beat or two off)
    big = max(peaks, key=lambda j: rise[j]) if peaks and max(rise[j] for j in peaks) >= 12.0 else None
    if anchor is not None:
        d0, downbeat_by = int(np.argmin(np.abs(beats + start - anchor))) % 4, f"anchor {anchor:.3f}s"
    elif big is not None and (big - d0) % 4 != 0:
        d0, downbeat_by = big % 4, f"biggest drop {beats[big] + start:.3f}s"
    downbeats = beats[d0::4]
    # loudness per bar
    bars = []
    for t0 in downbeats:
        seg = x[int(t0 * SR): int((t0 + 4 * period) * SR)]
        if len(seg) < SR * 0.5:
            break
        bars.append({"t": round(float(t0 + start), 3), "rms_db": round(float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)), 1)})
    loud = np.array([b["rms_db"] for b in bars])
    peak = loud.max() if len(loud) else 0
    best_start = next((b["t"] for b in bars if b["rms_db"] >= peak - 3.0), start)
    drops = [{"t": round(float(beats[j] + start), 4), "bar": (j - d0) / 4, "rise_db": round(float(rise[j]), 1),
              "low_db": round(float((E[j:j + 4].mean(axis=0) - E[j - 4:j].mean(axis=0))[0]), 1), "on_downbeat": (j - d0) % 4 == 0}
             for j in peaks if rise[j] >= 6.0]
    drops = sorted(drops, key=lambda d: -d["rise_db"])[:4]
    res = {"file": path, "tempo": round(float(tempo), 2), "period": round(float(period), 5),
           "beats": [round(float(b + start), 4) for b in beats], "downbeats": [round(float(b + start), 4) for b in downbeats],
           "bars": bars, "best_start": best_start, "drops": drops, "confidence": round(float(best / (len(beats) + 1e-9)), 3)}
    if out:
        json.dump(res, open(out, "w"), indent=0)
    curve = " ".join(f"{b['rms_db']:.0f}" for b in bars[:24])
    print(f"{path.split('/')[-1]:40} {tempo:6.1f} BPM  beat {period:.3f}s  first downbeat {downbeats[0] + start:.2f}s  "
          f"strongest from {best_start:.1f}s  conf {res['confidence']}  phase refined {refine * 1000:+.0f} ms ({len(offs)} onsets)"
          f"  downbeat by {downbeat_by} {np.round(sec, 1).tolist()}\n   bars dB: {curve}\n   drops: " +
          (", ".join(f"{d['t']:.3f}s (bar {d['bar']:g}{'' if d['on_downbeat'] else ' OFF-BAR'}, +{d['rise_db']}, low {d['low_db']:+.0f} dB)" for d in drops) or "none"))


if __name__ == "__main__":
    main()
