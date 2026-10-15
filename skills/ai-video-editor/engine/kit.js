// kit.js — the shot grammar on top of launch.js. Every helper here shipped in real promos and is kept generic.
// A promo = a beat grid, a director, shots.
//
//   const g = beatGrid(0.48384);                       // seconds per beat, from tools/beats.py
//   const d = director(stage, tl);
//   d.slam(d.hud("title", 1000, 260, 0, -120), g.cut(g.B(1)));
//   await d.bind();                                    // then: window.__timelines["main"] = tl
import { htmlPanel, imagePanel, bindToHyperFrames, THREE } from "./launch.js";

// ── time ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
// B(n) = bar n's downbeat, b(n) = n beats, from the promo's t = 0 (start the music so that its drop is a bar line).
// cut(t): a hard cut half-way between two frames, so no frame's motion-blur shutter straddles it (no blended frame).
export function beatGrid(beat, fps = 30) {
  return {
    BEAT: beat, BAR: 4 * beat, FPS: fps,
    B: (n) => n * 4 * beat,
    b: (n) => n * beat,
    cut: (t) => (Math.round(t * fps - 0.5) + 0.5) / fps,
  };
}

// ── layout ───────────────────────────────────────────────────────────────────────────────────────────────────────────
// Shrink each headline until its TEXT fits its box. Measure the text: scrollWidth is never below clientWidth, and
// comparing those two shrank every headline to the floor (10-06). Run after document.fonts.ready.
export function fitText(selector = ".fit", { margin = 0.94, step = 4, min = 24 } = {}) {
  for (const el of document.querySelectorAll(selector)) {
    el.style.whiteSpace = "nowrap";
    const span = document.createElement("span");
    while (el.firstChild) span.appendChild(el.firstChild);
    el.appendChild(span);
    let fs = parseFloat(getComputedStyle(el).fontSize);
    while (span.getBoundingClientRect().width > el.getBoundingClientRect().width * margin && fs > min) {
      fs -= step; el.style.fontSize = fs + "px";
    }
  }
}

// Build <canvas layoutsubtree> panels from code (cards from data). Returns { canvas, el } for htmlPanel.
export function makePanelDom(root, html, w, h, { scale = 2, className = "" } = {}) {
  const canvas = document.createElement("canvas");
  canvas.setAttribute("layoutsubtree", "");
  canvas.width = Math.round(w * scale); canvas.height = Math.round(h * scale);
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  const el = document.createElement("div");
  if (className) el.className = className;
  el.innerHTML = html;
  canvas.appendChild(el); root.appendChild(canvas);
  return { canvas, el };
}

// ── discrete state ───────────────────────────────────────────────────────────────────────────────────────────────────
// Which card is face up, which tile is lit: a time-ordered schedule read in sync(ts). Not GSAP — tl.set turned the
// string "5" into the number 5 and an array may be tweened element by element (10-06).
export function schedule(initial = null) {
  const ev = [];
  return {
    at(t, v) { ev.push([t, v]); ev.sort((a, b) => a[0] - b[0]); return this; },
    get(ts) { let v = initial; for (const [t0, x] of ev) { if (t0 <= ts + 1e-6) v = x; else break; } return v; },
  };
}

