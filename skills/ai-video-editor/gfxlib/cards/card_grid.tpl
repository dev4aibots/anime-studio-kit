<!doctype html>
<html lang="en" data-theme="/*THEME*/" data-accent="/*ACCENT*/">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="assets/vendor/gsap.min.js"></script>
    <script type="importmap">
      { "imports": { "three": "./assets/vendor/three/three.module.js", "three/addons/": "./assets/vendor/three/addons/" } }
    </script>
    <style>
/*FONTS*/
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: var(--bg); }
      #stage { position: absolute; inset: 0; width: 1920px; height: 1080px; display: block; z-index: 1; }
      canvas[layoutsubtree] { position: absolute; left: 0; top: 0; z-index: -1; pointer-events: none; }
      .tile { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; font-family: Geist, sans-serif;
              color: var(--ink); text-align: center; }
      .tile .n { font-weight: 700; font-size: 40px; letter-spacing: 0.14em; color: var(--accent-t); }
      .tile .l { text-transform: var(--case); font-weight: 700; font-size: 62px; letter-spacing: -0.03em; line-height: 1.02; white-space: nowrap; }
      .title { text-transform: var(--case); display: flex; align-items: center; justify-content: center; font-family: var(--display); font-weight: var(--display-w); font-size: 96px;
               letter-spacing: var(--display-ls); color: var(--ink); white-space: nowrap; }
      .title b { color: var(--accent-t); }
    </style>
  </head>
  <body>
    <!-- GRID CARD: a title, then N tiles (3 per row), each landing on the word that names it. Filled by new_card.py. -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="/*DUR*/" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
    </div>
    <script type="module">
      import { world, dom, ready, fit, $, THREE, shadow } from "./assets/gfx.js";
      const CFG = /*CFG*/;   // { dur, title: {text, accent, t}, tiles: [{n, label, t}] }
      const TW = 520, TH = 250;
      const tiles = CFG.tiles.map((x, i) => dom(`tile${i}`, TW, TH, `<span class="n">${x.n}</span><span class="l" id="tl${i}">${x.label}</span>`, { cls: "glass tile" }));
      const title = dom("title", 1700, 130, `<span id="tt">${CFG.title.accent ? CFG.title.text.replace(CFG.title.accent, `<b>${CFG.title.accent}</b>`) : CFG.title.text}</span>`, { cls: "title" });
      await ready();
      CFG.tiles.forEach((_, i) => fit($(`tl${i}`), TW - 60, { min: 30, step: 2 }));
      fit($("tt"), 1600, { min: 48, step: 4 });
      const W = await world({ floorY: -0.66, pool: 0.16, poolAt: [0, -0.8] });
      const { tl, D, view, aim, breathe, P, enter, stage } = W;
      const G = new THREE.Group(); stage.scene.add(G);
      const t = P(title); G.add(t.group); t.group.position.set(0, 0.4, 0.02);
      enter(t, CFG.title.t, { from: { z: -0.4, y: 0.06 }, kind: "heavy", dur: 0.6 });
      breathe(CFG.title.t, 0.45);
      const cols = 3, gx = 0.58, gy = 0.3;
      CFG.tiles.forEach((x, i) => {
        const p = P(tiles[i], { radius: 30, shadow: shadow(60, 30) }); G.add(p.group);
        const c = i % cols, r = Math.floor(i / cols);
        p.group.position.set((c - 1) * gx, 0.12 - r * gy, 0); p.group.rotation.y = (1 - c) * 0.12;
        enter(p, x.t, { from: { z: -0.5, y: -0.08, rx: 0.4 }, kind: "ui", dur: 0.8 });
      });
      G.rotation.y = -0.05; tl.to(G.rotation, { y: 0.04, duration: CFG.dur, ease: "sine.inOut" }, 0);
      view(0, aim(0, 0.08, 0, D * 1.12, { oy: 0.04 }), 0);
      view(0.001, aim(0, 0.08, 0, D * 1.0, { oy: 0.03 }), CFG.dur, "none");
      await W.bind(CFG.dur);
      window.__timelines["main"] = W.tl;
    </script>
  </body>
</html>
