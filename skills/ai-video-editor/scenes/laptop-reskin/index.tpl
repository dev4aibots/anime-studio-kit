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
      #ms { width: 1440px; height: 900px; overflow: hidden; position: relative; background: #000; }
      #ms img { position: absolute; left: 0; top: 0; width: 1440px; height: 900px; object-fit: cover; object-position: top; display: block; }
      .lb { font-family: Geist, sans-serif; font-weight: 800; font-size: 92px; letter-spacing: -0.045em; color: #fafafa; white-space: nowrap; display: flex; align-items: center; gap: 28px; line-height: 1; }
      .lb i { width: 18px; height: 18px; border-radius: 50%; background: #ff2440; box-shadow: 0 0 0 8px rgba(255,36,64,0.2); flex: none; }
      .lt { font-family: Fraunces, serif; font-weight: 600; font-size: 104px; letter-spacing: -0.035em; color: #1a1a1a; white-space: nowrap; display: flex; align-items: center; line-height: 1; }
      .lt em { color: #c2553d; font-style: italic; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="12.1" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
      <canvas id="c-ms" layoutsubtree width="2880" height="1800" style="width:1440px;height:900px"><div id="ms"><img id="pl" src="assets/pl.png"/><img id="yt" src="assets/yt.png"/></div></canvas>
      <canvas id="c-l1" layoutsubtree width="1800" height="280" style="width:900px;height:140px"><div id="l1" class="lb"><i></i><span>their website</span></div></canvas>
      <canvas id="c-l2" layoutsubtree width="2000" height="280" style="width:1000px;height:140px"><div id="l2" class="lb"><i></i><span>their social media page</span></div></canvas>
      <canvas id="c-l3" layoutsubtree width="2000" height="300" style="width:1000px;height:150px"><div id="l3" class="lt"><span>their business <em>theme.</em></span></div></canvas>
    </div>
    <script type="module">
      import { Stage, ground, loadDevice, reflectiveFloor, THREE } from "./assets/vendor/launch.js";
      import { director, noir } from "./assets/vendor/kit.js";
      await document.fonts.ready;
      await Promise.all([...document.images].map((im) => (im.complete ? 0 : new Promise((r) => (im.onload = im.onerror = r)))));
      const spring = (t, k, d) => { if (t <= 0) return 0; const w0 = Math.sqrt(k), z = d / (2 * w0);
        if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
        return 1 - Math.exp(-w0 * t) * (1 + w0 * t); };
      const SPR = { ui: [300, 24], card: [190, 25], heavy: [130, 23], snap: [420, 32] };
      const sp = (kind, dur) => { const [k, d] = SPR[kind]; const end = spring(dur, k, d); return (p) => spring(p * dur, k, d) / end; };
      const SF = (tg, f, v, t, kind = "card", dur = 0.8) => tl.fromTo(tg, f, { ...v, duration: dur, ease: sp(kind, dur), immediateRender: false }, t);

      const stage = new Stage({ canvas: document.getElementById("stage"), width: 1920, height: 1080, background: "#040405", samples: 8,
                                dof: { strength: 26, max: 34 }, grain: 0.03, vignette: 0.38, bloom: { strength: 1.0, threshold: 1.0 } });
      const gnd = ground(stage, { colorA: "#050506", colorB: "#050506", dots: 0, size: 60, z: -6 });
      await stage.studio({ env: 0.8, key: 2.0, fill: 0.55, rim: 2.6, warm: "#ffe6e8", cool: "#ffc9d1" });
      const FLOOR_Y = -0.4;
      const floor = await reflectiveFloor(stage, { y: FLOOR_Y, size: 30, color: "#2a2a30" });
      const tl = gsap.timeline({ paused: true });
      const d = director(stage, tl), { cam } = d;
      const U = stage.presentMat.uniforms; const look = noir(stage, tl);   // NEON NOIR edge light: subtle, one place (kit.js)
      const pulse = (t, k = 0.5) => look.pulse(t, k);

      // the laptop: a real 3D model, its display a live page (their website ↔ their social page)
      const ms = d.panel("ms", 1440, 900, { live: true, scale: 2 });
      const mac = await loadDevice(stage, { url: "assets/vendor/models/macbook.glb", kind: "laptop", screen: ms, size: 1.25 });
      const bb = new THREE.Box3().setFromObject(mac.group);
      mac.group.position.set(0.0, FLOOR_Y - bb.min.y, 0);
      mac.group.rotation.y = -0.95;
      const dispMat = mac.display.material; dispMat.color.setRGB(0, 0, 0);
      const C = { x: 0, y: (bb.max.y + bb.min.y) / 2 + (FLOOR_Y - bb.min.y) * 0 , z: 0 };          // the laptop's middle

      // the camera: the laptop sits right of centre, the words on the left
      Object.assign(cam, { x: 0.25, y: 0.45, z: 3.1, tx: -0.42, ty: 0.02, tz: 0, roll: 0, focus: -1, aperture: 0.6 });
      tl.to(cam, { x: 0.05, y: 0.36, z: 2.75, duration: 2.6, ease: "power2.out" }, 0);
      tl.to(mac.group.rotation, { y: -0.52, duration: 2.6, ease: "power2.out" }, 0);
      // 2.3 "their website" — the screen powers on with the real site
      tl.to(dispMat.color, { r: 1.6, g: 1.6, b: 1.6, duration: 0.07, ease: "power2.in" }, 2.2);
      tl.to(dispMat.color, { r: 1, g: 1, b: 1, duration: 0.45, ease: "power2.out" }, 2.28);
      pulse(2.25, 0.45);
      const LX = -960 + 120 + 450;
      const l1 = d.hud("l1", 900, 140, LX, -330), l2 = d.hud("l2", 1000, 140, -960 + 120 + 500, -330), l3 = d.hud("l3", 1000, 150, -960 + 120 + 500, -330);
      const k = 0.5 / d.D;
      const tIn = (p, t) => { const x0 = p.group.position.x; tl.set(p.state, { opacity: 1 }, t); SF(p.group.position, { x: x0 - 0.028 * k }, { x: x0 }, t, "heavy", 0.7); };
      const tOut = (p, t) => tl.to(p.state, { opacity: 0, duration: 0.2, ease: "power1.in" }, t);
      tIn(l1, 2.45);
      // 3.45 "or their social media page" — the screen swipes to the channel page
      const sw = { y: 0, back: 0 };
      tOut(l1, 3.3);
      tl.to(sw, { y: 1, duration: 0.55, ease: "power3.inOut" }, 3.35);
      tIn(l2, 3.75); pulse(3.6, 0.4);
      tOut(l2, 5.05);
      // 5.0 "on the 3D render" — an orbit round the laptop: it's a real object
      tl.to(cam, { x: -1.65, y: 0.62, z: 1.7, tx: 0.0, ty: -0.02, duration: 2.7, ease: "power2.inOut" }, 4.95);
      // 7.75 "customize the experience" — back to a hero angle, their site back on the screen
      tl.to(cam, { x: 0.15, y: 0.34, z: 2.6, tx: -0.4, ty: 0.02, duration: 1.6, ease: "power3.inOut" }, 7.6);
      tl.to(sw, { y: 0, duration: 0.55, ease: "power3.inOut" }, 7.95);
      // 10.4 "to match their business theme" — the whole world takes their colours: paper, ink, terracotta
      const RS = 10.35, PAPER = new THREE.Color("#f7f4ee"), FLOORC = new THREE.Color("#e3dccd"), TERRA = new THREE.Color("#c2553d");
      const gmat = gnd && (gnd.material || (gnd.mesh && gnd.mesh.material));
      const skin = { v: 0 };
      tl.to(skin, { v: 1, duration: 0.9, ease: "power2.inOut" }, RS);
      tl.to(U.edge, { value: 0.0, duration: 0.6, ease: "power2.inOut" }, RS);
      tl.to(U.vignette, { value: 0.12, duration: 0.9, ease: "power2.inOut" }, RS);
      tl.to(cam, { z: 2.9, y: 0.4, duration: 1.75, ease: "power2.out" }, RS);
      tIn(l3, 11.2);
      tl.to({}, { duration: 0.001 }, 12.1);

      const DARK = new THREE.Color("#040405"), DFLOOR = new THREE.Color("#2a2a30"), RED = new THREE.Color("#ff1e3c");
      const ytEl = document.getElementById("yt");
      d.onSync(() => {
        ytEl.style.transform = `translateY(${(1 - sw.y) * 100}%)`;
        stage.bg.copy(DARK).lerp(PAPER, skin.v);
        if (gmat && gmat.uniforms && gmat.uniforms.a) { gmat.uniforms.a.value.copy(DARK).lerp(PAPER, skin.v); gmat.uniforms.b.value.copy(gmat.uniforms.a.value); }
        if (floor.material.uniforms && floor.material.uniforms.color) floor.material.uniforms.color.value.copy(DFLOOR).lerp(FLOORC, skin.v);
        U.edgeColor.value.copy(RED).lerp(TERRA, skin.v);
      });
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
