<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=/*W*/, height=/*H*/" />
    <script src="assets/vendor/gsap.min.js"></script>
    <script type="importmap">
      { "imports": { "three": "./assets/vendor/three/three.module.js", "three/addons/": "./assets/vendor/three/addons/" } }
    </script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: /*W*/px; height: /*H*/px; overflow: hidden; background: transparent; }
      #stage { position: absolute; inset: 0; width: /*W*/px; height: /*H*/px; display: block; }
    </style>
  </head>
  <body>
    <!-- LOGO CLIP: ONE real logo, extruded and lit, turning slowly on a TRANSPARENT stage — a seamless loop of DUR s,
         rendered with `render.sh <dir> <name> --alpha` (ProRes 4444) to lay over the face or footage.
         Built by gfxlib/logo_clip.py; the logo comes from gfxlib/logos/ (logos.json) or a brand's own SVG. -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="/*DUR*/" data-width="/*W*/" data-height="/*H*/">
      <canvas id="stage" width="/*W*/" height="/*H*/"></canvas>
    </div>
    <script type="module">
      import { Stage, bindToHyperFrames } from "./assets/vendor/launch.js";
      import { logo3d } from "./assets/gfx.js";
      const CFG = /*CFG*/;   // { dur, logo, color, width, swing, tilt }
      const stage = new Stage({ canvas: document.getElementById("stage"), width: /*W*/, height: /*H*/, transparent: true,
                                background: "#000000", samples: 8, dof: null, bloom: null, grain: 0, vignette: 0, fov: 30 });
      const tl = gsap.timeline({ paused: true });
      const g = await logo3d({ stage }, CFG.logo, { width: CFG.width, color: CFG.color, glow: 0.08 });
      g.rotation.x = CFG.tilt;
      // a seamless loop: out to one side and back through the other, easing to rest at each end (frame DUR = frame 0)
      const h = CFG.dur / 4;
      tl.fromTo(g.rotation, { y: 0 }, { y: CFG.swing, duration: h, ease: "sine.out", immediateRender: false }, 0)
        .to(g.rotation, { y: -CFG.swing, duration: 2 * h, ease: "sine.inOut" }, h)
        .to(g.rotation, { y: 0, duration: h, ease: "sine.in" }, 3 * h);
      tl.fromTo(g.position, { y: -0.004 }, { y: 0.004, duration: CFG.dur / 2, ease: "sine.inOut", yoyo: true, repeat: 1, immediateRender: false }, 0);
      tl.to({}, { duration: 0.001 }, Math.max(0, CFG.dur - 0.001));
      await bindToHyperFrames(stage, tl);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
