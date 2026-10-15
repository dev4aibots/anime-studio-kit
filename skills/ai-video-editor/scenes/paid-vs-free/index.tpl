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
      .pill { display: flex; align-items: center; justify-content: center; gap: 22px; border-radius: 60px; background: #141417; border: 2px solid #2c2c32;
              font-family: Geist, sans-serif; font-weight: 700; font-size: 52px; letter-spacing: -0.03em; color: #fafafa; white-space: nowrap; }
      .pill svg { width: 58px; height: 58px; flex: none; }
      .pill .dot { width: 22px; height: 22px; border-radius: 50%; background: #8a8a93; flex: none; }
      .tag { display: flex; align-items: center; justify-content: center; border-radius: 40px; border: 3px solid #ff2440; background: #0b0b0d;
             font-family: Geist, sans-serif; font-weight: 800; font-size: 48px; letter-spacing: -0.02em; color: #fafafa; white-space: nowrap; }
      .cap { display: flex; align-items: center; justify-content: center; font-family: Geist, sans-serif; font-weight: 700; font-size: 46px;
             letter-spacing: -0.02em; color: #ff2a48; white-space: nowrap; }
      .big { display: flex; align-items: center; justify-content: center; font-family: Geist, sans-serif; font-weight: 800; font-size: 330px;
             letter-spacing: -0.06em; color: #fafafa; line-height: 1; white-space: nowrap; text-shadow: 0 10px 50px rgba(0,0,0,0.8); }
      .big sup { font-size: 170px; vertical-align: 0.95em; margin-right: 10px; }
      .halo { display: flex; align-items: center; justify-content: center; font-family: Geist, sans-serif; font-weight: 800; font-size: 330px;
              letter-spacing: -0.06em; color: transparent; line-height: 1; white-space: nowrap;
              text-shadow: 0 0 30px rgba(255,40,70,0.9), 0 0 80px rgba(255,30,60,0.6), 0 0 140px rgba(255,30,60,0.35); }
      .halo sup { font-size: 170px; vertical-align: 0.95em; margin-right: 10px; }
      .sub { display: flex; align-items: center; justify-content: center; font-family: Roboto, sans-serif; font-weight: 500; font-size: 50px; color: #c9c9d0; white-space: nowrap; }
      .sub b { color: #fafafa; font-weight: 500; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="16.0" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
      <canvas id="c-pC" layoutsubtree width="920" height="240" style="width:460px;height:120px"><div id="pC" class="pill"><svg viewBox="0 0 24 24"><path fill="#D97757" d="M4.709 15.955l4.72-2.647.08-.23-.08-.128H9.2l-.79-.048-2.698-.073-2.339-.097-2.266-.122-.571-.121L0 11.784l.055-.352.48-.321.686.06 1.52.103 2.278.158 1.652.097 2.449.255h.389l.055-.157-.134-.098-.103-.097-2.358-1.596-2.552-1.688-1.336-.972-.724-.491-.364-.462-.158-1.008.656-.722.881.06.225.061.893.686 1.908 1.476 2.491 1.833.365.304.145-.103.019-.073-.164-.274-1.355-2.446-1.446-2.49-.644-1.032-.17-.619a2.97 2.97 0 01-.104-.729L6.283.134 6.696 0l.996.134.42.364.62 1.414 1.002 2.229 1.555 3.03.456.898.243.832.091.255h.158V9.01l.128-1.706.237-2.095.23-2.695.08-.76.376-.91.747-.492.584.28.48.685-.067.444-.286 1.851-.559 2.903-.364 1.942h.212l.243-.242.985-1.306 1.652-2.064.73-.82.85-.904.547-.431h1.033l.76 1.129-.34 1.166-1.064 1.347-.881 1.142-1.264 1.7-.79 1.36.073.11.188-.02 2.856-.606 1.543-.28 1.841-.315.833.388.091.395-.328.807-1.969.486-2.309.462-3.439.813-.042.03.049.061 1.549.146.662.036h1.622l3.02.225.79.522.474.638-.079.485-1.215.62-1.64-.389-3.829-.91-1.312-.329h-.182v.11l1.093 1.068 2.006 1.81 2.509 2.33.127.578-.322.455-.34-.049-2.205-1.657-.851-.747-1.926-1.62h-.128v.17l.444.649 2.345 3.521.122 1.08-.17.353-.608.213-.668-.122-1.374-1.925-1.415-2.167-1.143-1.943-.14.08-.674 7.254-.316.37-.729.28-.607-.461-.322-.747.322-1.476.389-1.924.315-1.53.286-1.9.17-.632-.012-.042-.14.018-1.434 1.967-2.18 2.945-1.726 1.845-.414.164-.717-.37.067-.662.401-.589 2.388-3.036 1.44-1.882.93-1.086-.006-.158h-.055L4.132 18.56l-1.13.146-.487-.456.061-.746.231-.243 1.908-1.312-.006.006z"/></svg>Claude</div></canvas>
      <canvas id="c-pH" layoutsubtree width="1000" height="240" style="width:500px;height:120px"><div id="pH" class="pill"><i class="dot"></i>Image tool</div></canvas>
      <canvas id="c-pA" layoutsubtree width="1080" height="240" style="width:540px;height:120px"><div id="pA" class="pill"><i class="dot"></i>After Effects</div></canvas>
      <canvas id="c-ln" layoutsubtree width="3600" height="120" style="width:1800px;height:60px"><svg id="ln" width="1800" height="60" viewBox="0 0 1800 60"><path id="lnp" d="M 20 30 H 1780" stroke="#ff2440" stroke-width="5" stroke-linecap="round" fill="none"/></svg></canvas>
      <canvas id="c-tF" layoutsubtree width="440" height="180" style="width:220px;height:90px"><div id="tF" class="tag">free</div></canvas>
      <canvas id="c-cP" layoutsubtree width="1200" height="140" style="width:600px;height:70px"><div id="cP" class="cap">you still have to pay</div></canvas>
      <canvas id="c-z" layoutsubtree width="1800" height="800" style="width:900px;height:400px"><div id="z" class="big"><sup>$</sup>0</div></canvas>
      <canvas id="c-zh" layoutsubtree width="900" height="400" style="width:900px;height:400px"><div id="zh" class="halo"><sup>$</sup>0</div></canvas>
      <canvas id="c-s1" layoutsubtree width="2800" height="160" style="width:1400px;height:80px"><div id="s1" class="sub">everything I'm showing you here</div></canvas>
      <canvas id="c-s2" layoutsubtree width="2800" height="160" style="width:1400px;height:80px"><div id="s2" class="sub">your computer or laptop&nbsp;<b>and Claude</b></div></canvas>
    </div>
    <script type="module">
      import { Stage, ground, reflectiveFloor, THREE } from "./assets/vendor/launch.js";
      import { director, noir } from "./assets/vendor/kit.js";
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
      ground(stage, { colorA: "#050506", colorB: "#050506", dots: 0, size: 60, z: -6 });
      const FLOOR_Y = -0.32;
      await reflectiveFloor(stage, { y: FLOOR_Y, size: 30, color: "#26262c" });
      const tl = gsap.timeline({ paused: true });
      const d = director(stage, tl), { cam } = d;
      const U = stage.presentMat.uniforms; const look = noir(stage, tl);   // NEON NOIR edge light: subtle, one place (kit.js)
      const pulse = (t, k = 0.5) => look.pulse(t, k);

      // the paid route: Claude → (an image tool) → After Effects, three glass pills joined by a neon line
      const G = new THREE.Group(); stage.scene.add(G);
      const pC = d.panel("pC", 460, 120, { radius: 60, shadow: { blur: 40, y: 22, opacity: 0.6, color: "#000" } });
      const pH = d.panel("pH", 500, 120, { radius: 60, shadow: { blur: 40, y: 22, opacity: 0.6, color: "#000" } });
      const pA = d.panel("pA", 540, 120, { radius: 60, shadow: { blur: 40, y: 22, opacity: 0.6, color: "#000" } });
      const ln = d.panel("ln", 1800, 60, { live: true }); ln.state.glow = 2.2;
      const tF = d.panel("tF", 220, 90, { radius: 45 }), cP = d.panel("cP", 600, 70);
      for (const p of [pC, pH, pA, ln, tF, cP]) { G.add(p.group); p.state.opacity = 0; }
      pC.group.position.set(-0.78, 0, 0.02); pH.group.position.set(0, 0, 0.02); pA.group.position.set(0.8, 0, 0.02);
      ln.group.position.set(0, 0, -0.005); tF.group.position.set(0, 0.15, 0.04); cP.group.position.set(0.8, -0.13, 0.03);
      tF.ol = 0; tF.state.glow = 0;
      G.position.set(0, 0.05, 0); G.rotation.set(-0.06, -0.12, 0);
      Object.assign(cam, { x: -0.55, y: 0.22, z: 1.75, tx: -0.55, ty: 0.03, tz: 0, roll: 0.01, focus: -1, aperture: 0.6 });
      const draw = { v: 1 };
      // 0.40 "plug Claude"
      tl.set(pC.state, { opacity: 1 }, 0.38); SF(pC.group.position, { y: -0.08, z: -0.1 }, { y: 0, z: 0.02 }, 0.38, "ui", 0.8); pulse(0.38, 0.45);
      // 1.90 "into After Effects" — the camera pans along the line as it draws to AE
      tl.to(draw, { v: 0.55, duration: 1.2, ease: "power2.inOut" }, 1.2);
      tl.set(ln.state, { opacity: 1 }, 1.2);
      tl.set(pA.state, { opacity: 1 }, 1.88); SF(pA.group.position, { y: -0.08, z: -0.1 }, { y: 0, z: 0.02 }, 1.88, "ui", 0.8); pulse(1.88, 0.45);
      tl.to(cam, { x: 0.15, tx: 0.05, z: 2.35, y: 0.25, duration: 1.6, ease: "power3.inOut" }, 1.4);
      // 3.71 "through an image tool" — the middle stop pops in on the line
      tl.to(draw, { v: 0, duration: 0.6, ease: "power2.out" }, 3.4);
      tl.set(pH.state, { opacity: 1 }, 3.85); SF(pH.group.position, { y: 0.12, z: 0.1 }, { y: 0, z: 0.02 }, 3.85, "ui", 0.7); pulse(3.85, 0.5);
      // 6.41 "the connector itself is free"
      tl.to(cam, { x: 0.0, tx: 0.0, z: 1.95, y: 0.2, duration: 1.4, ease: "power2.inOut" }, 4.9);
      tl.set(tF.state, { opacity: 1 }, 6.36); SF(tF.group.scale, { x: 1.35, y: 1.35 }, { x: 1, y: 1 }, 6.36, "snap", 0.45); pulse(6.36, 0.45);
      // 7.92 "but you still have to pay for After Effects"
      tl.to(cam, { x: 0.55, tx: 0.55, z: 1.75, y: 0.15, duration: 1.0, ease: "power2.inOut" }, 7.0);
      tl.set(cP.state, { opacity: 1 }, 7.88); SF(cP.group.position, { y: -0.17 }, { y: -0.13 }, 7.88, "heavy", 0.6); pulse(7.88, 0.6);
      tl.to(pA.state, { glow: 0.0, duration: 0.1 }, 7.88);
      // 9.42 "So mind you…" — the paid route steps back into the dark
      tl.to(G.position, { z: -1.2, y: 0.25, duration: 1.2, ease: "power3.inOut" }, 9.4);
      tl.to(cam, { x: 0, tx: 0, ty: 0.05, z: 2.6, y: 0.18, duration: 1.2, ease: "power3.inOut" }, 9.4);
      for (const p of [pC, pH, pA, ln, tF, cP]) tl.to(p.state, { dim: 0.7, duration: 0.9 }, 9.6);
      // 10.34 "everything I'm showing you here costs zero dollars" — $0, the only thing that glows
      const s1 = d.hud("s1", 1400, 80, 0, -250);
      tl.set(s1.state, { opacity: 1 }, 10.3); SF(s1.group.position, { y: s1.group.position.y - 0.02 * (0.5 / d.D) }, { y: s1.group.position.y }, 10.3, "heavy", 0.6);
      const zh = d.hud("zh", 900, 400, 0, 20), z = d.hud("z", 900, 400, 0, 20); zh.state.glow = 1.2;
      tl.set([z.state, zh.state], { opacity: 1 }, 12.3);
      for (const p of [z, zh]) SF(p.group.scale, { x: p.group.scale.x * 1.18, y: p.group.scale.y * 1.18 }, { x: p.group.scale.x, y: p.group.scale.y }, 12.3, "heavy", 0.9);
      SF(zh.state, { glow: 2.2 }, { glow: 0.9 }, 12.3, "heavy", 1.0);
      d.flash(12.3, 0.08, 0.2); pulse(12.3, 0.9);
      tl.to(s1.state, { opacity: 0, duration: 0.25 }, 13.5);
      // 13.0 "All you need is your computer or laptop and Claude"
      const s2 = d.hud("s2", 1400, 80, 0, 300);
      tl.set(s2.state, { opacity: 1 }, 14.05); SF(s2.group.position, { y: s2.group.position.y + 0.02 * (0.5 / d.D) }, { y: s2.group.position.y }, 14.05, "heavy", 0.6);
      tl.to(cam, { z: 2.45, duration: 2.7, ease: "none" }, 12.3);
      tl.to({}, { duration: 0.001 }, 16.0);
      const lnp = document.getElementById("lnp"), L = lnp.getTotalLength(); lnp.style.strokeDasharray = L;
      d.onSync(() => { lnp.style.strokeDashoffset = L * draw.v; });
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
