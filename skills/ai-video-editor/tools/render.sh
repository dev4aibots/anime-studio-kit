#!/bin/bash
# render.sh <project_dir> [name] [--fonts "Geist,Instrument Serif"] [--alpha]
#   link → lint → validate → render (1 worker) → mix (if audio/cues.json) → encode → contact sheet
#   --alpha: a transparent ProRes 4444 .mov instead (no mix, no encode) — for clips laid over footage (3D logo stickers)
# → <project_dir>/renders/<name>.mp4 (or .mov) + <name>-sheet.png
# Gentle by design: one worker, ONE render at a time on this machine (a lock in /tmp), and it waits while any other
# HyperFrames render is running. Never start a second render beside it.
set -euo pipefail
if [ $# -lt 1 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0; fi
P="$(cd "$1" && pwd)"; shift
NAME="promo"; if [ $# -gt 0 ] && [[ "$1" != --* ]]; then NAME="$1"; shift; fi
FONTS=""; ALPHA=""; while [ $# -gt 0 ]; do case "$1" in --fonts) FONTS="$2"; shift 2;; --alpha) ALPHA=1; shift;; *) shift;; esac; done
HERE="$(cd "$(dirname "$0")" && pwd)"
AIE="${AI_EDITOR_HOME:-$HOME/ai-video-editor}"
if [ -z "${PY:-}" ]; then if [ -x "$AIE/venv/bin/python" ]; then PY="$AIE/venv/bin/python"; else PY=python3; fi; fi
# the pinned HyperFrames: a node_modules up the tree from the project, else AI_EDITOR_HOME's, else npx (downloads it once)
HF=""; d="$P"; while [ "$d" != "/" ]; do [ -x "$d/node_modules/.bin/hyperframes" ] && HF="$d/node_modules/.bin/hyperframes" && break; d="$(dirname "$d")"; done
[ -z "$HF" ] && [ -x "$AIE/node_modules/.bin/hyperframes" ] && HF="$AIE/node_modules/.bin/hyperframes"
[ -z "$HF" ] && HF="npx --yes hyperframes@0.8.137"
mkdir -p "$P/renders"
# one render at a time: a lock (two queued renders used to pass a pgrep check together and the second one failed);
# the lock remembers its owner, so a killed render can't block the queue for ever
LOCK=/tmp/launch-video-render.lock
while ! mkdir "$LOCK" 2>/dev/null; do
  owner=$(cat "$LOCK/pid" 2>/dev/null || true)
  if [ -n "$owner" ] && ! kill -0 "$owner" 2>/dev/null; then rm -rf "$LOCK"; continue; fi
  echo "another render is running — waiting…"; sleep 10
done
echo $$ > "$LOCK/pid"; trap 'rm -rf "$LOCK"' EXIT
# …and any HyperFrames render started some other way: count only node processes running `hyperframes … render` — a pgrep
# on the text also matched shells whose command line merely mentioned both words, and stalled the queue
hf_busy() { ps -axo comm=,args= | awk '$1 ~ /(^|\/)node$/ && /hyperframes/ && / render( |$)/ { f = 1 } END { exit !f }'; }
while hf_busy; do echo "another HyperFrames render is running — waiting…"; sleep 10; done
"$PY" "$HERE/link.py" "$P" ${FONTS:+--fonts "$FONTS"}
cd "$P"
$HF lint > renders/lint.log 2>&1 || true; grep -E "✗|◇" renders/lint.log | tail -3 || true
$HF validate > renders/validate.log 2>&1 || true; grep -E "✗|◇" renders/validate.log | head -6 || true
if [ -n "$ALPHA" ]; then
  if ! $HF render --workers 1 --format mov --output "renders/$NAME.mov" > renders/render.log 2>&1; then tail -25 renders/render.log; exit 1; fi
  grep -E "rendered in" renders/render.log | tail -1 || true
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/$NAME.mov")
  TS=$("$PY" -c "d=float('$DUR'); print(' '.join(f'{d*(i+0.5)/12:.2f}' for i in range(12)))")
  "$PY" "$HERE/sheet.py" "renders/$NAME.mov" "renders/$NAME-sheet.png" $TS --cols 12 --w 160 >/dev/null || true
  echo "→ $P/renders/$NAME.mov  ($(du -h "renders/$NAME.mov" | cut -f1), ${DUR}s, alpha)   sheet: renders/$NAME-sheet.png"; exit 0
fi
if ! $HF render --workers 1 --quality delivery --output renders/raw.mp4 > renders/render.log 2>&1; then tail -25 renders/render.log; exit 1; fi
grep -E "rendered in" renders/render.log | tail -1 || true
SRC=renders/raw.mp4
if [ -f audio/cues.json ]; then "$PY" "$HERE/mix.py" audio/cues.json renders/raw.mp4 renders/mix.mp4; SRC=renders/mix.mp4; fi
ffmpeg -v error -y -i "$SRC" -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a copy -movflags +faststart "renders/$NAME.mp4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/$NAME.mp4")
TS=$("$PY" -c "d=float('$DUR'); print(' '.join(f'{d*(i+0.5)/12:.2f}' for i in range(12)))")
"$PY" "$HERE/sheet.py" "renders/$NAME.mp4" "renders/$NAME-sheet.png" $TS --cols 12 --w 160 >/dev/null
echo "→ $P/renders/$NAME.mp4  ($(du -h "renders/$NAME.mp4" | cut -f1), ${DUR}s)   sheet: renders/$NAME-sheet.png"
