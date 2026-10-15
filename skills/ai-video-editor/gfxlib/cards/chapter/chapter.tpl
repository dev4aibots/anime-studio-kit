<!doctype html>
<html lang="en" data-theme="%%THEME%%" data-accent="%%ACCENT%%">
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
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: var(--bg, #F2ECE1); }
      #stage { position: absolute; inset: 0; width: 1920px; height: 1080px; display: block; z-index: 1; }
      canvas[layoutsubtree] { position: absolute; left: 0; top: 0; z-index: -1; pointer-events: none; }
      /* Warm Cream chapter card: the number in the accent, the title in the serif, the subtitle (the speaker's words) in the sans */
      #word { display: block; text-align: center; font-family: var(--display, 'Instrument Serif', serif); font-weight: var(--display-w, 400); color: var(--ink, #1F1B17); letter-spacing: var(--display-ls, -0.012em); text-transform: var(--case, none); white-space: nowrap; }
      #num { font-family: var(--sans, Geist, sans-serif); font-weight: 600; letter-spacing: 0.16em; white-space: nowrap; display: flex; align-items: center; gap: 22px; }
      #num b { color: var(--accent, #E0703A); font-weight: 600; }
      #sub { display: block; text-align: center; font-family: var(--sans, Geist, sans-serif); font-weight: 500; color: var(--mute, #7A7064); letter-spacing: -0.01em; text-transform: var(--case, none); white-space: nowrap; }
      #ul { border-radius: 8px; background: var(--accent, #E0703A); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="1.8" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
    </div>
    <script type="module">
      import { world, dom, ready, fit, $, THREE } from "./assets/gfx.js";
      // chapter card %%NUM%% — "%%WORD%%" / "%%SUB%%" (chapter_cards.py writes one per chapter)
      const DUR = 1.8, SUB = `%%SUB%%`;
      const wordR = dom("word", 1840, 360, `<span id="wt"><span class="mk" id="ws"></span>%%WORD%%<span class="mk" id="we"></span></span>`, { style: "font-size:300px;line-height:360px" });
      const numR = dom("num", 300, 74, `<b>%%NUM%%</b>`, { style: "font-size:60px" });
      const subR = dom("sub", 1700, 90, `<span id="stx">${SUB}</span>`, { style: "font-size:60px;line-height:96px" });
      await ready();
      const fs = fit($("wt"), 1640, { min: 96, step: 4 });
      if (SUB) fit($("stx"), 1500, { min: 30, step: 2 });

      const W = await world({ floorY: -0.56 });                               // the theme comes from <html data-theme> (warmcream by default)
      const { tl, SF, rig, view, P, enter, flash, stage } = W;

      const word = P(wordR);
      const ws = word.locate("#ws"), we = word.locate("#we");                  // baseline + the title's two ends
      const capH = (fs * 0.66) / 1000;
      const G = new THREE.Group(); stage.scene.add(G);
      G.add(word.group);
      word.group.position.y = -(ws.y + capH / 2) + 0.05;                        // the caps a touch above the group's origin
      const by = ws.y + word.group.position.y;                                  // baseline in G
      const num = P(numR); G.add(num.group);
      num.group.position.set(ws.x + 0.15 + 0.006, by + capH + 0.10, 0);       // above the title, flush with its left edge
      // the accent stroke under the title: a plain bar (no glow on Warm Cream), drawn from its left end
      const ulw = Math.round((we.x - ws.x) * 1000 * 0.42);
      const ulR = dom("ul", ulw, 12, ""); const ul = P(ulR, { order: 5 });
      const piv = new THREE.Group(); G.add(piv); piv.add(ul.group);
      ul.group.position.set(ulw / 2000, 0, 0); piv.position.set(ws.x - 0.002, by - 0.058, 0.004); piv.scale.x = 1e-4; ul.state.opacity = 0;
      let sub = null;
      if (SUB) { sub = P(subR); G.add(sub.group); sub.group.position.set((ws.x + we.x) / 2, by - 0.19, 0); }

      // the slam (unchanged motion): in front of the lens at t = 0, lands with the heavy spring; 8 sub-frames blur it
      Object.assign(rig, { x: 0.09, y: 0.06, z: 2.16, tx: 0.0, ty: 0.0, tz: 0, roll: -0.012 });
      view(0, { x: -0.04, y: 0.045, z: 1.96, ty: 0.0, roll: 0.0 }, DUR, "power1.out");
      tl.fromTo(word.state, { opacity: 0.0 }, { opacity: 1, duration: 0.05, ease: "none", immediateRender: false }, 0);
      SF(G.position, { x: -0.05, y: 0.06, z: 1.25 }, { x: 0, y: 0, z: 0 }, 0, "heavy", 0.42);
      SF(G.rotation, { x: 0.22, y: -0.42, z: 0.035 }, { x: 0.0, y: 0.075, z: 0 }, 0, "heavy", 0.6);
      tl.to(G.rotation, { y: -0.02, duration: DUR - 0.6, ease: "sine.inOut" }, 0.6);
      flash(0.17, 0.025);
      tl.set(ul.state, { opacity: 1 }, 0.26);
      tl.fromTo(piv.scale, { x: 1e-4 }, { x: 1, duration: 0.5, ease: "power3.out", immediateRender: false }, 0.26);
      enter(num, 0.34, { from: { x: -0.07, z: -0.05 }, kind: "heavy", dur: 0.6 });
      if (sub) enter(sub, 0.46, { from: { y: -0.04, z: -0.03 }, kind: "heavy", dur: 0.6 });

      await W.bind(DUR);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
