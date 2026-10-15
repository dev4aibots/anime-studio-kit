#!/usr/bin/env python3
"""new.py — scaffold a promo: capture the brand, beat-map the music, write a HyperFrames project that renders.
  new.py <dir> [--url URL] [--aspect 9:16|16:9] [--music FILE] [--drop S] [--drop-bar 1] [--bars 8] [--name NAME]
→ <dir>/capture/   brand.json + real screenshots (tools/capture.py)            — only with --url
  <dir>/promo/     index.tpl (the starter, filled with the brand's colours, font, name, line and the beat grid),
                   audio/<track> + audio/beats.json + audio/cues.json (music only, so the first render already has sound),
                   assets/, renders/, hyperframes.json — then linked (engine, kit, fonts) and ready for tools/render.sh
The drop: --drop S (a time in the track) or the biggest drop beats.py measured; the music starts --drop-bar bars
before it, so the drop is bar N of the promo. Without --music the grid is 120 BPM and the promo is silent."""
import argparse, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import aie
PY = aie.python()


def run(*cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd[:3]), "…" if len(cmd) > 3 else "")
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def first_family(stack):
    return (stack or "").split(",")[0].strip().strip("'\"") or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir"); ap.add_argument("--url"); ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--music"); ap.add_argument("--drop", type=float); ap.add_argument("--drop-bar", type=int, default=1)
    ap.add_argument("--bars", type=int, default=8); ap.add_argument("--name"); ap.add_argument("--force", action="store_true")
    aie.usage(__doc__)
    a = ap.parse_args()
    root = os.path.abspath(a.dir); promo = os.path.join(root, "promo")
    if os.path.exists(os.path.join(promo, "index.tpl")) and not a.force:      # never overwrite a promo someone built
        sys.exit(f"{promo}/index.tpl already exists — pick a new folder (e.g. {a.dir}-2) or pass --force")
    W, H = (1080, 1920) if a.aspect == "9:16" else (1920, 1080) if a.aspect == "16:9" else (1080, 1080)
    for sub in ("assets/brand", "audio", "renders"):
        os.makedirs(os.path.join(promo, sub), exist_ok=True)

    # 1. the brand, from the live page
    brand = {}
    if a.url:
        cap = os.path.join(root, "capture")
        run(PY, os.path.join(HERE, "capture.py"), a.url, cap)
        brand = json.load(open(os.path.join(cap, "brand.json")))
    cols = brand.get("colors") or {}
    lum = lambda h: sum(w * int(h[i:i + 2], 16) for w, i in ((0.2126, 1), (0.7152, 3), (0.0722, 5))) / 255
    bg = (cols.get("background") or [{"hex": "#f8f7f5"}])[0]["hex"]
    texts = cols.get("text") or [{"hex": "#1a1a1a", "weight": 1}]
    top = [c for c in texts if c.get("weight", 1) >= 0.1 * texts[0].get("weight", 1)][:4]
    # headline ink = the strongest-contrast of the page's main text colours (the body grey is not the ink)
    ink = (min if lum(bg) > 0.5 else max)(top, key=lambda c: lum(c["hex"]))["hex"]
    title = brand.get("name") or re.split(r"\s+[—|·–-]\s+", brand.get("title") or "")[0]
    name = a.name or title or "Your product"
    line = re.split(r"(?<=[.!?])\s", (brand.get("description") or "").strip())[0][:70] or "One line from the page."
    family = first_family((brand.get("fonts") or {}).get("heading")) or first_family((brand.get("fonts") or {}).get("body")) or "Inter"
    try:   # vendor the brand's own typeface when Google Fonts has it; otherwise Inter
        run(PY, os.path.join(HERE, "fonts.py"), "add", f"{family}:wght@400;500;700;800;900")
    except subprocess.CalledProcessError:
        family = "Inter"; run(PY, os.path.join(HERE, "fonts.py"), "add", "Inter:wght@400;500;700;800;900")

    # 2. the music and its grid
    beat, mstart, mname, bpm = 0.5, 0.0, "none", 120.0
    if a.music:
        mname = os.path.basename(a.music)
        shutil.copy2(a.music, os.path.join(promo, "audio", mname))
        bj = os.path.join(promo, "audio", "beats.json")
        args = [PY, os.path.join(HERE, "beats.py"), a.music, "--out", bj] + (["--anchor", str(a.drop)] if a.drop else [])
        run(*args)
        bt = json.load(open(bj)); beat, bpm = bt["period"], bt["tempo"]
        drop = a.drop if a.drop else (bt["drops"][0]["t"] if bt.get("drops") else bt["best_start"])
        drop = min(bt["beats"], key=lambda t: abs(t - drop))                    # snap to the measured grid
        mstart = round(max(0.0, drop - a.drop_bar * 4 * beat), 4)
    dur = round(a.bars * 4 * beat, 3)
    if a.music:
        json.dump({"duration": dur, "target_lufs": -14, "music": {"file": mname, "start": mstart, "fade_in": 0.01, "fade_out": 1.0, "gain_db": 0},
                   "sfx": []}, open(os.path.join(promo, "audio", "cues.json"), "w"), indent=1)

    # 3. the project
    tpl = open(os.path.join(SKILL, "engine", "starter.tpl")).read()
    subs = {"W": W, "H": H, "BG": bg, "INK": ink, "FONT": f"'{family}', sans-serif", "NAME": name, "LINE": line,
            "DUR": dur, "BEAT": beat, "BPM": round(bpm, 2), "MUSIC": mname, "MSTART": mstart, "DROPBAR": a.drop_bar}
    for k, v in subs.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    open(os.path.join(promo, "index.tpl"), "w").write(tpl)
    json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
               "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
               "media": {"autoProxy": True}}, open(os.path.join(promo, "hyperframes.json"), "w"), indent=2)
    json.dump({"id": "promo", "name": os.path.basename(root)}, open(os.path.join(promo, "meta.json"), "w"), indent=2)
    json.dump({"name": "promo", "private": True, "type": "module"}, open(os.path.join(promo, "package.json"), "w"), indent=2)
    run(PY, os.path.join(HERE, "link.py"), promo)
    print(f"\n{promo}\n  {W}×{H} · {dur}s ({a.bars} bars) · {bpm:.1f} BPM · music {mname} from {mstart}s, drop = bar {a.drop_bar}"
          f"\n  brand: {name} · bg {bg} · ink {ink} · font {family}"
          f"\n  next: storyboard it by bars (engine/ENGINE.md, \"Promos\"), write the shots in index.tpl, then tools/render.sh {promo}")


if __name__ == "__main__":
    main()
