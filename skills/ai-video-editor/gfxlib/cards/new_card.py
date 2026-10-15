#!/usr/bin/env python3
"""new_card.py — a card graphic from one of the templates here, ready to render with tools/render.sh.

    new_card.py <kind> <out_dir> --cfg cfg.json [--dur 4.2] [--theme warmcream|noir] [--accent "#E0703A"]
kinds and their CFG (times t = seconds INTO this card: the spoken word's time in words_out.json − the card's start):
  words   {"lines": [{"text": "Your exact words", "t": 0.3, "size": 120, "small": false, "accent": "exact"}], "ul": 0}
          kinetic lines that land on the words; "accent" = the part in the accent colour; "ul" = the line that gets the underline
  vs      {"head": {"text": "…", "accent": "…", "t": 0.2} | null, "left": {"tag": "A", "tagW": 420, "lines": [{"text": "…", "t": 0.5}]},
           "right": {…}, "win": "left"|"right"|"tie"|null, "t_win": 2.0}
  grid    {"title": {"text": "…", "accent": null, "t": 0.2}, "tiles": [{"n": "", "label": "…", "t": 0.8}, …]}
  detail  {"items": [{"img": "path/to/image.png", "tag": "…", "t": 0.4}, …]}       1–3 real images, laid out for you
  pair    {"left": {"img": "path/a.jpg", "tag": "…"}, "right": {"img": "path/b.jpg", "tag": "…"}}
"dur" may also sit in the CFG. Every word on a card must be the speaker's own (STYLE.md "Content"). Examples: cards/examples/.
→ <out_dir>/ index.tpl, assets/gfx.js (a fresh copy), assets/<images>, renders/, hyperframes.json, package.json, meta.json
then:  bash <skill>/tools/render.sh <out_dir> <name> --fonts "Geist,Instrument Serif\""""
import argparse, json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
GFXLIB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(GFXLIB, "..", "tools"))
import aie

KINDS = {"words": "card_words.tpl", "vs": "card_vs.tpl", "grid": "card_grid.tpl", "detail": "detail.tpl", "pair": "pair.tpl"}


def scaffold(out):
    os.makedirs(os.path.join(out, "assets"), exist_ok=True); os.makedirs(os.path.join(out, "renders"), exist_ok=True)
    for f in ("hyperframes.json", "package.json"):
        shutil.copy2(os.path.join(GFXLIB, "project", f), os.path.join(out, f))
    name = os.path.basename(os.path.abspath(out))
    json.dump({"id": name, "name": name}, open(os.path.join(out, "meta.json"), "w"), indent=2)
    shutil.copy2(os.path.join(GFXLIB, "gfx.js"), os.path.join(out, "assets", "gfx.js"))


def copy_img(src, out, k, base):
    src = aie.expand(src if os.path.isabs(os.path.expanduser(src)) else os.path.join(base, src))
    if not os.path.exists(src): sys.exit(f"image not found: {src}")
    dst = f"i{k}{os.path.splitext(src)[1].lower()}"
    shutil.copy2(src, os.path.join(out, "assets", dst))
    return dst, src


def main():
    aie.usage(__doc__, need=2)
    ap = argparse.ArgumentParser(); ap.add_argument("kind", choices=sorted(KINDS)); ap.add_argument("out")
    ap.add_argument("--cfg", required=True, help="a JSON file, or the JSON itself"); ap.add_argument("--dur", type=float)
    ap.add_argument("--theme", default="warmcream"); ap.add_argument("--accent", default="")
    a = ap.parse_args()
    raw = a.cfg.strip()
    cfg = json.loads(raw) if raw.startswith("{") else json.load(open(aie.expand(raw)))
    base = os.getcwd() if raw.startswith("{") else os.path.dirname(aie.expand(raw))
    dur = a.dur or cfg.get("dur")
    if not dur: sys.exit("give the card's length: --dur 4.2 (the slot from the plan) or \"dur\" in the CFG")
    cfg["dur"] = dur
    out = os.path.abspath(a.out); scaffold(out)
    tpl = open(os.path.join(HERE, KINDS[a.kind])).read()
    if a.kind == "detail":
        from PIL import Image
        its = cfg["items"][:3]; n = len(its); items = []
        for i, it in enumerate(its):
            fn, src = copy_img(it["img"], out, i, base)
            im = Image.open(src)
            k = min(800 / im.width, 760 / im.height) if n <= 2 else min(560 / im.width, 640 / im.height)
            w, h = round(im.width * k), round(im.height * k)
            x = (i - (n - 1) / 2) * (0.86 if n <= 2 else 0.62)
            items.append(dict(img=fn, w=w, h=h, x=round(x, 3), y=0.06, z=0, ry=(0.12 if x < 0 else -0.12 if x > 0 else 0), tag=it["tag"],
                              tagW=int(min(760, max(260, 90 + 25 * len(it["tag"])))), tagY=round(0.06 + h / 2000 + 0.075, 3), t=it.get("t")))
        tpl = tpl.replace("/*CFG*/", json.dumps(items)).replace("/*DURN*/", str(dur))
    elif a.kind == "pair":
        for k, side in enumerate(("left", "right")):
            fn, _ = copy_img(cfg[side]["img"], out, k, base); cfg[side]["img"] = f"assets/{fn}"
        tpl = tpl.replace("/*CFG*/", json.dumps(cfg))
    else:
        tpl = tpl.replace("/*CFG*/", json.dumps(cfg))
    tpl = tpl.replace("/*DUR*/", str(dur)).replace("/*THEME*/", a.theme).replace("/*ACCENT*/", a.accent)
    open(os.path.join(out, "index.tpl"), "w").write(tpl)
    name = os.path.basename(out)
    print(f"{out}: {a.kind} card, {dur}s, theme {a.theme}{', accent ' + a.accent if a.accent else ''}\n"
          f"render:  bash {os.path.join(aie.TOOLS, 'render.sh')} {out} {name} --fonts \"Geist,Instrument Serif\"")


if __name__ == "__main__":
    main()
