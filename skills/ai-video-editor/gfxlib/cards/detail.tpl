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
      .tag { text-transform: var(--case); display: flex; align-items: center; justify-content: center; gap: 18px; border-radius: 44px; background: var(--surf); box-shadow: var(--glass-shadow);
             border: 2px solid var(--line); font-family: Geist, sans-serif; font-weight: 700; font-size: 40px;
             letter-spacing: -0.02em; color: var(--ink); white-space: nowrap; }
      .tag i { width: 16px; height: 16px; border-radius: 50%; background: var(--accent); flex: none; }
    </style>
  </head>
  <body>
    <!-- DETAIL CARD: 1–3 real images (crops, screenshots, results) side by side, each with a tag, landing on the words that
         name them. In by 1.0 s, then a slow dolly the edit trims to the sentence. new_card.py lays the items out. -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="/*DUR*/" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
    </div>
    <script type="module">
      import { world, dom, ready, loadImage, shadow } from "./assets/gfx.js";
      const CFG = /*CFG*/;   // [{ img, w, h, x, y, z, ry, tag, tagW, tagY, t? }]
      const DUR = /*DURN*/;
      const W = await world({ floorY: -0.46, pool: 0.14, poolAt: [0, -0.15] });
      const { tl, D, view, aim, breathe, IMG, P, enter } = W;
      const ims = await Promise.all(CFG.map((c) => loadImage(`assets/${c.img}`)));
      const items = CFG.map((c, i) => {
        const p = IMG(ims[i], c.w, c.h, { radius: 12, sheen: true, shadow: shadow(60, 30) });
        p.group.position.set(c.x, c.y, c.z || 0); p.group.rotation.y = c.ry || 0;
        const t = P(dom(`tag${i}`, c.tagW, 88, `<i></i>${c.tag}`, { cls: "tag" }), { order: 6 });
        t.group.position.set(c.x, c.tagY, (c.z || 0) + 0.06);
        return { c, p, t };
      });
      await ready();
      view(0, aim(0, 0.1, 0, D * 1.16, { oy: 0.05 }), 0);
      items.forEach(({ c, p, t }, i) => {
        const side = c.x < -0.01 ? 1 : c.x > 0.01 ? -1 : 0;
        const t0 = c.t != null ? c.t : 0.1 + 0.13 * i;               // an item can land on a spoken word (c.t), else staggered in
        enter(p, t0, { from: { z: -0.45, y: side ? -0.05 : 0.08, ry: 0.3 * side }, kind: "ui", dur: 0.9 });
        enter(t, t0 + 0.45, { from: { y: 0.05 }, kind: "heavy", dur: 0.6 });
      });
      breathe(0.25, 0.4);
      view(0.001, aim(0, 0.1, 0, D * 1.04, { oy: 0.035 }), 1.2, "power3.out");
      view(1.2, aim(0, 0.1, 0, D * 0.97, { oy: 0.03 }), DUR - 1.2, "none");
      await W.bind(DUR);
      window.__timelines["main"] = W.tl;
    </script>
  </body>
</html>
