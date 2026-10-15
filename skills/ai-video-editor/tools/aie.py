#!/usr/bin/env python3
"""aie.py — where everything lives. Every tool imports this; run it on its own to print the paths it resolved.

Two places, never mixed:
  the skill folder (where this file is)   the code: tools/, engine/, gfxlib/, scenes/, templates/, the docs
  AI_EDITOR_HOME (default ~/ai-video-editor)
                                           everything downloaded or made:
      venv/          the Python the tools run with (numpy, pillow, opencv)
      node_modules/  HyperFrames, GSAP and three.js, pinned (npm)
      vendor/        fonts/ (woff2 + fonts.css, ttf/ for the PIL-drawn pills), models/ (iphone.glb, macbook.glb)
      models/        the whisper model (ggml-medium.en.bin)
      music/         your own licensed music beds (e.g. free Mixkit tracks)
      sfx/           your own sound effects: whoosh/ pop/ shutter/ riser/ (any .wav/.mp3 inside)
      logos3d/       3D logo clips rendered once by gfxlib/logo_clip.py, reused in every video
      projects/      one folder per video: projects/<slug>/edit/ (the cut) and projects/<slug>/gfx/ (its graphics)
      vocab.txt      optional: names you say often (one per line), given to whisper as a hint
      folds.json     optional: {"heard": "meant"} spellings to treat as equal when a cut is checked ("cloud": "claude")
Overrides: WHISPER_MODEL (a model file), WHISPER_CLI (the whisper.cpp binary), PY (the Python for render.sh).

    python aie.py          prints every path and whether it exists"""
import json, os, platform, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(SKILL, "tools")
ENGINE = os.path.join(SKILL, "engine")
GFXLIB = os.path.join(SKILL, "gfxlib")
HOME = os.path.abspath(os.path.expanduser(os.environ.get("AI_EDITOR_HOME") or "~/ai-video-editor"))
VENDOR = os.path.join(HOME, "vendor")
FONTS = os.path.join(VENDOR, "fonts")
TTF = os.path.join(FONTS, "ttf")
MODELS3D = os.path.join(VENDOR, "models")
NODE = os.path.join(HOME, "node_modules")
MUSIC = os.path.join(HOME, "music")
SFX = os.path.join(HOME, "sfx")
LOGOS3D = os.path.join(HOME, "logos3d")
PROJECTS = os.path.join(HOME, "projects")
BIN = os.path.join(HOME, "bin")
WHISPER_MODEL = os.path.abspath(os.path.expanduser(os.environ.get("WHISPER_MODEL") or os.path.join(HOME, "models", "ggml-medium.en.bin")))
HYPERFRAMES_VERSION = "0.8.137"
MAC = platform.system() == "Darwin"


def expand(p):
    """a path from a plan or a command line: ~ and $AI_EDITOR_HOME (set or not: its default) and any other $VAR expanded"""
    if not p:
        return p
    p = str(p).replace("${AI_EDITOR_HOME}", HOME).replace("$AI_EDITOR_HOME", HOME)
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))


def whisper_cli():
    return os.environ.get("WHISPER_CLI") or shutil.which("whisper-cli") or "whisper-cli"


def need_model():
    if not os.path.exists(WHISPER_MODEL):
        raise SystemExit(f"no whisper model at {WHISPER_MODEL}: download ggml-medium.en.bin (SETUP-PROMPT.md, step 5) "
                         f"or point WHISPER_MODEL at one")
    return WHISPER_MODEL


def prompt(base="Umm, so, so I I think, like, the the, uh, you know, it's it's, okay."):
    """a disfluent prompt (so whisper writes restarts and repeats instead of smoothing them away) + your vocab.txt names"""
    f = os.path.join(HOME, "vocab.txt")
    names = [l.strip() for l in open(f, encoding="utf-8")] if os.path.exists(f) else []
    names = [n for n in names if n and not n.startswith("#")][:30]
    return base + (" " + ", ".join(names) + "." if names else "")


def folds():
    """{"heard": "meant"} from AI_EDITOR_HOME/folds.json, lowercase, for comparing what was said with what was heard"""
    f = os.path.join(HOME, "folds.json")
    return {k.lower(): v.lower() for k, v in json.load(open(f)).items()} if os.path.exists(f) else {}


def ttf(name):
    """a font file for PIL (Geist.ttf, InstrumentSerif.ttf), installed by tools/install_assets.py"""
    p = os.path.join(TTF, name)
    if not os.path.exists(p):
        raise SystemExit(f"missing {p}: run  python {os.path.join(TOOLS, 'install_assets.py')}")
    return p


def hyperframes():
    """the pinned HyperFrames CLI: AI_EDITOR_HOME/node_modules first, else npx (downloads it once)"""
    b = os.path.join(NODE, ".bin", "hyperframes")
    return [b] if os.path.exists(b) else ["npx", "--yes", f"hyperframes@{HYPERFRAMES_VERSION}"]


def python():
    """the Python the tools run with: AI_EDITOR_HOME/venv if it exists, else the one running now"""
    for p in (os.path.join(HOME, "venv", "bin", "python"), os.path.join(HOME, "venv", "Scripts", "python.exe")):
        if os.path.exists(p):
            return p
    return sys.executable


def ocr_bin():
    """Apple's on-device text recognition (tools/ocr.swift), built once into AI_EDITOR_HOME/bin/ocr. macOS only:
    returns None elsewhere (or when swiftc is missing), and the screen tools then work with hand-set boxes only."""
    out = os.path.join(BIN, "ocr")
    if os.path.exists(out):
        return out
    if not MAC or not shutil.which("swiftc"):
        return None
    os.makedirs(BIN, exist_ok=True)
    r = subprocess.run(["swiftc", "-O", os.path.join(TOOLS, "ocr.swift"), "-o", out], capture_output=True, text=True)
    if r.returncode:
        print("could not build the OCR helper (swiftc):", r.stderr.strip()[-300:], file=sys.stderr)
        return None
    return out


def ocr(png):
    """OCR one image: [{text, x, y, w, h, conf}] in pixels from the top-left, reading order; [] when OCR isn't available"""
    b = ocr_bin()
    if not b:
        return []
    r = subprocess.run([b, png], capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("lines", [])
    except Exception:
        return []


def usage(doc, argv=None, need=1):
    """print a tool's docstring and exit when it is called with -h/--help or with fewer than `need` arguments"""
    a = sys.argv[1:] if argv is None else argv
    if any(x in ("-h", "--help") for x in a) or len(a) < need:
        print(doc.strip())
        sys.exit(0 if any(x in ("-h", "--help") for x in a) else 2)


if __name__ == "__main__":
    usage(__doc__, need=0)
    rows = [("skill", SKILL), ("AI_EDITOR_HOME", HOME), ("python", python()), ("whisper-cli", shutil.which(whisper_cli()) or whisper_cli()),
            ("whisper model", WHISPER_MODEL), ("hyperframes", " ".join(hyperframes())), ("fonts", FONTS), ("device models", MODELS3D),
            ("music", MUSIC), ("sfx", SFX), ("3D logos", LOGOS3D), ("projects", PROJECTS)]
    for k, v in rows:
        print(f"{k:15s} {v}" + ("" if (os.path.exists(v) or k in ("hyperframes",)) else "   (missing)"))
