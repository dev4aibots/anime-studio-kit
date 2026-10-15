#!/usr/bin/env bash
# anime-studio-kit installer — one command sets up the entire JS anime pipeline.
# Usage: bash install.sh
# What it installs: all skills, libraries, frameworks and repos discussed —
#   pure-code JS anime video (MP4) + audio (MP3/WAV) generation with OpenCode.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
STUDIO="$HOME/anime-studio"
SKILLS_SRC="$KIT_DIR/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"

echo "=== anime-studio-kit installer ==="
echo "Studio dir : $STUDIO"
echo "Skills src : $SKILLS_SRC"
echo ""

# ---------- 0. prerequisites ----------
need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1 — please install it first."; MISSING=1; }; }
MISSING=0
need git; need node; need npm; need python3; need ffmpeg
if [ "$MISSING" = "1" ]; then echo "Install the missing tools and re-run."; exit 1; fi
NODE_MAJOR=$(node -p "process.versions.node.split('.')[0]")
if [ "$NODE_MAJOR" -lt 18 ]; then echo "Node 18+ required (found $NODE_MAJOR)."; exit 1; fi
echo "Prerequisites OK (node $(node -v), $(ffmpeg -version 2>/dev/null | head -1))"
echo ""

# ---------- 1. clone upstream repos ----------
mkdir -p "$STUDIO/jsmotion"
clone() { # $1 = repo, $2 = dest dir name
  if [ -d "$STUDIO/jsmotion/$2" ]; then echo "exists: $2 (skipping)"; else
    echo "cloning: $1"; git clone --depth 1 "https://github.com/$1" "$STUDIO/jsmotion/$2"
  fi
}
clone "yihui-dev/awesome-opus5-5-videos" "awesome-opus5-5-videos"
clone "BowTiedSwan/animejs-skills"       "animejs-skills"
clone "cth9191/animate"                  "animate"
clone "met4citizen/HeadTTS"              "headtts"
clone "met4citizen/TalkingHead"          "talkinghead"
clone "iart-ai/javascript-animation-skills" "packs/javascript-animation-skills"
clone "iart-ai/kinetic-typography-skills"   "packs/kinetic-typography-skills"
clone "iart-ai/motion-design-skills"        "packs/motion-design-skills"
clone "iart-ai/webgl-animation-skills"      "packs/webgl-animation-skills"
clone "greensock/gsap-skills"               "packs/gsap-skills"
echo ""

# ---------- 2. npm libraries (video, audio, animation) ----------
mkdir -p "$STUDIO/jsmotion/pipeline"
cd "$STUDIO/jsmotion/pipeline"
[ -f package.json ] || npm init -y >/dev/null 2>&1
echo "installing JS libraries (this takes a few minutes)..."
npm install --no-audit --no-fund \
  hyperframes \
  gsap \
  animejs \
  mediabunny \
  @webav/av-cliper \
  kokoro-js \
  zzfx \
  rhubarb-lip-sync-wasm \
  @mojs/core \
  spessasynth \
  @diffusionstudio/core \
  pixi-particle-system \
  three \
  pixi.js
echo ""

# ---------- 3. HeadTTS deps (needs TMPDIR outside tiny /tmp) ----------
if [ -d "$STUDIO/jsmotion/headtts" ]; then
  echo "installing HeadTTS deps..."
  mkdir -p "$STUDIO/jsmotion/headtts/tmp"
  (cd "$STUDIO/jsmotion/headtts" && TMPDIR="$STUDIO/jsmotion/headtts/tmp" npm install --no-audit --no-fund) || \
    echo "HeadTTS install had issues — see its README; not fatal."
fi
echo ""

# ---------- 4. skills -> OpenCode ----------
mkdir -p "$OPENCODE_SKILLS"
echo "installing skills into OpenCode ($OPENCODE_SKILLS)..."
for s in "$SKILLS_SRC"/*/; do
  name=$(basename "$s")
  rm -rf "$OPENCODE_SKILLS/$name"
  cp -r "$s" "$OPENCODE_SKILLS/$name"
  echo "  skill: $name"
done
echo ""

# ---------- 5. opencode.json ----------
if [ -f "$HOME/.config/opencode/opencode.json" ]; then
  echo "opencode.json already exists — leaving yours untouched."
  echo "See $KIT_DIR/opencode.json for the recommended additions."
else
  mkdir -p "$HOME/.config/opencode"
  cp "$KIT_DIR/opencode.json" "$HOME/.config/opencode/opencode.json"
  echo "installed opencode.json"
fi
echo ""

echo "=== DONE ==="
echo "Studio : $STUDIO/jsmotion"
echo "Skills : $OPENCODE_SKILLS (11 skills)"
echo "Next   : cd $STUDIO/jsmotion/pipeline && npx hyperframes --help"
echo "Read   : $KIT_DIR/README.md for the pipeline guide."
