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
      .tag.big { font-size: 64px; gap: 26px; border-radius: 70px; }   /* ≥ 34 px on screen in the wide view */
      .tag.big i { width: 24px; height: 24px; }
    </style>
  </head>
  <body>
    <!-- PAIR CARD: two real images side by side on two screens (two results, before/after, two pages), each with a tag.
         One clip, four held views the edit cuts between on the speaker's words (plan.py src=), scaled to DUR (here for 29 s):
         WIDE 0.9–7.0 · LEFT 7.6–14.6 · RIGHT 15.2–22.2 · WIDE 22.8–29.0 (0.6 s camera moves between them).
         CFG = { left: { img: "assets/left.jpg", tag: "Before" }, right: { img: "assets/right.jpg", tag: "After" } } (new_card.py) -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="/*DUR*/" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
    </div>
    <script type="module">
      import { world, dom, ready, loadImage, shadow } from "./assets/gfx.js";
      const CFG = /*CFG*/;
      const DUR = /*DUR*/, q = DUR / 29.0;                 // the four views keep their proportions at any length
      const W = await world({ floorY: -0.46, pool: 0.14, poolAt: [0, -0.15] });
      const { tl, D, view, aim, breathe, IMG, P, enter } = W;
      const [li, ri] = await Promise.all([loadImage(CFG.left.img), loadImage(CFG.right.img)]);
      const X = 0.86, Y = 0.12, TY = Y + 0.45 + 0.1;   // tags ABOVE the screens (a mirror floor would show them upside down)
      const L = IMG(li, 1600, 900, { radius: 12, sheen: true, shadow: shadow(70, 34) });
      const R = IMG(ri, 1600, 900, { radius: 12, sheen: true, shadow: shadow(70, 34) });
      L.group.position.set(-X, Y, 0); L.group.rotation.y = 0.1;
      R.group.position.set(X, Y, 0); R.group.rotation.y = -0.1;
      const tw = (s) => Math.min(900, Math.max(360, 120 + 38 * s.length));
      const tL = P(dom("tagL", tw(CFG.left.tag), 136, `<i></i>${CFG.left.tag}`, { cls: "tag big" }), { order: 6 });
      const tR = P(dom("tagR", tw(CFG.right.tag), 136, `<i></i>${CFG.right.tag}`, { cls: "tag big" }), { order: 6 });
      tL.group.position.set(-X, TY, 0.02); tR.group.position.set(X, TY, 0.02);
      await ready();

      // the screens swing in, the tags rise above them
      view(0, aim(0, 0.18, 0, D * 2.05, { oy: 0.09 }), 0);
      enter(L, 0.12, { from: { z: -0.55, y: -0.06, ry: 0.32 }, kind: "ui", dur: 0.95 });
      enter(R, 0.26, { from: { z: -0.55, y: -0.06, ry: -0.32 }, kind: "ui", dur: 0.95 });
      enter(tL, 0.62, { from: { y: 0.05 }, kind: "heavy", dur: 0.6 });
      enter(tR, 0.72, { from: { y: 0.05 }, kind: "heavy", dur: 0.6 });
      breathe(0.3, 0.45);
      view(0.001, aim(0, 0.18, 0, D * 1.86, { oy: 0.06 }), 6.95 * q, "power2.out");
      // the left screen
      view(7.0 * q, aim(-X, 0.2, 0, D * 1.19, { ox: 0.1 }), 0.6);
      view(7.0 * q + 0.6, aim(-X, 0.2, 0, D * 1.12, { ox: 0.07 }), 7.6 * q - 0.6, "none");
      breathe(7.0 * q, 0.18);
      // the right screen
      view(14.6 * q, aim(X, 0.2, 0, D * 1.19, { ox: -0.1 }), 0.6);
      view(14.6 * q + 0.6, aim(X, 0.2, 0, D * 1.12, { ox: -0.07 }), 7.6 * q - 0.6, "none");
      breathe(14.6 * q, 0.18);
      // both again
      view(22.2 * q, aim(0, 0.18, 0, D * 1.96, { oy: 0.07 }), 0.6);
      view(22.2 * q + 0.6, aim(0, 0.18, 0, D * 1.82, { oy: 0.06 }), DUR - 22.2 * q - 0.6, "none");
      breathe(22.2 * q, 0.18);
      await W.bind(DUR);
      window.__timelines["main"] = W.tl;
    </script>
  </body>
</html>
