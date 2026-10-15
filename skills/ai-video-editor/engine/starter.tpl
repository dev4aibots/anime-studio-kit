<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={{W}}, height={{H}}" />
    <script src="assets/vendor/gsap.min.js"></script>
    <script type="importmap">
      { "imports": { "three": "./assets/vendor/three/three.module.js", "three/addons/": "./assets/vendor/three/addons/" } }
    </script>
    <style>
/*FONTS*/
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: {{W}}px; height: {{H}}px; overflow: hidden; background: {{BG}}; }
      #stage { position: absolute; inset: 0; width: {{W}}px; height: {{H}}px; display: block; z-index: 1; }
      canvas[layoutsubtree] { position: absolute; left: 0; top: 0; z-index: -1; pointer-events: none; }
      .box { display: flex; align-items: center; justify-content: center; flex-direction: column; width: 100%; height: 100%; }
      .h { font-family: {{FONT}}; font-weight: 800; color: {{INK}}; letter-spacing: -0.03em; line-height: 0.98; text-align: center; }
      .s { font-family: {{FONT}}; font-weight: 400; color: {{INK}}; opacity: 0.7; text-align: center; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{DUR}}" data-width="{{W}}" data-height="{{H}}">
      <canvas id="stage" width="{{W}}" height="{{H}}"></canvas>
      <!-- one <canvas layoutsubtree> per panel: CSS size = the panel, bitmap 2×. Never opacity:0 on these (0 pixels). -->
      <canvas id="c-title" layoutsubtree width="2000" height="520" style="width:1000px;height:260px"><div id="title" class="box h fit" style="font-size:200px">{{NAME}}</div></canvas>
      <canvas id="c-line" layoutsubtree width="2000" height="320" style="width:1000px;height:160px"><div id="line" class="box s" style="font-size:52px;line-height:1.25;padding:0 60px">{{LINE}}</div></canvas>
    </div>

    <script type="module">
      import { Stage, ground, THREE } from "./assets/vendor/launch.js";
      import { beatGrid, director, fitText, schedule, wall, burst, makePanelDom } from "./assets/vendor/kit.js";
      await document.fonts.ready;
      await Promise.all([...document.images].map((im) => (im.complete ? 0 : new Promise((r) => (im.onload = im.onerror = r)))));
      fitText(".fit");

      // music: {{MUSIC}} from {{MSTART}} s ({{BPM}} BPM) — its drop is bar {{DROPBAR}} here
      const g = beatGrid({{BEAT}});
      const { B, b, cut } = g;
      const stage = new Stage({ canvas: document.getElementById("stage"), width: {{W}}, height: {{H}}, background: "{{BG}}" });
      ground(stage, { colorA: "{{BG}}", colorB: "{{BG}}", dots: 0.05, size: 80 });
      const tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
      const d = director(stage, tl);
      const { cam, D } = d;

      // ── shots: one block per bar. Every word and number on screen comes from the capture. ──────────────────────────
      Object.assign(cam, { x: 0, y: 0, z: D + 0.25, tx: 0, ty: 0, tz: 0 });
      d.move(0.001, { z: D - 0.08 }, {{DUR}} - 0.02, "none");
      const title = d.hud("title", 1000, 260, 0, -60), line = d.hud("line", 1000, 160, 0, 150);
      d.slam(title, cut(B({{DROPBAR}})), 1.25);
      d.rise(line, B({{DROPBAR}}) + b(2));

      tl.to({}, { duration: 0.001 }, {{DUR}});
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
