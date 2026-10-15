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
      .tag { text-transform: var(--case); display: flex; align-items: center; justify-content: center; gap: 22px; border-radius: 60px; background: var(--surf); box-shadow: var(--glass-shadow);
             border: 2px solid var(--line); font-family: Geist, sans-serif; font-weight: 700; font-size: 52px;
             letter-spacing: -0.02em; color: var(--ink); white-space: nowrap; }
      .tag i { width: 20px; height: 20px; border-radius: 50%; background: var(--accent); flex: none; }
      .card { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 22px; padding: 40px 46px;
              text-align: center; font-family: Geist, sans-serif; color: var(--ink); }
      .card .w { text-transform: var(--case); display: block; font-weight: 700; font-size: 64px; letter-spacing: -0.03em; line-height: 1.04; }
      .head { text-transform: var(--case); display: flex; align-items: center; justify-content: center; font-family: var(--display); font-weight: var(--display-w);
              font-size: 92px; letter-spacing: var(--display-ls); color: var(--ink); white-space: nowrap; }
      .head b { color: var(--accent-t); }
    </style>
  </head>
  <body>
    <!-- VERSUS CARD: two sides (A left, B right), the speaker's words in each, landing on the voice; the side the verdict
         goes to lights up (accent underline, a lift) and the other steps back. A tie lights both. new_card.py fills CFG. -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="/*DUR*/" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
    </div>
    <script type="module">
      import { world, dom, ready, fit, $, THREE, shadow } from "./assets/gfx.js";
      const CFG = /*CFG*/;   // { dur, head: {text, accent, t} | null, left: {tag, tagW, lines: [{text, t}]}, right: {…}, win, t_win }
      const side = (k, s) => {
        const lines = s.lines.map((l, j) => `<span class="w" id="${k}w${j}">${l.text}</span>`).join("");
        return { card: dom(`${k}card`, 790, 460, lines, { cls: "glass card" }), tag: dom(`${k}tag`, s.tagW, 120, `<i></i>${s.tag}`, { cls: "tag" }) };
      };
      const L = side("l", CFG.left), R = side("r", CFG.right);
      const headR = CFG.head ? dom("head", 1700, 130, `<span id="ht">${CFG.head.accent ? CFG.head.text.replace(CFG.head.accent, `<b>${CFG.head.accent}</b>`) : CFG.head.text}</span>`, { cls: "head" }) : null;
      await ready();
      ["l", "r"].forEach((k) => (k === "l" ? CFG.left : CFG.right).lines.forEach((_, j) => fit($(`${k}w${j}`), 710, { min: 34, step: 2 })));
      if (headR) fit($("ht"), 1600, { min: 48, step: 4 });
      const W = await world({ floorY: -0.62, pool: 0.16, poolAt: [0, -0.7] });
      const { tl, D, view, aim, breathe, P, enter, neon, reveal, stage } = W;
      const X = 0.44, Y = -0.04;   // room for the winner's 5 % lift inside the frame
      const mk = (S, x, ry) => {
        const c = P(S.card, { live: true, radius: 30, shadow: shadow(70, 34) });
        const t = P(S.tag, { order: 6 });
        c.group.position.set(x, Y, 0); c.group.rotation.y = ry; t.group.position.set(x, Y + 0.235 + 0.09, 0.03);
        return { c, t };
      };
      const l = mk(L, -X, 0.1), r = mk(R, X, -0.1);
      enter(l.c, 0.05, { from: { z: -0.5, y: -0.06, ry: 0.3 }, kind: "ui", dur: 0.85 });
      enter(r.c, 0.17, { from: { z: -0.5, y: -0.06, ry: -0.3 }, kind: "ui", dur: 0.85 });
      enter(l.t, 0.4, { from: { y: 0.05 }, kind: "heavy", dur: 0.55 });
      enter(r.t, 0.5, { from: { y: 0.05 }, kind: "heavy", dur: 0.55 });
      reveal(CFG.left.lines.map((_, j) => $(`lw${j}`)), CFG.left.lines.map((x) => x.t));
      reveal(CFG.right.lines.map((_, j) => $(`rw${j}`)), CFG.right.lines.map((x) => x.t));
      breathe(0.2, 0.4);
      if (headR) {
        const h = P(headR); h.group.position.set(0, Y + 0.235 + 0.27, 0.05);
        enter(h, CFG.head.t, { from: { z: -0.4, y: 0.06 }, kind: "heavy", dur: 0.6 });
      }
      if (CFG.win) {
        const lit = CFG.win === "tie" ? [l, r] : [CFG.win === "left" ? l : r];
        const dim = CFG.win === "tie" ? [] : [CFG.win === "left" ? r : l];
        lit.forEach((s, k) => {
          const u = neon(`win${k}`, 720, { parent: s.c.group, x: 0, y: -0.235 - 0.03, z: 0.01, h: 10, glow: 2.5 });
          u.draw(CFG.t_win, 0.4, "power3.out");
          tl.fromTo(s.c.group.scale, { x: 1, y: 1 }, { x: 1.05, y: 1.05, duration: 0.5, ease: "back.out(2)", immediateRender: false }, CFG.t_win);
        });
        dim.forEach((s) => { tl.to(s.c.state, { dim: 0.55, duration: 0.4 }, CFG.t_win); tl.to(s.t.state, { dim: 0.55, duration: 0.4 }, CFG.t_win); });
        breathe(CFG.t_win, 0.65);
      }
      view(0, aim(0, 0.06, 0, D * 1.16, { oy: 0.04 }), 0);
      view(0.001, aim(0, 0.06, 0, D * 1.08, { oy: 0.03 }), CFG.dur, "none");
      await W.bind(CFG.dur);
      window.__timelines["main"] = W.tl;
    </script>
  </body>
</html>
