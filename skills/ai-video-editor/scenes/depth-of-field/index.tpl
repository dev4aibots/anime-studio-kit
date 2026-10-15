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
      .lb { font-family: Geist, sans-serif; font-weight: 800; font-size: 100px; letter-spacing: -0.045em; color: #fafafa; white-space: nowrap; display: flex; align-items: center; gap: 30px; line-height: 1; }
      .lb i { width: 18px; height: 18px; border-radius: 50%; background: #ff2440; box-shadow: 0 0 0 8px rgba(255,36,64,0.2); flex: none; }
      .lb em, .ls em, .wl em { font-style: normal; color: #ff2a48; }
      .ls { font-family: Roboto, sans-serif; font-weight: 500; font-size: 48px; color: #b9b9c0; white-space: nowrap; display: flex; align-items: center; padding-left: 48px; }
      .wl { font-family: Geist, sans-serif; font-weight: 800; font-size: 120px; letter-spacing: -0.045em; color: #fafafa; white-space: nowrap; display: flex; align-items: center; justify-content: center; line-height: 1; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="8.95" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
      <canvas id="c-lb" layoutsubtree width="1800" height="300" style="width:900px;height:150px"><div id="lb" class="lb"><i></i>depth of field</div></canvas>
      <canvas id="c-ls" layoutsubtree width="1800" height="140" style="width:900px;height:70px"><div id="ls" class="ls">how far or close an object is<em>.</em></div></canvas>
      <canvas id="c-w1" layoutsubtree width="1200" height="300" style="width:600px;height:150px"><div id="w1" class="wl">clear</div></canvas>
      <canvas id="c-w2" layoutsubtree width="1200" height="300" style="width:600px;height:150px"><div id="w2" class="wl">blurry<em>.</em></div></canvas>
    </div>
    <script type="module">
      import { Stage, ground, loadImage, reflectiveFloor, THREE } from "./assets/vendor/launch.js";
      import { director, noir } from "./assets/vendor/kit.js";
      await document.fonts.ready;
      const spring = (t, k, d) => { if (t <= 0) return 0; const w0 = Math.sqrt(k), z = d / (2 * w0);
        if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
        return 1 - Math.exp(-w0 * t) * (1 + w0 * t); };
      const SPR = { ui: [300, 24], card: [190, 25], heavy: [130, 23], snap: [420, 32] };
      const sp = (kind, dur) => { const [k, d] = SPR[kind]; const end = spring(dur, k, d); return (p) => spring(p * dur, k, d) / end; };
      const SF = (tg, f, v, t, kind = "card", dur = 0.8) => tl.fromTo(tg, f, { ...v, duration: dur, ease: sp(kind, dur), immediateRender: false }, t);

      const stage = new Stage({ canvas: document.getElementById("stage"), width: 1920, height: 1080, background: "#040405", samples: 8,
                                dof: { strength: 30, max: 40 }, grain: 0.03, vignette: 0.38, bloom: { strength: 1.1, threshold: 1.0 } });
      ground(stage, { colorA: "#050506", colorB: "#050506", dots: 0, size: 60, z: -12 });
      const FLOOR_Y = -0.4;
      await reflectiveFloor(stage, { y: FLOOR_Y, size: 30, color: "#2a2a30" });
      const tl = gsap.timeline({ paused: true });
      const d = director(stage, tl), { cam } = d;
      const U = stage.presentMat.uniforms; const look = noir(stage, tl);   // NEON NOIR edge light: subtle, one place (kit.js)
      U.depthNear.value = 1.4; U.depthFar.value = 8.6;
      const pulse = (t, k = 0.45) => look.pulse(t, k);

      // a row of real thumbnails on the mirror floor, receding diagonally: each card is solved from where it should sit
      // on screen (X px from the centre) and how far away (Z) — near and big at the left, far and small at the right
      const files = ["t05", "t09", "t01", "t08", "t02", "t04", "t22"];
      const imgs = await Promise.all(files.map((f) => loadImage(`assets/thumbs/${f}.jpg`)));
      const CAM0 = { x: 0, y: -0.05, z: 3.0 }, CAM1 = { x: 0.04, y: -0.04, z: 2.78 }, FPX = 540 / Math.tan((16 * Math.PI) / 180);
      const cards = imgs.map((img, i) => {
        const Z = 1.9 + i * 0.85, X = -430 + i * 175;
        const x = (X * Z) / FPX, z = CAM0.z - Z, y = FLOOR_Y + 0.184;
        const p = d.image(img, 640, 360, { radius: 16, shadow: { blur: 40, y: 20, opacity: 0.5, color: "#000" } });
        p.group.position.set(x, y, z); p.group.rotation.y = Math.atan2(CAM0.x - x, CAM0.z - z);
        return { p, x, y, z };
      });
      // a neon strip on the floor just behind the row, running on into the dark
      const c0 = cards[0], c6 = cards[6], L = Math.hypot(c6.x - c0.x, c6.z - c0.z), dx = (c6.x - c0.x) / L, dz = (c6.z - c0.z) / L;
      let px = -dz, pz = dx; const mx = (c0.x + c6.x) / 2, mz = (c0.z + c6.z) / 2;
      if (px * (CAM0.x - mx) + pz * (CAM0.z - mz) > 0) { px = -px; pz = -pz; }
      const stripG = new THREE.Group(); stage.scene.add(stripG);
      const strip = new THREE.Mesh(new THREE.PlaneGeometry(0.016, L + 9), new THREE.MeshBasicMaterial({ color: new THREE.Color(3.0, 0.14, 0.3), toneMapped: false }));
      strip.rotation.x = -Math.PI / 2; stripG.add(strip);
      stripG.rotation.y = Math.atan2(-dx, -dz); stripG.position.set(mx + px * 0.42 + dx * 3.6, FLOOR_Y + 0.002, mz + pz * 0.42 + dz * 3.6);

      // the camera dollies slowly toward the row; focus is a distance, racked from card to card
      Object.assign(cam, { ...CAM0, tx: 0.0, ty: -0.22, tz: 0, roll: 0, aperture: 0.9 });
      const at = (t) => ({ x: CAM0.x + (CAM1.x - CAM0.x) * t / 8.95, y: CAM0.y + (CAM1.y - CAM0.y) * t / 8.95, z: CAM0.z + (CAM1.z - CAM0.z) * t / 8.95 });
      const F = (i, t) => { const c = cards[i], q = at(t); return Math.hypot(q.x - c.x, q.y - c.y, q.z - c.z); };
      cam.focus = F(0, 0);
      tl.to(cam, { x: CAM1.x, y: CAM1.y, z: CAM1.z, tx: 0.04, duration: 8.95, ease: "none" }, 0);
      const rack = (t, i, dur = 0.45) => tl.to(cam, { focus: F(i, t + dur), duration: dur, ease: "power2.inOut" }, t);

      // 0.13 "depth of field is also a thing as well" — sharp up close, the row melts into bokeh; then a rack
      const LX = -960 + 120 + 450;
      const lb = d.hud("lb", 900, 150, LX, -392), ls = d.hud("ls", 900, 70, LX, -304);
      const k = 0.5 / d.D;
      const tIn = (p, t, kind = "heavy") => { const x0 = p.group.position.x; tl.set(p.state, { opacity: 1 }, t);
        SF(p.group.position, { x: x0 - 0.028 * k }, { x: x0 }, t, kind, 0.7); };
      tIn(lb, 0.13); pulse(0.13);
      rack(1.25, 4, 0.7);
      rack(2.3, 0, 0.45);
      // 2.93 "so depending on how far or close" — the depth pass itself: white = near, black = far
      tl.set(U.depthView, { value: 1 }, 2.85);
      tl.fromTo(U.depthSplit, { value: 0 }, { value: 1, duration: 0.65, ease: "power2.inOut", immediateRender: false }, 2.88);
      pulse(2.9, 0.5);
      tIn(ls, 4.05, "card");
      tl.to(U.depthSplit, { value: 0, duration: 0.6, ease: "power2.inOut" }, 5.0);
      tl.set(U.depthView, { value: 0 }, 5.62);
      tl.to([lb.state, ls.state], { opacity: 0, duration: 0.25 }, 5.55);
      // 5.6 "it's going to either…" — slow rack to the back; 7.85 "clear" — snap to the front; 8.65 "blurry."
      rack(5.7, 5, 1.4);
      rack(7.7, 0, 0.3);
      const w1 = d.panel("w1", 600, 150), w2 = d.panel("w2", 600, 150);
      // "clear" floats over the near card (in focus), "blurry." over a far one: the word itself is out of focus
      const W1Y = FLOOR_Y + 0.368 + 0.045 + 0.0375, W2Y = FLOOR_Y + 0.368 + 0.05 + 0.123;
      for (const [w, c, s, y] of [[w1, cards[0], 0.5, W1Y], [w2, cards[4], 1.64, W2Y]]) {
        w.group.position.set(c.x, y, c.z); w.group.rotation.y = c.p.group.rotation.y; w.group.scale.setScalar(s); w.state.opacity = 0;
      }
      tl.set(w1.state, { opacity: 1 }, 7.82); SF(w1.group.position, { y: W1Y - 0.03 }, { y: W1Y }, 7.82, "heavy", 0.6);
      tl.to(cam, { aperture: 0.5, duration: 0.3 }, 8.3);
      tl.set(w2.state, { opacity: 1 }, 8.6); SF(w2.group.position, { y: W2Y - 0.08 }, { y: W2Y }, 8.6, "heavy", 0.6);
      pulse(7.82, 0.4); pulse(8.6, 0.4);
      tl.to({}, { duration: 0.001 }, 8.95);
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
