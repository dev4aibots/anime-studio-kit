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
      .ln { text-transform: var(--case); display: flex; align-items: center; justify-content: center; font-family: var(--display); font-weight: var(--display-w); color: var(--ink);
            letter-spacing: var(--display-ls); white-space: nowrap; line-height: 1; }
      .ln b { color: var(--accent-t); font-weight: inherit; }
      .ln.sm { font-family: var(--sans); font-weight: 600; color: var(--mute); letter-spacing: -0.01em; }
    </style>
  </head>
  <body>
    <!-- WORDS CARD: the speaker's exact phrases, each landing on the word it is said; one key word in the accent and
         an accent underline under the line that carries the point. Filled by new_card.py (CFG times = the spoken words). -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="/*DUR*/" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
    </div>
    <script type="module">
      import { world, dom, ready, fit, textWidth, $, THREE } from "./assets/gfx.js";
      const CFG = /*CFG*/;   // { dur, lines: [{ text, t, size, small, accent }], ul }
      const rows = CFG.lines.map((l, i) => {
        const html = l.accent ? l.text.replace(l.accent, `<b>${l.accent}</b>`) : l.text;
        return { l, r: dom(`ln${i}`, 1760, Math.round(l.size * 1.3), `<span id="lt${i}">${html}</span>`,
                           { cls: "ln" + (l.small ? " sm" : ""), style: `font-size:${l.size}px` }) };
      });
      await ready();
      rows.forEach((_, i) => fit($(`lt${i}`), 1620, { min: 40, step: 4 }));
      const widths = rows.map((_, i) => textWidth($(`lt${i}`)));
      const W = await world({ floorY: -0.6, pool: 0.18, poolAt: [0, -0.7] });
      const { tl, D, view, aim, breathe, P, enter, neon, stage } = W;
      const G = new THREE.Group(); stage.scene.add(G);
      const hs = rows.map(({ l }) => (l.size * 1.3) / 1000), gap = 0.03;
      const total = hs.reduce((a, b) => a + b, 0) + gap * (rows.length - 1);
      let y = total / 2 + 0.06;
      const ps = rows.map(({ l, r }, i) => {
        const p = P(r); G.add(p.group); y -= hs[i] / 2; p.group.position.set(0, y, 0); y -= hs[i] / 2 + gap; return p;
      });
      ps.forEach((p, i) => enter(p, CFG.lines[i].t, { from: { z: -0.45, y: -0.07, rx: 0.25 }, kind: "heavy", dur: 0.6 }));
      if (CFG.ul != null) {
        const i = CFG.ul, p = ps[i], w = Math.round(widths[i]) + 40;
        const line = neon("ul", w, { parent: G, x: 0, y: p.group.position.y - hs[i] / 2 + 0.01, z: 0.004, h: 10, glow: 2.4 });
        line.draw(CFG.lines[i].t + 0.18, 0.4, "power3.out");
        breathe(CFG.lines[i].t + 0.1, 0.6);
      }
      breathe(CFG.lines[0].t, 0.45);
      G.rotation.y = -0.07;
      tl.to(G.rotation, { y: 0.05, duration: CFG.dur, ease: "sine.inOut" }, 0);
      view(0, aim(0, 0.08, 0, D * 1.1, { oy: 0.04 }), 0);
      view(0.001, aim(0, 0.08, 0, D * 0.97, { oy: 0.03 }), CFG.dur, "none");
      await W.bind(CFG.dur);
      window.__timelines["main"] = W.tl;
    </script>
  </body>
</html>
