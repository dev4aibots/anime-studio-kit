#!/usr/bin/env python3
"""finish.py <edit_dir> — the last step, after assemble.py and a look at qc.py's sheets:
  1. the master where you will find it: <project>/renders/<slug>_FINAL.mp4 (a hard link to edit/out/final.mp4: no second copy)
  2. YouTube chapters from the cut: edit/out/chapters.txt (chapters.py)
  3. the release check: −16 LUFS ± 0.7 and a true peak ≤ −1 dBTP, measured on the file itself (voicechain.py check)
  4. on macOS, the file shown in Finder
Then write the publish sheet (SKILL.md step 10) — nothing is uploaded for you."""
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

aie.usage(__doc__)
E = os.path.abspath(sys.argv[1]); P = os.path.dirname(E); slug = os.path.basename(P)
final = os.path.join(E, "out", "final.mp4")
if not os.path.exists(final): sys.exit("no edit/out/final.mp4 yet: run assemble.py first")
os.makedirs(os.path.join(P, "renders"), exist_ok=True)
dst = os.path.join(P, "renders", f"{slug}_FINAL.mp4")
if os.path.exists(dst): os.remove(dst)
try: os.link(final, dst)
except OSError: shutil.copy2(final, dst)
print("master →", dst)
py = aie.python()
subprocess.run([py, os.path.join(aie.TOOLS, "chapters.py"), E])
ok = subprocess.run([py, os.path.join(aie.TOOLS, "voicechain.py"), "check", dst]).returncode == 0
if aie.MAC and shutil.which("open"): subprocess.run(["open", "-R", dst])
sys.exit(0 if ok else 1)
