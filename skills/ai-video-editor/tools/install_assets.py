#!/usr/bin/env python3
"""install_assets.py — download what this skill may not ship, each from its own source, into AI_EDITOR_HOME/vendor/.
Safe to re-run: what is already there (and checks out) is kept.

  1. fonts for the graphics (woff2, Google Fonts css2 API): Geist, Instrument Serif, Roboto, JetBrains Mono, Fraunces
     → vendor/fonts/ + fonts.css                                                                     (SIL OFL / Apache 2.0)
  2. two font files for the pills and labels drawn with PIL: Geist (variable) and Instrument Serif, from the google/fonts
     repository → vendor/fonts/ttf/ (+ each font's OFL.txt)                                            (SIL OFL 1.1)
  3. the 3D device models (iPhone, MacBook) from the HyperFrames registry, at a pinned commit, checked by sha256
     → vendor/models/                                         (HyperFrames registry block "vfx-iphone-device"; see THIRD-PARTY.md)
Music, sound effects and the whisper model are NOT downloaded here: SETUP-PROMPT.md says where to get them.

    python install_assets.py            everything
    python install_assets.py --check    only report what is missing"""
import hashlib, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

FAMILIES = ["Geist:wght@400;500;600;700;800", "Instrument Serif:ital@0;1", "Roboto:wght@400;500;700;900",
            "JetBrains Mono:wght@400;500;700", "Fraunces:wght@400;700;900"]
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"
TTFS = {"Geist.ttf": f"{GF}/geist/Geist%5Bwght%5D.ttf", "InstrumentSerif.ttf": f"{GF}/instrumentserif/InstrumentSerif-Regular.ttf",
        "Geist-OFL.txt": f"{GF}/geist/OFL.txt", "InstrumentSerif-OFL.txt": f"{GF}/instrumentserif/OFL.txt"}
REG = "https://raw.githubusercontent.com/heygen-com/hyperframes/9734578e6065d6dec8993c4e30a978263c3eaa8b/registry/blocks/vfx-iphone-device/models"
MODELS = {"iphone.glb": (f"{REG}/iphone.glb", "20b926be3ab68ad773af8ef83949561f1f93bc22777688efd89bc38f0840614e"),
          "macbook.glb": (f"{REG}/macbook.glb", "12749c742f3bf67d14650eb831ab6c02104fba59074034c8ed42ce2c5c37c02b")}


def fetch(url, dst):
    tmp = dst + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ai-video-editor-setup"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 16)
            if not b: break
            f.write(b)
    os.replace(tmp, dst)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def main():
    aie.usage(__doc__, need=0)
    check = "--check" in sys.argv
    missing = []
    # 1. woff2 fonts
    css = os.path.join(aie.FONTS, "fonts.css")
    have = open(css).read() if os.path.exists(css) else ""
    lack = [f for f in FAMILIES if f"{f.split(':')[0]}|" not in have]
    if lack and not check:
        import fonts
        fonts.add(lack)
    elif lack: missing.append(f"fonts: {', '.join(f.split(':')[0] for f in lack)}")
    # 2. PIL fonts
    os.makedirs(aie.TTF, exist_ok=True)
    for name, url in TTFS.items():
        dst = os.path.join(aie.TTF, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 1000: continue
        if check: missing.append(f"ttf: {name}"); continue
        fetch(url, dst); print(f"  {name}  ← {url}")
    # 3. device models
    os.makedirs(aie.MODELS3D, exist_ok=True)
    for name, (url, want) in MODELS.items():
        dst = os.path.join(aie.MODELS3D, name)
        if os.path.exists(dst) and sha256(dst) == want: continue
        if check: missing.append(f"model: {name}"); continue
        fetch(url, dst)
        got = sha256(dst)
        if got != want:
            os.remove(dst)
            sys.exit(f"{name}: the download's sha256 is {got}, expected {want} — the registry file changed; nothing kept")
        print(f"  {name}  ← HyperFrames registry (sha256 ok)")
    if check:
        print("assets: " + ("all present" if not missing else "missing → " + "; ".join(missing)))
        sys.exit(1 if missing else 0)
    print(f"assets ready in {aie.VENDOR}")


if __name__ == "__main__":
    main()