// ── the director ─────────────────────────────────────────────────────────────────────────────────────────────────────
export function director(stage, tl) {
  const cam = stage.cam, syncs = [];
  const D = stage.unitDistance();
  const d = {
    cam, tl, stage, D,
    onSync(fn) { syncs.push(fn); return fn; },
    sync(ts) { for (const f of syncs) f(ts); },
    async bind() { await bindToHyperFrames(stage, tl, d.sync); },

    // a panel from <canvas id="c-ID" layoutsubtree><div id="ID">…</div></canvas>; o: radius, shadow, live, sheen, scale
    panel(id, w, h, o = {}) {
      return htmlPanel(stage, { canvas: document.getElementById("c-" + id), el: document.getElementById(id), w, h, ...o });
    },
    // the same, pinned to the camera: x, y in px from the frame centre (y down). Sharp through every move. Hidden.
    hud(id, w, h, x = 0, y = 0, o = {}) {
      const p = d.panel(id, w, h, o); stage.hud(p, { x, y, dist: 0.5 }); p.state.opacity = 0; return p;
    },
    image(img, w, h, o = {}) { return imagePanel(stage, { img, w, h, ...o }); },
    // a panel from DOM built in code (makePanelDom → { canvas, el })
    panelEl({ canvas, el }, w, h, o = {}) { return htmlPanel(stage, { canvas, el, w, h, ...o }); },
    at(p, x, y, z = 0) { p.group.position.set(x, y, z); return p; },

    // entrances / exits. px values are screen px for HUD panels and CSS px for world panels.
    slam(p, t, from = 1.2, dur = 0.22) {
      tl.set(p.state, { opacity: 1 }, t);
      const sx = p.group.scale.x, sy = p.group.scale.y;
      tl.fromTo(p.group.scale, { x: sx * from, y: sy * from }, { x: sx, y: sy, duration: dur, ease: "expo.out", immediateRender: false }, t);
    },
    rise(p, t, { dur = 0.35, dy = 30 } = {}) {
      const y0 = p.group.position.y, k = p.group.scale.y / 1000;
      tl.to(p.state, { opacity: 1, duration: dur * 0.7, ease: "power1.out" }, t);
      tl.fromTo(p.group.position, { y: y0 - dy * k }, { y: y0, duration: dur, ease: "power3.out", immediateRender: false }, t);
    },
    fade(p, t, to = 1, dur = 0.3) { tl.to(p.state, { opacity: to, duration: dur, ease: "power1.inOut" }, t); },
    out(ps, t, dur = 0) { for (const p of [].concat(ps)) dur ? tl.to(p.state, { opacity: 0, duration: dur, ease: "none" }, t) : tl.set(p.state, { opacity: 0 }, t); },

    // a white (or any) flash, in DISPLAY space: v = how far toward white the frame goes
    flash(t, v = 0.3, dur = 0.24) {
      tl.set(stage.presentMat.uniforms.flash, { value: v }, t);
      tl.to(stage.presentMat.uniforms.flash, { value: 0, duration: dur, ease: "power2.out" }, t + 1 / 30);
    },

    // camera. A framing of a world point: distance dist, the point shown sy px below and sx px right of the centre.
    frame(x, y, dist, sy = 0, z = 0, sx = 0) {
      const k = dist / (1000 * D), tx = x - sx * k, ty = y + sy * k;
      return { x: tx, y: ty, z: z + dist, tx, ty, tz: z };
    },
    cutTo(t, to) { tl.set(cam, { roll: 0, focus: -1, aperture: 1, ...to }, t); },
    move(t, to, dur, ease = "power2.inOut") { tl.to(cam, { ...to, duration: dur, ease }, t); },
    // a whip pan centred on t: travel + roll, then settle. Keep camera tweens from overlapping (GSAP: last one wins).
    whip(t, to, { roll = 0.035, dur = 0.36, lead = 0.2 } = {}) {
      const W0 = t - lead;
      tl.to(cam, { ...to, roll, duration: dur, ease: "power3.inOut" }, W0);
      tl.to(cam, { roll: 0, duration: 0.35, ease: "power2.out" }, W0 + dur);
      return W0 + dur;
    },
    // a zoom punch on a cut: start `by` closer, ease back over dur
    punch(t, base, { by = 0.12, dur = 0.3, roll = 0.012 } = {}) {
      tl.set(cam, { ...base, z: base.z - by, roll }, t);
      tl.to(cam, { z: base.z + 0.02, roll: 0, duration: dur, ease: "power2.out" }, t + 0.001);
    },
    // rack focus (focus = distance from the camera; ≤ 0 = auto on the target)
    rack(t, from, to, dur = 0.35) { tl.set(cam, { focus: from }, t - 0.01); tl.to(cam, { focus: to, duration: dur, ease: "power2.inOut" }, t); },

    // live words: ids revealed at times (opacity + rise), written into the DOM each frame — the panel must be live
    words(ids, times, { rise = 60, dur = 0.26 } = {}) {
      const ws = ids.map((id) => ({ el: document.getElementById(id), v: 0 }));
      ws.forEach((w, i) => tl.to(w, { v: 1, duration: dur, ease: "power3.out" }, times[i]));
      d.onSync(() => { for (const w of ws) { w.el.style.opacity = w.v; w.el.style.transform = `translateY(${(1 - w.v) * rise}px)`; } });
      return ws;
    },
    // a highlighter sweep behind inline text (CSS: background linear-gradient no-repeat, box-decoration-break: clone)
    highlight(el, t, { dur = 0.4, height = "46%" } = {}) {
      const h = { v: 0 };
      tl.to(h, { v: 1, duration: dur, ease: "power2.inOut" }, t);
      d.onSync(() => { el.style.backgroundSize = `${h.v * 100}% ${height}`; });
      return h;
    },
    // typing: el.textContent = text up to n characters between t0 and t1 (newlines → <br>)
    type(el, text, t0, t1) {
      const s = { n: 0 };
      tl.to(s, { n: text.length, duration: t1 - t0, ease: "none" }, t0);
      d.onSync(() => { el.innerHTML = text.slice(0, Math.floor(s.n)).replace(/\n/g, "<br/>"); });
      return s;
    },
    // a button press: scale dip + spring back; returns the tween target {press} for the sync to style
    press(t) {
      const s = { press: 0, ripple: 0 };
      tl.to(s, { press: 1, duration: 0.07, ease: "power2.in" }, t - 0.07);
      tl.to(s, { press: 0, duration: 0.3, ease: "back.out(3)" }, t);
      tl.fromTo(s, { ripple: 0 }, { ripple: 1, duration: 0.55, ease: "power2.out", immediateRender: false }, t - 0.03);
      return s;
    },
  };
  return d;
}

