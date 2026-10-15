#!/usr/bin/env python3
"""doctor.py — is everything this skill needs installed? One line per requirement, ✓ / ✗ (must fix) / · (optional).

    python doctor.py          the report; exits 1 if a required piece is missing"""
import json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

rows, bad = [], 0


def row(ok, what, detail="", optional=False):
    global bad
    mark = "✓" if ok else ("·" if optional else "✗")
    if not ok and not optional: bad += 1
    rows.append(f"  {mark} {what:30s} {detail}")


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode, (r.stdout + r.stderr)
    except Exception as e:
        return 1, str(e)


def main():
    aie.usage(__doc__, need=0)
    # ffmpeg
    ff = shutil.which("ffmpeg")
    if ff:
        _, v = run(["ffmpeg", "-hide_banner", "-version"]); _, enc = run(["ffmpeg", "-hide_banner", "-encoders"])
        ver = re.search(r"ffmpeg version (\S+)", v)
        row(True, "ffmpeg", ver.group(1) if ver else ff)
        row(" libx264 " in enc, "ffmpeg: libx264 encoder", "H.264 for every piece")
        row(" prores_ks " in enc, "ffmpeg: prores_ks encoder", "transparent stickers (ProRes 4444)")
        row(" aac_at " in enc, "ffmpeg: aac_at (Apple AAC)", "else the built-in aac encoder is used", optional=True)
    else:
        row(False, "ffmpeg", "not on PATH")
    row(bool(shutil.which("ffprobe")), "ffprobe")
    # python
    py = aie.python()
    c, out = run([py, "-c", "import numpy, PIL, cv2; print(numpy.__version__, PIL.__version__, cv2.__version__)"])
    row(c == 0, "python: numpy, pillow, opencv", f"{py} → {out.strip().splitlines()[-1] if out.strip() else ''}")
    # node + npm packages
    c, out = run(["node", "--version"])
    m = re.match(r"v(\d+)", out.strip()) if c == 0 else None
    row(bool(m) and int(m.group(1)) >= 22, "node ≥ 22", out.strip() if c == 0 else "not on PATH (HyperFrames 0.8.137 needs 22+)")
    for pkg, want in (("hyperframes", aie.HYPERFRAMES_VERSION), ("gsap", "3.14.2"), ("three", "0.181.2")):
        pj = os.path.join(aie.NODE, pkg, "package.json")
        got = json.load(open(pj)).get("version") if os.path.exists(pj) else None
        row(got == want, f"npm: {pkg}@{want}", got and f"found {got} in {aie.NODE}" or f"missing in {aie.NODE}")
    # whisper
    wc = shutil.which(aie.whisper_cli())
    if wc:
        _, h = run([wc, "--help"])
        row("--dtw" in h, "whisper.cpp (whisper-cli)", wc + ("" if "--dtw" in h else "  (no --dtw: update whisper.cpp)"))
    else:
        row(False, "whisper.cpp (whisper-cli)", "not on PATH")
    ok = os.path.exists(aie.WHISPER_MODEL) and os.path.getsize(aie.WHISPER_MODEL) > 10 ** 8
    row(ok, "whisper model", f"{aie.WHISPER_MODEL}" + (f" ({os.path.getsize(aie.WHISPER_MODEL) / 1e9:.2f} GB)" if os.path.exists(aie.WHISPER_MODEL) else " (missing)"))
    # downloaded assets
    css = os.path.join(aie.FONTS, "fonts.css")
    have = open(css).read() if os.path.exists(css) else ""
    row(all(f"{f}|" in have for f in ("Geist", "Instrument Serif", "Roboto")), "fonts (woff2)", aie.FONTS)
    row(all(os.path.exists(os.path.join(aie.TTF, f)) for f in ("Geist.ttf", "InstrumentSerif.ttf")), "fonts (ttf for PIL)", aie.TTF)
    row(all(os.path.exists(os.path.join(aie.MODELS3D, f)) for f in ("iphone.glb", "macbook.glb")), "3D device models", aie.MODELS3D)
    # optional
    row(aie.MAC and bool(shutil.which("swiftc")), "on-screen text (OCR)", "macOS + swiftc (Xcode Command Line Tools)" if aie.MAC
        else "macOS only: hand-set zoom boxes work everywhere", optional=True)
    c, _ = run([py, "-c", "import playwright"])
    row(c == 0, "page captures (playwright)", "pip install playwright && python -m playwright install chromium", optional=True)
    music = [f for f in os.listdir(aie.MUSIC)] if os.path.isdir(aie.MUSIC) else []
    row(bool(music), "music beds", f"{len(music)} file(s) in {aie.MUSIC}", optional=True)
    kinds = [k for k in ("whoosh", "pop", "shutter", "riser") if os.path.isdir(os.path.join(aie.SFX, k)) and os.listdir(os.path.join(aie.SFX, k))]
    row(len(kinds) == 4, "sound effects", f"{', '.join(kinds) or 'none'} in {aie.SFX}", optional=True)
    print(f"AI_EDITOR_HOME = {aie.HOME}\n" + "\n".join(rows))
    print("ready." if not bad else f"{bad} required piece(s) missing — fix the ✗ lines (SETUP-PROMPT.md).")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
