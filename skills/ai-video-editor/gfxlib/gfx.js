// gfx.js — the shared look of every card and diagram: one room in the video's theme (Warm Cream by default, Noir on
// request), one camera rig that never stops drifting, closed-form springs, glass cards, and accent strokes that glow
// softly while the type stays crisp. Built on launch.js + kit.js (copied in by link.py). Copy this file FRESH into each
// graphic's assets/ (new_card.py, chapter_cards.py, make_icons.py and logo_clip.py do).
import { Stage, ground, reflectiveFloor, loadImage, depthMaterial, THREE } from "./vendor/launch.js";
import { director, makePanelDom, schedule } from "./vendor/kit.js";
export { THREE, loadImage, schedule };

// ── THEMES: the default look is "warmcream" (light: friendlier for retention than a near-black room); "noir" stays
// available. A graphic picks its theme with
// <html data-theme="noir"> and the video's accent (the product's colour) with <html data-accent="#D97757">; both are read at
// load, so the right fonts are in place before any text is measured. The assembler (tools/theme.py) parses the same block.
export const THEMES = /*THEMES*/{
   "noir": {
    "bg": "#050506",
    "surf": "rgba(40,40,46,0.94)",
    "surf2": "rgba(20,20,24,0.94)",
    "surf3": "rgba(12,12,15,0.94)",
    "floor": "#2a2a30",
    "ink": "#fafafa",
    "mute": "#9a9aa3",
    "line": "rgba(255,255,255,0.12)",
    "hi": "rgba(255,255,255,0.07)",
    "accent": "#ff1e3c",
    "accentT": "#ff2a48",
    "core1": "#ff7a8c",
    "core2": "#ffe2e7",
    "warm": "#fff4e8",
    "cool": "#e8f0ff",
    "pool": 0.2,
    "vignette": 0.38,
    "grain": 0.03,
    "bloom": 1.1,
    "reflect": true,
    "edge": 0.015,
    "serif": false,
    "case": "uppercase",
    "shadow": "",
    "panelShadow": {
     "color": "#000000",
     "opacity": 0.7
    },
    "contact": "0,0,0",
    "light": false
   },
   "warmcream": {
    "bg": "#F2ECE1",
    "surf": "#FFFCF7",
    "surf2": "#F7F1E7",
    "surf3": "#EAE2D3",
    "floor": "#E5DCCB",
    "ink": "#1F1B17",
    "mute": "#7A7064",
    "line": "rgba(70,45,20,0.12)",
    "hi": "rgba(255,255,255,0.75)",
    "accent": "#E0703A",
    "accentT": "#E0703A",
    "core1": "#EE9A6C",
    "core2": "#F8D3BD",
    "warm": "#fff1e2",
    "cool": "#f1ede6",
    "pool": 0,
    "vignette": 0.12,
    "grain": 0.03,
    "bloom": 0.2,
    "reflect": false,
    "edge": 0,
    "serif": true,
    "case": "none",
    "shadow": "0 22px 48px rgba(90,60,25,0.16)",
    "panelShadow": {
     "color": "#4A3218",
     "opacity": 0.34
    },
    "contact": "70,45,20",
    "light": true
   }
  }/*/THEMES*/;   // strict JSON: tools/theme.py reads this block
