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
      /* an icon tile: a warm white card, the icon drawn in the accent, the spoken word under it */
      .tile { background: var(--surf, #FFFCF7); border: 2px solid var(--line, rgba(70,45,20,0.12)); border-radius: 40px;
              display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 26px; }
      .tile svg { width: 132px; height: 132px; stroke: var(--accent, #E0703A); stroke-width: 1.7; }
      .tile .lb { font-family: var(--sans, Geist, sans-serif); font-weight: 600; font-size: 40px; color: var(--ink, #1F1B17);
                  letter-spacing: -0.02em; text-transform: var(--case, none); white-space: nowrap; }
      .wire { border-radius: 6px; background: var(--accent, #E0703A); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="%%DUR%%" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
    </div>
    <script type="module">
      import { world, dom, ready, fit, $, THREE, shadow } from "./assets/gfx.js";
      // line icons: ITEMS = [{icon, label (the speaker's words), t (the word's time in this clip)}], FLOW joins them
      const DUR = %%DUR%%, ITEMS = %%ITEMS%%, FLOW = %%FLOW%%, ICONS = %%ICONS%%;
      const N = ITEMS.length, TW = 330, TH = 340, GAP = N > 3 ? 120 : 170;
      const tiles = ITEMS.map((it, i) => dom(`tile${i}`, TW, TH,
        `${ICONS[it.icon]}<div class="lb" id="lb${i}">${it.label}</div>`, { cls: "tile" }));
      const wires = FLOW ? ITEMS.slice(1).map((_, i) => dom(`wire${i}`, GAP - 40, 10, "", { cls: "wire" })) : [];
      await ready();
      ITEMS.forEach((_, i) => fit($(`lb${i}`), TW - 40, { min: 22, step: 2 }));

      const W = await world({ floorY: -0.5 });                                // the theme comes from <html data-theme>
      const { tl, SF, rig, view, P, enter, stage, d } = W;
      const span = N * TW + (N - 1) * GAP, x0 = -span / 2000 + TW / 2000;
      const G = new THREE.Group(); stage.scene.add(G);
      const ps = tiles.map((r, i) => { const p = P(r, { live: true, order: 4, shadow: shadow(28, 14) }); G.add(p.group); p.group.position.set(x0 + i * (TW + GAP) / 1000, 0.02, 0); return p; });
      const ws = wires.map((r, i) => {
        const p = P(r, { order: 3 }); const piv = new THREE.Group(); G.add(piv); piv.add(p.group);
        p.group.position.set((GAP - 40) / 2000, 0, 0);
        piv.position.set(x0 + i * (TW + GAP) / 1000 + TW / 2000 + 0.02, 0.02, -0.004); piv.scale.x = 1e-4; p.state.opacity = 0;
        return { p, piv };
      });

      // every stroke of every icon, with its length, so it can draw itself
      const strokes = ITEMS.map((_, i) => [...$(`tile${i}`).querySelectorAll("path,circle,line,rect,polyline,polygon,ellipse")].map((el) => {
        const L = el.getTotalLength ? el.getTotalLength() : 100; el.style.strokeDasharray = `${L}`; el.style.strokeDashoffset = `${L}`; return { el, L };
      }));
      const ease = (u) => 1 - Math.pow(1 - Math.min(1, Math.max(0, u)), 3);
      d.onSync((ts) => {
        ITEMS.forEach((it, i) => {
          const u = (ts - it.t - 0.12) / 0.75, n = strokes[i].length;
          strokes[i].forEach((s, j) => {                              // the strokes draw one after another, overlapping
            const v = ease(u * 1.6 - (j / Math.max(1, n)) * 0.6);
            s.el.style.strokeDashoffset = `${s.L * (1 - v)}`;
          });
        });
      });

      // a slow push-in with the house drift; each tile springs in on its word
      Object.assign(rig, { x: 0.03, y: 0.02, z: 1.78, tx: 0, ty: 0.0, tz: 0 });
      view(0, { x: -0.02, y: 0.0, z: 1.6, tx: 0, ty: 0.0 }, DUR, "power1.inOut");
      ps.forEach((p, i) => enter(p, ITEMS[i].t, { from: { y: -0.06, z: -0.12, rx: 0.12, s: 0.92 }, kind: "ui", dur: 0.7 }));
      ws.forEach((w, i) => {
        const t = ITEMS[i + 1].t - 0.08;
        tl.set(w.p.state, { opacity: 1 }, t);
        tl.fromTo(w.piv.scale, { x: 1e-4 }, { x: 1, duration: 0.42, ease: "power3.out", immediateRender: false }, t);
      });

      await W.bind(DUR);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
