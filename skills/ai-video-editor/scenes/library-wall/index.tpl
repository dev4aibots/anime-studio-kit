<!doctype html>
<html lang="en">
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
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #040405; }
      #stage { position: absolute; inset: 0; width: 1920px; height: 1080px; display: block; z-index: 1; }
      canvas[layoutsubtree] { position: absolute; left: 0; top: 0; z-index: -1; pointer-events: none; }
      .lb { font-family: Geist, sans-serif; font-weight: 800; font-size: 120px; letter-spacing: -0.045em; color: #fafafa; white-space: nowrap; display: flex; align-items: center; justify-content: center; line-height: 1; text-shadow: 0 8px 40px rgba(0,0,0,0.9), 0 0 2px rgba(0,0,0,0.6); }
      .lb em { font-style: normal; color: #ff2a48; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="6.4" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
      <canvas id="c-lb" layoutsubtree width="2800" height="320" style="width:1400px;height:160px"><div id="lb" class="lb"><span>an entire library<em>.</em></span></div></canvas>
    </div>
    <script type="module">
      import { Stage, ground, loadImage, reflectiveFloor, THREE } from "./assets/vendor/launch.js";
      import { director, wall, noir } from "./assets/vendor/kit.js";
      await document.fonts.ready;
      const spring = (t, k, d) => { if (t <= 0) return 0; const w0 = Math.sqrt(k), z = d / (2 * w0);
        if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
        return 1 - Math.exp(-w0 * t) * (1 + w0 * t); };
      const SPR = { heavy: [130, 23] };
      const sp = (kind, dur) => { const [k, d] = SPR[kind]; const end = spring(dur, k, d); return (p) => spring(p * dur, k, d) / end; };
      const stage = new Stage({ canvas: document.getElementById("stage"), width: 1920, height: 1080, background: "#040405", samples: 8,
                                dof: { strength: 26, max: 34 }, grain: 0.03, vignette: 0.4, bloom: { strength: 1.0, threshold: 1.0 } });
      ground(stage, { colorA: "#050506", colorB: "#050506", dots: 0, size: 60, z: -6 });
      const tl = gsap.timeline({ paused: true });
      const d = director(stage, tl), { cam } = d;
      const U = stage.presentMat.uniforms; const look = noir(stage, tl);   // NEON NOIR edge light: subtle, one place (kit.js)
      const pulse = (t, k = 0.5) => look.pulse(t, k);
      // the wall: every motion graphic made for this video, real frames (6 × 4, the centre tile is the hero promo)
      const N = 22, imgs = await Promise.all(Array.from({ length: N }, (_, i) => loadImage(`assets/tiles/t${String(i).padStart(2, "0")}.jpg`)));
      const order = [8, 15, 2, 19, 10, 6,  13, 1, 4, 0, 16, 11,  20, 9, 3, 14, 5, 18,  7, 17, 12, 21, 10, 2];
      const W = wall(d, imgs, { cols: 6, rows: 4, w: 640, h: 360, gapX: 44, gapY: 44, radius: 14, order, dim: 0.62 });
      await reflectiveFloor(stage, { y: -0.98, size: 30, color: "#24242a" });
      const centre = W.tiles.find((T) => T.r === 1 && T.c === 3);      // the hero frame (t00) sits here
      // light the wall in a wave from the centre outward as the camera pulls back
      const lit = new Set([centre.k]);
      W.light(0, [...lit]);
      [...W.tiles].sort((a, b) => Math.hypot(a.x - centre.x, a.y - centre.y) - Math.hypot(b.x - centre.x, b.y - centre.y))
        .forEach((T, i) => { lit.add(T.k); W.light(0.35 + i * 0.045, [...lit]); });
      Object.assign(cam, { x: centre.x + 0.05, y: centre.y + 0.02, z: 0.62, tx: centre.x, ty: centre.y, tz: 0, roll: 0.02, focus: -1, aperture: 0.7 });
      tl.to(cam, { x: 0.35, y: 0.25, z: 3.75, tx: 0.0, ty: -0.05, roll: 0, duration: 2.0, ease: "expo.out" }, 0.05);
      tl.to(cam, { x: -0.25, y: 0.2, z: 3.45, duration: 4.3, ease: "power1.inOut" }, 2.05);
      pulse(0.08, 0.6);
      const lb = d.hud("lb", 1400, 160, 0, 360);
      tl.set(lb.state, { opacity: 1 }, 1.05);
      tl.fromTo(lb.group.scale, { x: lb.group.scale.x * 1.12, y: lb.group.scale.y * 1.12 }, { x: lb.group.scale.x, y: lb.group.scale.y, duration: 0.8, ease: sp("heavy", 0.8), immediateRender: false }, 1.05);
      pulse(1.05, 0.55);
      tl.to({}, { duration: 0.001 }, 6.4);
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