const _hex = (h) => { const n = parseInt(h.replace("#", "").slice(0, 6), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const _mix = (h, k) => "#" + _hex(h).map((c) => Math.round(c + (255 - c) * k).toString(16).padStart(2, "0")).join("");
export const THEME_NAME = THEMES[document.documentElement.dataset.theme] ? document.documentElement.dataset.theme : "warmcream";
export const T = Object.assign({}, THEMES[THEME_NAME] || THEMES.warmcream);
if (/^#[0-9a-f]{6}$/i.test(document.documentElement.dataset.accent || "")) {   // the video's own accent (the product's colour)
  const a = document.documentElement.dataset.accent; Object.assign(T, { accent: a, accentT: a, core1: _mix(a, 0.3), core2: _mix(a, 0.72) });
}
T.a_rgb = _hex(T.accent).join(",");
export const COL = { bg: T.bg, red: T.accent, redT: T.accentT, ink: T.ink, mute: T.mute, accent: T.accent };
// a panel's 3D drop shadow in the theme: P(el, { shadow: shadow(70, 34) }) — black at 0.7 on noir, warm brown on cream
export const shadow = (blur = 60, y = 30) => ({ blur, y, ...T.panelShadow });

// ── springs: a pure function of time. Tiny overshoot on UI ("ui"), none on type ("heavy") ──────────────────────────
export const spring = (t, k, d) => {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(k), z = d / (2 * w0);
  if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
  return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
};
export const SP = { ui: [260, 24], card: [170, 24], heavy: [120, 22], snap: [380, 30] };
export const sp = (kind, dur) => { const [k, d] = SP[kind]; const end = spring(dur, k, d); return (p) => spring(p * dur, k, d) / end; };

// ── shared CSS ────────────────────────────────────────────────────────────────────────────────────────────────────
const CSS = `
.gs{font-family:Geist,sans-serif}.rb{font-family:Roboto,sans-serif}.mono{font-family:'JetBrains Mono',monospace}
.ty{font-family:var(--display);font-weight:var(--display-w);color:var(--ink);letter-spacing:var(--display-ls);text-transform:var(--case);line-height:0.95;white-space:nowrap;display:flex;align-items:center;justify-content:center}
.lbl{font-family:var(--sans);font-weight:600;color:var(--ink);letter-spacing:-0.02em;white-space:nowrap;display:flex;align-items:center;justify-content:center}
.glass{background:linear-gradient(160deg,var(--surf) 0%,var(--surf2) 52%,var(--surf3) 100%);border:2px solid var(--line);border-radius:30px;box-shadow:var(--glass-shadow);color:var(--ink)}
.acc{color:var(--accent-t)}.mute{color:var(--mute)}
.mk{display:inline-block;width:0;height:0}
.w{display:inline-block;will-change:transform}
`;
// the theme as CSS variables — every template colours itself with these (var(--ink), var(--accent-t), var(--surf)…)
const VARS = `:root{--bg:${T.bg};--surf:${T.surf};--surf2:${T.surf2};--surf3:${T.surf3};--floor:${T.floor};--ink:${T.ink};--mute:${T.mute};
--line:${T.line};--hi:${T.hi};--accent:${T.accent};--accent-t:${T.accentT};--a-rgb:${T.a_rgb};--core1:${T.core1};--core2:${T.core2};
--glass-shadow:${T.shadow ? T.shadow + "," : ""}inset 0 2px 0 ${T.hi};--sans:Geist,sans-serif;
--display:${T.serif ? "'Instrument Serif',serif" : "Geist,sans-serif"};--display-w:${T.serif ? 400 : 800};--display-ls:${T.serif ? "-0.01em" : "-0.045em"};
--serif:var(--display);--shadow:${T.shadow || "none"};--case:${T.case}}
html,body{background:${T.bg}}`;
{ const st = document.createElement("style"); st.textContent = VARS + CSS; document.head.appendChild(st); }

// ── DOM for panels, built in code ─────────────────────────────────────────────────────────────────────────────────
// <canvas layoutsubtree width=w*scale height=h*scale><div id class style="width:w;height:h">html</div></canvas>
export function dom(id, w, h, html, { cls = "", style = "", scale = 2 } = {}) {
  const r = makePanelDom(document.getElementById("root"), html, w, h, { scale, className: cls });
  r.el.id = id;
  r.el.style.cssText = `width:${w}px;height:${h}px;${style}`;
  r.w = w; r.h = h;
  return r;
}
export async function ready() {
  await document.fonts.ready;
  await Promise.all([...document.images].map((im) => (im.complete && im.naturalWidth
    ? (im.decode ? im.decode().catch(() => {}) : 0)
    : new Promise((r) => { im.onload = im.onerror = r; }))));
  await document.fonts.ready;
}
// the rendered width of an element's text (a Range measures the text itself, not the box)
export function textWidth(el) { const r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect().width; }
// shrink el's font until its text is at most maxW px wide
export function fit(el, maxW, { min = 18, step = 2 } = {}) {
  let fs = parseFloat(getComputedStyle(el).fontSize);
  while (textWidth(el) > maxW && fs > min) { fs -= step; el.style.fontSize = fs + "px"; }
  return fs;
}
export const $ = (id) => document.getElementById(id);

const EDGE_PEAK = 0.06;   // the edge light's ceiling for any pulse (it was 0.28: too strong)

// ── the world ─────────────────────────────────────────────────────────────────────────────────────────────────────
export async function world(o = {}) {
  let { edge = T.edge, edgeWidth = 0.045, floorY = -0.46, reflect = T.reflect, floorColor = T.floor, pool = T.light ? 0 : 0.2, poolAt = [0, -0.3],
          poolSize = [2600, 900], dof = { strength: 30, max: 40 }, vignette = T.vignette, grain = T.grain, samples = 8,
          bloom = { strength: T.bloom, threshold: 1.0 } } = o;
  if (T.light) pool = 0;                                             // no coloured pool on a light floor, whatever a template asks for
  // a tag pill never clips its words: the text shrinks to the pill (a hand-set tagW once clipped "THE PREVIOUS VERSION")
  document.querySelectorAll(".tag").forEach((el) => { if (el.clientWidth) fit(el, el.clientWidth - 72, { min: 22, step: 2 }); });
  const stage = new Stage({ canvas: document.getElementById("stage"), width: 1920, height: 1080, background: COL.bg, samples, dof, grain, vignette, bloom });
  if (T.light) stage.dimTo = new THREE.Color(T.bg);                 // dim fades a panel toward the cream, not to a grey slab
  ground(stage, { colorA: COL.bg, colorB: COL.bg, dots: 0, size: 90, z: -8 });
  const tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
  const d = director(stage, tl), cam = stage.cam, D = d.D;
  const S = (target, vars, t, kind = "card", dur = 0.9) => tl.to(target, { ...vars, duration: dur, ease: sp(kind, dur) }, t);
  const SF = (target, from, to, t, kind = "card", dur = 0.9) => tl.fromTo(target, from, { ...to, duration: dur, ease: sp(kind, dur), immediateRender: false }, t);

  // neon on the sides (noir only): the present shader's edge light — a whisper: base 0.015, width 0.045 of the screen, a hit
  // never past 0.06. Stronger values (0.06–0.75) were tried and "took over" the frame.
  const U = stage.presentMat.uniforms; U.edge.value = edge; U.edgeWidth.value = edgeWidth;
  if (T.light) {   // no edge light on a light theme, even from a template that sets or tweens U.edge itself
    U.edge.value = 0; Object.defineProperty(U.edge, "value", { get: () => 0, set: () => {}, configurable: true });
    reflect = false;                                                 // no mirror: a seamless studio floor, objects get contact shadows
  }
  const mirror = reflect ? await reflectiveFloor(stage, { y: floorY, size: 40, color: floorColor }) : null;
  let poolP = null;
  if (pool) {
    const r = dom("gfxPool", poolSize[0], poolSize[1], "", { scale: 0.4, style: `background:radial-gradient(ellipse 50% 50% at 50% 50%, rgba(${T.a_rgb},0.55) 0%, rgba(${T.a_rgb},0.18) 40%, rgba(${T.a_rgb},0) 72%)` });
    poolP = d.panelEl(r, poolSize[0], poolSize[1]);
    poolP.group.rotation.x = -Math.PI / 2;
    poolP.group.position.set(poolAt[0], floorY + 0.004, poolAt[1]);
    poolP.state.glow = pool;
  }
  const base = { edge, pool };
  // breathe(t, k): k = share 0..1 of the allowed hit (EDGE_PEAK) — the same scale as kit.js noir().pulse
  const breathe = (t, k = 0.7, { up = 0.09, down = 0.85 } = {}) => {
    const peak = base.edge + (EDGE_PEAK - base.edge) * Math.max(0, Math.min(1, k));
    tl.fromTo(U.edge, { value: base.edge }, { value: peak, duration: up, ease: "power2.out", immediateRender: false }, t);
    tl.fromTo(U.edge, { value: peak }, { value: base.edge, duration: down, ease: "power2.inOut", immediateRender: false }, t + up);
    if (poolP) {
      const pk = base.pool * (1 + (peak - base.edge) * 2.2);
      tl.fromTo(poolP.state, { glow: base.pool }, { glow: pk, duration: up, ease: "power2.out", immediateRender: false }, t);
      tl.fromTo(poolP.state, { glow: pk }, { glow: base.pool, duration: down, ease: "power2.inOut", immediateRender: false }, t + up);
    }
  };

  // the camera rig: GSAP animates `rig`; the drift (a slow handheld float) is added on top every sub-frame, so the
  // camera is never locked and moves never fight the drift
  const rig = { x: 0, y: 0, z: D, tx: 0, ty: 0, tz: 0, roll: 0, focus: -1, aperture: 1 };
  const drift = { a: 1 };
  d.onSync((ts) => {
    const a = drift.a;
    cam.x = rig.x + a * (0.011 * Math.sin(ts * 0.52 + 0.4) + 0.004 * Math.sin(ts * 1.27 + 1.1));
    cam.y = rig.y + a * (0.007 * Math.sin(ts * 0.43 + 1.3) + 0.003 * Math.sin(ts * 1.09 + 2.0));
    cam.z = rig.z + a * 0.008 * Math.sin(ts * 0.31 + 0.8);
    cam.tx = rig.tx + a * 0.003 * Math.sin(ts * 0.37 + 0.2);
    cam.ty = rig.ty + a * 0.002 * Math.sin(ts * 0.29 + 1.7);
    cam.tz = rig.tz;
    cam.roll = rig.roll + a * 0.0028 * Math.sin(ts * 0.35 + 0.9);
    cam.focus = rig.focus; cam.aperture = rig.aperture;
  });
  const view = (t, to, dur = 0.8, ease = "power3.inOut") => (dur ? tl.to(rig, { ...to, duration: dur, ease }, t) : tl.set(rig, to, t));
  // a framing: look at (x, y, z) from `dist` in front, the camera offset by (ox, oy) for an oblique view
  const aim = (x, y, z, dist, { ox = 0, oy = 0 } = {}) => ({ x: x + ox, y: y + oy, z: z + dist, tx: x, ty: y, tz: z });

  // transparent panels are sorted by their centres' distance, so a thin overlay whose centre is off its card's centre
  // can be drawn before the card and vanish under it: `order` pins the draw order (higher = later = on top)
  const ordered = (p, order) => { if (order != null) { p.mesh.renderOrder = order; if (p.shadowMesh) p.shadowMesh.renderOrder = order - 0.5; } return p; };
  const P = (r, o2 = {}) => { const { order, ...rest } = o2; return ordered(d.panelEl(r, r.w, r.h, rest), order); };
  const IMG = (im, w, h, o2 = {}) => { const { order, ...rest } = o2; return ordered(d.image(im, w, h, rest), order); };

  // an entrance that is already moving: opacity snaps up over `fade` while position / rotation / scale spring home
  const enter = (p, t, { from = {}, kind = "ui", dur = 0.8, fade = 0.07, obj = null } = {}) => {
    const g = obj || p.group;
    const P0 = { x: g.position.x, y: g.position.y, z: g.position.z }, R0 = { x: g.rotation.x, y: g.rotation.y, z: g.rotation.z }, s0 = g.scale.x;
    if (p) { p.state.opacity = 0; tl.fromTo(p.state, { opacity: 0 }, { opacity: 1, duration: fade, ease: "none", immediateRender: false }, t); }
    const { x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1 } = from;
    if (x || y || z) SF(g.position, { x: P0.x + x, y: P0.y + y, z: P0.z + z }, P0, t, kind, dur);
    if (rx || ry || rz) SF(g.rotation, { x: R0.x + rx, y: R0.y + ry, z: R0.z + rz }, R0, t, kind, dur);
    if (s !== 1) SF(g.scale, { x: s0 * s, y: s0 * s, z: s0 * s }, { x: s0, y: s0, z: s0 }, t, kind, dur);
  };
  const exit = (p, t, { dur = 0.3, to = null, obj = null } = {}) => {
    tl.to(p.state, { opacity: 0, duration: dur, ease: "power1.in" }, t);
    if (to) tl.to((obj || p.group).position, { ...to, duration: dur, ease: "power2.in" }, t);
  };

  // a neon tube (red, with a hot core) that blooms; centred at (x, y, z) in its parent, rotated rz; draw() grows it
  // from its left end. Only the tube glows — never the type.
  const neon = (id, w, { h = 10, glow = 2.3, x = 0, y = 0, z = 0.006, rz = 0, parent = null, color = COL.red, order = 5 } = {}) => {
    const H = h + 20;
    const bg = `linear-gradient(180deg, ${color} 0%, ${color} 20%, ${T.core1} 40%, ${T.core2} 50%, ${T.core1} 60%, ${color} 80%, ${color} 100%)`;
    const r = dom(id, w, H, `<i style="position:absolute;left:3px;right:3px;top:10px;height:${h}px;border-radius:${h}px;background:${bg}"></i>`, { style: "position:relative" });
    const p = P(r, { order });
    const pivot = new THREE.Group(); (parent || stage.scene).add(pivot);
    pivot.add(p.group); p.group.position.set(w / 2000, 0, 0);
    const c = Math.cos(rz), s = Math.sin(rz);
    pivot.position.set(x - (c * w) / 2000, y - (s * w) / 2000, z); pivot.rotation.z = rz; pivot.scale.x = 1e-4;
    p.state.glow = glow; p.state.opacity = 0;
    const L = {
      p, pivot,
      draw(t, dur = 0.3, ease = "power3.out") {
        tl.set(p.state, { opacity: 1 }, t);
        tl.fromTo(pivot.scale, { x: 1e-4 }, { x: 1, duration: dur, ease, immediateRender: false }, t);
        return L;
      },
      pulse(t, peak = 4.5, dur = 0.8) {
        tl.fromTo(p.state, { glow }, { glow: peak, duration: 0.08, ease: "power2.out", immediateRender: false }, t);
        tl.fromTo(p.state, { glow: peak }, { glow, duration: dur, ease: "power2.inOut", immediateRender: false }, t + 0.08);
        return L;
      },
    };
    return L;
  };
  // a soft coloured light (radial) — a halo behind a wordmark, light spilling out of a folder
  const halo = (id, w, h, { rgb = T.a_rgb, a = T.light ? 0.35 : 0.75, glow = 1.0, x = 0, y = 0, z = -0.05, parent = null, order = -2 } = {}) => {
    const r = dom(id, w, h, "", { scale: 0.5, style: `background:radial-gradient(ellipse 50% 50% at 50% 50%, rgba(${rgb},${a}) 0%, rgba(${rgb},${a * 0.45}) 34%, rgba(${rgb},${a * 0.12}) 56%, rgba(${rgb},0) 74%)` });
    const p = P(r, { order });
    if (parent) parent.add(p.group);
    p.group.position.set(x, y, z); p.state.glow = glow; p.state.opacity = 0;
    return p;
  };

  // a soft contact shadow on the floor under an object at (x, z), w × dpt world units; `lift` = how high the object's
  // bottom floats above the floor (a higher object casts a fainter, wider shadow). Light themes have no mirror: this
  // is what sits a laptop, a phone or a logo in the room. Returns the panel (move it with the object if it moves).
  const contact = (x, z, w, dpt = w * 0.28, { lift = 0, a = T.light ? 0.3 : 0.5 } = {}) => {
    const k = 1 / (1 + 3 * Math.max(0, lift)), W2 = Math.round(w * 1000 * (1 + 0.6 * (1 - k))), H2 = Math.round(dpt * 1000 * (1 + 0.6 * (1 - k)));
    const el = dom(`contact${Math.round(Math.random() * 1e9)}`, W2, H2, "", { scale: 0.5,
      style: `background:radial-gradient(ellipse 50% 50% at 50% 50%, rgba(${T.contact},${(a * k).toFixed(3)}) 0%, rgba(${T.contact},${(a * k * 0.4).toFixed(3)}) 45%, rgba(${T.contact},0) 72%)` });
    const sp = P(el, { order: -3 }); sp.group.rotation.x = -Math.PI / 2; sp.group.position.set(x, floorY + 0.003, z);
    return sp;
  };

  // words of a live panel revealed on their spoken times (inline-block spans), rising with the type spring
  const reveal = (els, times, { rise = 36, dur = 0.34 } = {}) => {
    const ws = els.map((el) => ({ el, v: 0 }));
    ws.forEach((w, i) => tl.fromTo(w, { v: 0 }, { v: 1, duration: dur, ease: sp("heavy", dur), immediateRender: false }, times[i]));
    d.onSync(() => { for (const w of ws) { w.el.style.opacity = String(Math.min(1, w.v * 1.8)); w.el.style.transform = `translateY(${(1 - w.v) * rise}px)`; } });
    return ws;
  };
  // typing synced to the voice: parts = [[text, t], …]; each part starts at its own time at `cps` characters/s
  const typeSync = (el, parts, { cps = 30, caret = null, blink = 0.53 } = {}) => {
    const sched = []; let all = [];
    for (const [txt, t] of parts) { const cs = Array.from(txt); sched.push({ t, from: all.length, n: cs.length }); all = all.concat(cs); }
    const st = { n: 0 };
    d.onSync((ts) => {
      let n = 0;
      for (const s of sched) if (ts >= s.t) n = s.from + Math.min(s.n, Math.floor((ts - s.t) * cps) + 1);
      st.n = n;
      el.textContent = all.slice(0, n).join("");
      if (caret) caret.style.opacity = n > 0 && n < all.length ? "1" : (Math.floor(ts / blink) % 2 ? "0" : "1");
    });
    return st;
  };
  const press = (t) => d.press(t);
  const flash = (t, v = 0.12, dur = 0.22) => d.flash(t, v, dur);
  const bind = async (duration) => { tl.to({}, { duration: 0.001 }, Math.max(0, duration - 0.001)); await d.bind(); };

  return { stage, tl, d, cam, D, S, SF, U, rig, drift, view, aim, breathe, P, IMG, enter, exit, neon, halo, reveal, typeSync, press, flash, bind, mirror, pool: poolP, base,
           floorY, T, contact };
}

// ── real logos, in 3D (name it, show it: a brand named on camera gets its real mark, which makes the edit feel alive) —
// the REAL mark from gfxlib/logos/ (copy the ones you need into <graphic>/assets/logos/; logos.json maps spoken names →
// file + colour), extruded, bevelled and lit by the stage's studio light. It is a real 3D object: motion blur and depth of
// field apply (and a mirror floor reflects it in noir).
//   const claude = await logo3d(W, "assets/logos/claude.svg", { width: 0.42, color: "#D97757" });   // width = its longer side
//   W.tl.fromTo(claude.rotation, { y: -0.6 }, { y: 0.6, duration: 4, ease: "sine.inOut" }, 0);
let _studioLit = null;
export async function logo3d(W, src, { width = 0.42, depth = 0.16, bevel = 0.022, color = null, metal = T.light ? 0.3 : 0.72,
                                       rough = T.light ? 0.42 : 0.28, glow = T.light ? 0 : 0.03, x = 0, y = 0, z = 0, parent = null,
                                       shadow = true } = {}) {
  const { SVGLoader } = await import("three/addons/loaders/SVGLoader.js");
  if (!_studioLit) _studioLit = await W.stage.studio(T.light ? { env: 1.0, key: 1.6, fill: 0.7, rim: 1.2, warm: T.warm, cool: T.cool }
                                                             : { env: 0.8, key: 1.8, fill: 0.5, rim: 2.2 });   // chrome catches light, no halo
  // on a light theme a near-white mark (OpenAI, X, GitHub…) would vanish into the cream: it takes the ink instead
  const lum = (h) => { const [r, g, b] = _hex(h); return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255; };
  if (T.light && color && color.startsWith("#") && lum(color) > 0.8) color = T.ink;
  const data = new SVGLoader().parse(await (await fetch(src)).text());
  const shapes = [];
  for (const p of data.paths) {
    const st = (p.userData && p.userData.style) || {};
    if (st.fill === "none") continue;
    const fill = color || (st.fill && st.fill !== "currentColor" ? st.fill : "#ffffff");
    for (const s of SVGLoader.createShapes(p)) shapes.push([s, fill]);
  }
  const b2 = new THREE.Box2();
  for (const [s] of shapes) for (const v of s.getPoints(24)) b2.expandByPoint(v);
  const svgW = Math.max(1e-6, b2.max.x - b2.min.x, b2.max.y - b2.min.y);   // the LONGER side: a tall mark fits too
  const mats = {}, inner = new THREE.Group(), group = new THREE.Group();
  for (const [s, fill] of shapes) {
    const key = new THREE.Color(fill).getHexString();
    mats[key] ||= new THREE.MeshPhysicalMaterial({ color: new THREE.Color(fill), metalness: metal, roughness: rough, clearcoat: 0.85,
                                                   clearcoatRoughness: 0.16, emissive: new THREE.Color(fill), emissiveIntensity: glow });
    const g = new THREE.ExtrudeGeometry(s, { depth: svgW * depth, bevelEnabled: true, bevelThickness: svgW * bevel,
                                            bevelSize: svgW * bevel * 0.6, bevelSegments: 5, curveSegments: 32 });
    const m = new THREE.Mesh(g, mats[key]);
    m.userData.depthMat = depthMaterial(null);                         // in the depth pass: focus and blur treat it as a real object
    inner.add(m);
  }
  inner.scale.set(1, -1, 1);                                        // SVG y points down
  group.add(inner);
  const c = new THREE.Box3().setFromObject(inner).getCenter(new THREE.Vector3());
  inner.position.set(-c.x, -c.y, -c.z);                             // centred, so it turns about its middle
  group.scale.setScalar(width / svgW);
  group.position.set(x, y, z);
  (parent || W.stage.scene).add(group);
  if (shadow && T.light && W.contact && !parent)   // light theme: a soft contact shadow on the floor instead of a reflection
    group.userData.shadow = W.contact(x, z, width * 1.1, width * 0.3, { lift: y - width / 2 - W.floorY });
  return group;
}

// a real mark as inline SVG for a DOM tag or card (flat, in its colour): `${await logoSVG("assets/logos/openai.svg", "#fff", 44)}`
export async function logoSVG(src, color = "#ffffff", px = 44) {
  const t = await (await fetch(src)).text();
  return t.replace(/<svg\b/, `<svg width="${px}" height="${px}" style="display:block;fill:${color}"`).replace(/<title>.*?<\/title>/s, "");
}
