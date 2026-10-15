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
      .num { width: 80px; height: 60px; display: flex; align-items: center; justify-content: center; font-family: "JetBrains Mono", monospace; font-size: 34px; font-weight: 600; color: #fafafa; }
      .brk { width: 1500px; height: 140px; position: relative; }
      .brk svg { position: absolute; left: 0; top: 0; }
      .lbl { font-family: Geist, sans-serif; font-weight: 700; color: #fafafa; letter-spacing: -0.03em; white-space: nowrap; display: flex; align-items: center; height: 100%; text-shadow: 0 6px 34px rgba(0,0,0,0.85); }
      .lbl em { font-style: normal; color: #ff2a48; }
      .mono { font-family: "JetBrains Mono", monospace; color: #b8b8c0; }
      .fr { width: 720px; height: 440px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="22.37" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
      <canvas id="c-brk" layoutsubtree width="3000" height="280" style="width:1500px;height:140px"><div id="brk" class="brk"><svg width="1500" height="140" viewBox="0 0 1500 140"><path id="brkp" d="M 20 20 V 70 H 1480 V 20" fill="none" stroke="#ff2440" stroke-width="5" stroke-linejoin="round"/></svg></div></canvas>
      <canvas id="c-cap" layoutsubtree width="2400" height="160" style="width:1200px;height:80px"><div id="cap" class="mono" style="font-size:48px;display:flex;align-items:center;justify-content:center;height:100%">across the camera's&nbsp;<span style="color:#fafafa">shutter</span></div></canvas>
      <canvas id="c-fr" layoutsubtree width="1440" height="880" style="width:720px;height:440px"><svg id="fr" class="fr" width="720" height="440" viewBox="0 0 720 440"><rect id="frr" x="5" y="5" width="710" height="430" rx="18" fill="none" stroke="#ff2440" stroke-width="5" stroke-dasharray="26 14"/></svg></canvas>
      <canvas id="c-t1" layoutsubtree width="2400" height="300" style="width:1200px;height:150px"><div id="t1" class="lbl" style="font-size:96px">8 renders<em>.</em></div></canvas>
      <canvas id="c-t2" layoutsubtree width="2400" height="300" style="width:1200px;height:150px"><div id="t2" class="lbl" style="font-size:96px">averaged together<em>.</em></div></canvas>
      <canvas id="c-t3" layoutsubtree width="1400" height="300" style="width:700px;height:150px"><div id="t3" class="lbl" style="font-size:120px;justify-content:center">24 fps</div></canvas>
      <canvas id="c-t4" layoutsubtree width="1400" height="300" style="width:700px;height:150px"><div id="t4" class="lbl" style="font-size:120px;justify-content:center">30 fps<em>.</em></div></canvas>
      <canvas id="c-n0" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n0" class="num">1</div></canvas>
      <canvas id="c-n1" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n1" class="num">2</div></canvas>
      <canvas id="c-n2" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n2" class="num">3</div></canvas>
      <canvas id="c-n3" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n3" class="num">4</div></canvas>
      <canvas id="c-n4" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n4" class="num">5</div></canvas>
      <canvas id="c-n5" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n5" class="num">6</div></canvas>
      <canvas id="c-n6" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n6" class="num">7</div></canvas>
      <canvas id="c-n7" layoutsubtree width="160" height="120" style="width:80px;height:60px"><div id="n7" class="num">8</div></canvas>
    </div>
    <script type="module">
      import { Stage, ground, loadImage, reflectiveFloor, THREE } from "./assets/vendor/launch.js";
      import { director, wall, noir } from "./assets/vendor/kit.js";
      await document.fonts.ready;
      const spring = (t, k, d) => { if (t <= 0) return 0; const w0 = Math.sqrt(k), z = d / (2 * w0);
        if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
        return 1 - Math.exp(-w0 * t) * (1 + w0 * t); };
      const SPR = { ui: [300, 24], card: [190, 25], heavy: [130, 23], snap: [420, 32] };
      const sp = (kind, dur) => { const [k, d] = SPR[kind]; const end = spring(dur, k, d); return (p) => spring(p * dur, k, d) / end; };
      const S = (tg, v, t, kind = "card", dur = 0.8) => tl.to(tg, { ...v, duration: dur, ease: sp(kind, dur) }, t);
      const SF = (tg, f, v, t, kind = "card", dur = 0.8) => tl.fromTo(tg, f, { ...v, duration: dur, ease: sp(kind, dur), immediateRender: false }, t);
      const stage = new Stage({ canvas: document.getElementById("stage"), width: 1920, height: 1080, background: "#040405", samples: 8,
                                dof: { strength: 26, max: 34 }, grain: 0.03, vignette: 0.38, bloom: { strength: 1.1, threshold: 1.0 } });
      ground(stage, { colorA: "#050506", colorB: "#050506", dots: 0, size: 60, z: -4 });
      await reflectiveFloor(stage, { y: -0.42, size: 16, color: "#26262c" });
      const tl = gsap.timeline({ paused: true });
      const d = director(stage, tl), { cam, D } = d;
      const U = stage.presentMat.uniforms; const look = noir(stage, tl);   // NEON NOIR edge light: subtle, one place (kit.js)
      const pulse = (t, k = 0.5) => look.pulse(t, k);
      Object.assign(cam, { x: 0, y: 0.05, z: D + 0.15, tx: 0, ty: 0.05, tz: 0, roll: 0, focus: -1, aperture: 1 });
      tl.to(cam, { z: D + 0.05, duration: 4.0, ease: "none" }, 0);
      tl.to(cam, { z: D + 0.47, duration: 2.9, ease: "none" }, 5.08);
      tl.to(cam, { z: D + 0.02, duration: 2.4, ease: "none" }, 9.02);

      // the subject: a real thumbnail card (640 × 360)
      const img = await loadImage("assets/thumbs/t09.jpg");
      const card = d.image(img, 640, 360, { radius: 18, shadow: { blur: 50, y: 30, opacity: 0.6, color: "#000" } });
      card.group.position.set(-0.05, 0.08, 0);
      // 0.0 – 2.5: "the motion blur is real" — it zips off, flies back in and settles: smeared when fast, crisp at rest
      tl.to(card.group.position, { x: 2.4, duration: 0.42, ease: "power3.in" }, 0.12);
      tl.set(card.group.position, { x: -2.4 }, 0.6);
      tl.to(card.group.position, { x: -0.05, duration: 0.9, ease: "expo.out" }, 1.0);
      pulse(0.3, 0.5); pulse(1.05, 0.5);
      // 2.53: "every single frame" — the same move, frozen halfway; a frame outline marks the instant
      const fr = d.at(d.panel("fr", 720, 440, { live: true }), -0.05, 0.08, 0.02); fr.state.glow = 2.0; fr.state.opacity = 0;
      tl.set(fr.state, { opacity: 1 }, 2.52); SF(fr.group.scale, { x: 1.15, y: 1.15 }, { x: 1, y: 1 }, 2.52, "ui", 0.6);
      pulse(2.52, 0.6);
      // 4.07: "is eight renders" — the instant splits into 8 sub-frames along the path
      const ghosts = [];
      for (let k = 0; k < 8; k++) {
        const gimg = d.image(img, 640, 360, { radius: 18 });
        gimg.group.position.set(-0.05, 0.08, 0.001 * k); gimg.state.opacity = 0;
        const num = d.panel("n" + k, 80, 60); num.state.opacity = 0; stage.scene.add(num.group);
        ghosts.push({ g: gimg, n: num, x: -0.05 + (k - 3.5) * 0.17 });
      }
      d.out([fr], 4.0, 0.12);
      tl.set(card.state, { opacity: 0 }, 4.05);
      ghosts.forEach((G, k) => {
        const t = 4.05 + k * 0.05;
        tl.set(G.g.state, { opacity: 0.92 }, 4.05);
        SF(G.g.group.position, { x: -0.05, z: 0.001 * k }, { x: G.x, z: 0.06 * (k - 3.5) }, t, "ui", 0.8);
        SF(G.g.group.rotation, { y: 0 }, { y: -0.28 }, t, "ui", 0.8);
        G.n.group.position.set(G.x, 0.36, 0.06 * (k - 3.5)); tl.to(G.n.state, { opacity: 1, duration: 0.15 }, t + 0.25);
      });
      tl.to(cam, { y: 0.12, z: D + 0.55, ty: 0.06, duration: 1.0, ease: "power3.inOut" }, 4.05);
      const t1 = d.hud("t1", 1200, 150, -240, -360); d.slam(t1, 4.32, 1.15, 0.25); pulse(4.32, 0.7);
      // 5.23: "across the camera's shutter" — the bracket
      const brk = d.at(d.panel("brk", 1500, 140, { live: true }), -0.05, -0.27, 0.05); brk.state.glow = 1.9; brk.state.opacity = 0;
      const bk = { v: 1 };
      tl.set(brk.state, { opacity: 1 }, 5.2); SF(bk, { v: 1 }, { v: 0 }, 5.2, "card", 0.8);
      const cap = d.hud("cap", 1200, 80, 0, 392); tl.set(cap.state, { opacity: 1 }, 5.5);
      SF(cap.group.position, { y: cap.group.position.y - 0.02 * (0.5 / D) }, { y: cap.group.position.y }, 5.5, "heavy", 0.6);
      // 7.83: "all averaged together" — each drops to an eighth and they slide into one smear
      d.out([t1], 7.75, 0.15);
      ghosts.forEach((G, k) => {
        S(G.g.group.position, { x: -0.05 + (k - 3.5) * 0.016, z: 0 }, 7.85, "card", 1.0);
        S(G.g.group.rotation, { y: 0 }, 7.85, "card", 1.0);
        tl.to(G.g.state, { opacity: 0.125 * 1.9, duration: 0.8, ease: "power2.inOut" }, 7.85);
        tl.to(G.n.state, { opacity: 0, duration: 0.2 }, 7.85);
      });
      d.out([brk, cap], 8.2, 0.3);
      const t2 = d.hud("t2", 1200, 150, -240, -360); d.slam(t2, 8.35, 1.15, 0.25); pulse(8.35, 0.7);
      tl.to(cam, { y: 0.05, z: D + 0.1, ty: 0.05, duration: 1.0, ease: "power3.inOut" }, 8.0);
      // 10.97: "a blur when something is moving across the screen" — unfreeze: the real card leaves, blurred for real
      d.out([t2], 10.8, 0.2);
      ghosts.forEach((G) => tl.set(G.g.state, { opacity: 0 }, 10.95));
      tl.set(card.state, { opacity: 1 }, 10.95); tl.set(card.group.position, { x: -0.05 }, 10.95);
      tl.to(card.group.position, { x: 2.3, duration: 0.45, ease: "power3.in" }, 11.0);
      // 14.77: "fast moves tend to smear, like a real camera" — a whip across the thumbnails
      const imgs = await Promise.all(Array.from({ length: 27 }, (_, i) => loadImage(`assets/thumbs/t${String(i).padStart(2, "0")}.jpg`)));
      const W = wall(d, imgs, { cols: 9, rows: 3, dim: 0.35, order: [0,1,2,3,4,5,6,7,8, 9,10,11,12,13,14,15,16,17, 18,19,20,21,22,23,24,25,26] });
      W.group.position.set(8, 0.05, -0.4); W.light(0, [...Array(27).keys()]);
      tl.set(cam, { x: 5.9, y: 0.1, z: 2.2, tx: 5.9, ty: 0.05, tz: -0.4, roll: 0.0 }, 11.47);
      tl.to(cam, { x: 6.5, tx: 6.5, duration: 3.1, ease: "none" }, 11.47);
      tl.to(cam, { x: 10.2, tx: 10.2, duration: 0.62, ease: "power3.inOut" }, 14.6);
      tl.to(cam, { roll: -0.03, duration: 0.31, ease: "power2.in" }, 14.6); tl.to(cam, { roll: 0, duration: 0.4, ease: "power2.out" }, 14.91);
      tl.to(cam, { x: 10.5, tx: 10.5, duration: 1.3, ease: "none" }, 15.22);
      tl.to(cam, { x: 8.0, tx: 8.0, z: 2.45, duration: 0.62, ease: "power3.inOut" }, 16.6);
      tl.to(cam, { roll: 0.025, duration: 0.31, ease: "power2.in" }, 16.6); tl.to(cam, { roll: 0, duration: 0.4, ease: "power2.out" }, 16.91);
      pulse(14.95, 0.7); pulse(17.0, 0.55);
      // 19.75: "especially if you're shooting in 24 or 30 fps"
      const t3 = d.hud("t3", 700, 150, -330, 0), t4 = d.hud("t4", 700, 150, 330, 0);
      W.light(20.6, [], 0.78);
      d.slam(t3, 20.97, 1.2, 0.3); pulse(20.97, 0.7);
      d.slam(t4, 21.8, 1.2, 0.3); pulse(21.8, 0.7);
      tl.to({}, { duration: 0.001 }, 22.37);

      const brkp = document.getElementById("brkp"), BL = brkp.getTotalLength(); brkp.style.strokeDasharray = BL;
      d.onSync(() => { brkp.style.strokeDashoffset = BL * bk.v; });
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