// ── shots ────────────────────────────────────────────────────────────────────────────────────────────────────────────
// A WALL of images (thumbnails, screenshots, posters): cols × rows tiles in a group, a spotlight (lit ids stay full,
// the rest dim — perceptually), and a framing helper. 3 × 9 tiles of 16:9 with 0.04 gaps is itself a 9:16 rectangle.
export function wall(d, imgs, { cols, rows, w = 640, h = 360, gapX = 40, gapY = 40, radius = 16, order = null, dim = 0.72 } = {}) {
  const group = new THREE.Group(); d.stage.scene.add(group);
  const sx = (w + gapX) / 1000, sy = (h + gapY) / 1000;
  const tiles = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const k = order ? order[r * cols + c] : r * cols + c;
    if (k == null || !imgs[k]) continue;
    const p = d.image(imgs[k], w, h, { radius, sheen: true });
    group.add(p.group);
    const x = (c - (cols - 1) / 2) * sx, y = ((rows - 1) / 2 - r) * sy;
    p.group.position.set(x, y, 0);
    tiles.push({ p, k, r, c, x, y });
  }
  const look = { dim }, lit = schedule(new Set());
  const W = {
    group, tiles, look,
    tile: (k) => tiles.find((T) => T.k === k),
    light(t, ks, dimTo) { lit.at(t, new Set(ks)); if (dimTo != null) d.tl.to(look, { dim: dimTo, duration: 0.2, ease: "power1.out" }, t); },
    frameOn(k, dist, sy = 0, sx = 0) { const T = W.tile(k); return d.frame(T.x, T.y, dist, sy, 0, sx); },
  };
  d.onSync((ts) => { const on = lit.get(ts); for (const T of tiles) { T.p.state.dim = on.has(T.k) ? 0 : look.dim; T.p.sync(); } });
  return W;
}

// A BURST: items ({p, x, y}) fly from one point to their places, nearest first, a few ms apart — a deck opening.
export function burst(d, items, t, { from = [0, 0], stagger = 0.012, dur = 0.85, spin = 0.22 } = {}) {
  const order = [...items].sort((a, b) => Math.hypot(a.x - from[0], a.y - from[1]) - Math.hypot(b.x - from[0], b.y - from[1]));
  order.forEach((C, j) => {
    const tj = t + j * stagger;
    d.tl.fromTo(C.p.group.position, { x: from[0], y: from[1], z: -0.02 * j }, { x: C.x, y: C.y, z: 0, duration: dur, ease: "expo.out", immediateRender: false }, tj);
    d.tl.fromTo(C.p.group.rotation, { z: spin * (j % 2 ? 1 : -1) }, { z: 0, duration: dur + 0.05, ease: "expo.out", immediateRender: false }, tj);
  });
}

// ── NEON NOIR (2026-10-07) ────────────────────────────────────────────────────────────────────────────────────────────
// The edge light — "neon on the sides" — and the ONE place its strength lives. Viewers' notes on stronger settings: a 0.17
// base with hits to 0.5–1.3 "took over a little bit too much"; 0.06/0.11 with hits to 0.28 was "still way too strong, and it
// covers a lot of the screen". So: a whisper — 0.015, a band 0.045 of the width, and a hit can never pass `peak` (0.06).
//   const look = noir(stage, tl);  look.pulse(t);  look.pulse(t, 0.5)   // k = share of the allowed hit, 0..1
export function noir(stage, tl, { base = 0.015, width = 0.045, peak = 0.06, color = "#ff1e3c" } = {}) {
  const U = stage.presentMat.uniforms;
  U.edge.value = base; U.edgeWidth.value = width; U.edgeColor.value.set(color);
  const pulse = (t, k = 1) => {
    tl.to(U.edge, { value: base + (peak - base) * Math.max(0, Math.min(1, k)), duration: 0.06 }, t);
    tl.to(U.edge, { value: base, duration: 0.6, ease: "power2.out" }, t + 0.07);
  };
  return { pulse, base, peak, U };
}
