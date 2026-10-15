#!/usr/bin/env python3
"""link.py — prepare a graphic (a HyperFrames project) for rendering: copy the engine into <project>/assets/vendor and write
index.html from index.tpl with the font faces inlined (HyperFrames' static guard only accepts @font-face declared in the page).

    link.py <project_dir> [--fonts "Geist,Instrument Serif"]

What it copies, and from where:
  engine/launch.js, engine/kit.js                         this skill
  three.js r181 (three.module.js, three.core.js, addons)  AI_EDITOR_HOME/node_modules/three   (npm i three@0.181.2)
  gsap.min.js                                             AI_EDITOR_HOME/node_modules/gsap    (npm i gsap@3.14.2)
  fonts (woff2 + the @font-face blocks)                   AI_EDITOR_HOME/vendor/fonts         (tools/install_assets.py)
  iphone.glb, macbook.glb — only if index.tpl uses them   AI_EDITOR_HOME/vendor/models        (tools/install_assets.py)
render.sh runs this first; run it alone to check a template before rendering."""
import os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie

# the three.js addons the engine, gfx.js and the scenes import (paths under three/examples/jsm/)
ADDONS = ["environments/RoomEnvironment.js", "lines/LineMaterial.js", "lines/LineSegments2.js", "lines/LineSegmentsGeometry.js",
          "loaders/GLTFLoader.js", "loaders/SVGLoader.js", "objects/Reflector.js", "postprocessing/BokehPass.js",
          "postprocessing/EffectComposer.js", "postprocessing/MaskPass.js", "postprocessing/OutputPass.js", "postprocessing/Pass.js",
          "postprocessing/RenderPass.js", "postprocessing/ShaderPass.js", "postprocessing/UnrealBloomPass.js", "shaders/BokehShader.js",
          "shaders/CopyShader.js", "shaders/LuminosityHighPassShader.js", "shaders/OutputShader.js", "utils/BufferGeometryUtils.js"]


def need(path, what):
    if not os.path.exists(path):
        sys.exit(f"link.py: {what} not found at {path} — run the setup (SETUP-PROMPT.md) or tools/doctor.py")
    return path


def main():
    aie.usage(__doc__)
    proj = os.path.abspath(sys.argv[1])
    want = sys.argv[sys.argv.index("--fonts") + 1].split(",") if "--fonts" in sys.argv else None
    tpl = os.path.join(proj, "index.tpl")
    src = open(tpl if os.path.exists(tpl) else os.path.join(proj, "index.src.html")).read()
    vend = os.path.join(proj, "assets", "vendor")
    os.makedirs(os.path.join(vend, "three", "addons"), exist_ok=True)
    three = need(os.path.join(aie.NODE, "three"), "three.js (npm i three@0.181.2)")
    for f in ("three.module.js", "three.core.js"):
        shutil.copy2(need(os.path.join(three, "build", f), f"three.js {f}"), os.path.join(vend, "three", f))
    for a in ADDONS:
        dst = os.path.join(vend, "three", "addons", a); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(need(os.path.join(three, "examples", "jsm", a), f"three.js addon {a}"), dst)
    shutil.copy2(need(os.path.join(aie.NODE, "gsap", "dist", "gsap.min.js"), "GSAP (npm i gsap@3.14.2)"), os.path.join(vend, "gsap.min.js"))
    for f in ("launch.js", "kit.js"):
        shutil.copy2(os.path.join(aie.ENGINE, f), os.path.join(vend, f))
    if "vendor/models/" in src:                                        # 3.5 MB: only for graphics that load a device
        need(os.path.join(aie.MODELS3D, "iphone.glb"), "the device models")
        shutil.copytree(aie.MODELS3D, os.path.join(vend, "models"), dirs_exist_ok=True)
    css_file = need(os.path.join(aie.FONTS, "fonts.css"), "the fonts (tools/install_assets.py)")
    os.makedirs(os.path.join(vend, "fonts"), exist_ok=True)
    for f in os.listdir(aie.FONTS):
        if f.endswith(".woff2"):
            shutil.copy2(os.path.join(aie.FONTS, f), os.path.join(vend, "fonts", f))
    css = open(css_file).read().replace("url(./", "url(assets/vendor/fonts/")
    if want:
        blocks = re.findall(r"/\*[^*]*\*/\s*@font-face\s*{[^}]*}", css)
        css = "\n".join(bl for bl in blocks if any(re.sub(r"\s", "", w).lower() in re.sub(r"\s", "", bl).lower() for w in want))
    open(os.path.join(proj, "index.html"), "w").write(src.replace("/*FONTS*/", css))
    print(f"linked {proj}: engine + {css.count('@font-face')} font faces")


if __name__ == "__main__":
    main()
