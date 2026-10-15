# Engine reference (launch.js + kit.js)

The engine every graphic is rendered with: a real three.js camera over HTML panels and real images, 8-sample motion blur,
true depth of field, rendered frame by frame by HyperFrames (headless Chrome). gfxlib/gfx.js builds the house look on top of
it (`world()`, `logo3d()`…); most graphics only touch gfx.js. Read this when you build a scene of your own.

Units: **1 world unit = 1000 CSS px**. At `stage.unitDistance()` (D ≈ 3.348 for 1080 × 1920, fov 32) a plane at
z = 0 shows its CSS size 1:1. Closer = bigger. The camera looks at a target; everything is a function of time.

## launch.js

### `new Stage(opts)`
`{ canvas, width = 1080, height = 1920, fps = 30, samples = 8, shutter = 180, fov = 32, background, dof: { strength,
max }, grain = 0.028, vignette = 0.14, exposure = 1, bloom: null | { strength, threshold } }`
- `samples` sub-frames per output frame across `shutter`° — true motion blur. 1 = off (drafts).
- `dof.strength` px of blur per unit of depth error (scaled by distance), capped at `max` px. 0 = off.
- `bloom` only for dark looks that want halation; keep it off for brands that say "no glow".
- `stage.cam` — the rig GSAP animates: `x, y, z` (position), `tx, ty, tz` (target), `roll` (rad), `fov`, `focus`
  (distance; ≤ 0 or null = auto on the target), `aperture` (multiplies dof.strength).
- `stage.presentMat.uniforms.flash.value` — 0…1 toward white, display space (use `d.flash`).
- `stage.hud(panel, { x, y, dist = 0.5 })` — pin a panel to the camera; x, y in px from the frame centre (y down).
  Its depth reports the focus distance, so it is never blurred.
- `stage.unitDistance()`.

### `ground(stage, { colorA, colorB, dots, spacing = 22, z = -1.6, size = 40 })`
The floor/backdrop plane: brand canvas colour with a dot texture. `ground.mix` (0…1) blends A → B — flip it at the
fastest instant of a whip (a dark section).

### `htmlPanel(stage, { canvas, el, w, h, scale = 2, radius, shadow, opacity, live, sheen })`
The element `el` inside `<canvas layoutsubtree>` (CSS size w × h), painted into a texture on a plane.
- `live: true` — repainted every frame it is visible (counters, typing, highlights). Static panels paint once.
- `shadow: { blur, y, opacity, z, color }` — a soft contact shadow plane behind it.
- `panel.state` — tween these: `opacity`, `sheen` (−1 … 2: a light sweep position), `dim` (0 … 1, perceptual).
- `panel.group` — position / rotation / scale (THREE.Group). Re-parent into your own groups freely.
- `panel.locate(selector, ax = .5, ay = .5)` — the world position of an element inside the panel (aim cameras at
  words). Measured with the group's current transform: set the rotation it WILL have, measure, set it back.

### `imagePanel(stage, { img, w, h, radius, shadow, opacity, sheen })` · `loadImage(src)`
A loaded image on a plane at native resolution (thumbnails, screenshots, covers, avatars — radius = w/2 → a circle).
Same `state` / `group` as htmlPanel.

### `await stage.studio({ env, key, fill, rim, warm, cool })`
A soft room reflected in every PBR surface + key / fill / rim lights. Only loaded models use light; HTML panels and
images stay the brand's exact pixels.

### `await loadDevice(stage, { url, kind = "phone" | "laptop", screen, size, hideLogos = true, finish })`
Loads `assets/vendor/models/iphone.glb` or `macbook.glb`, scales it (phone height / laptop width = `size` units),
centres it, turns its display to +Z, gives the display planar UVs and puts `screen.tex` on it (a live htmlPanel; its
own plane is removed), adds depth materials (devices take part in depth of field), hides logo meshes, and recolours
the body metal with `finish`. Returns `{ group, model, display, screen }`. Hide `group` until its shot
(`tl.set(group, { visible: true }, t)`) and set `screen.state.opacity = 0` so the screen is not repainted before.

### `bindToHyperFrames(stage, tl, sync)`
Wires the GSAP timeline to HyperFrames' seek: for every frame and every motion-blur sub-frame the timeline is
seeked (events suppressed), panels sync, `sync(ts)` writes live DOM, live visible panels repaint, then the frame
renders. Await it, then `window.__timelines["main"] = tl` in the page.

## kit.js

### `beatGrid(beat, fps = 30)` → `{ BEAT, BAR, FPS, B(n), b(n), cut(t) }`
Start the music so its drop is a bar line (`new.py` does), then `B(1)` is the drop. `cut(t)` rounds to the middle
between two frames — use it for every hard cut and every `tl.set` of the camera.

### `director(stage, tl)` → `d`
| helper | does |
|---|---|
| `d.panel(id, w, h, o)` / `d.hud(id, w, h, x, y, o)` / `d.image(img, w, h, o)` | make panels (hud: pinned + hidden) |
| `d.at(p, x, y, z)` | place a world panel |
| `d.slam(p, t, from = 1.2, dur = .22)` | appear at t, scaling from `from` × (expo.out) |
| `d.rise(p, t, { dur, dy })` | fade + rise dy px |
| `d.fade(p, t, to, dur)` / `d.out(ps, t, dur = 0)` | opacity |
| `d.flash(t, v = .3, dur = .24)` | display-space flash |
| `d.frame(x, y, dist, sy = 0, z = 0)` | a camera framing: the point shown sy px below centre |
| `d.cutTo(t, framing)` | hard camera cut (resets roll, focus, aperture) |
| `d.move(t, to, dur, ease)` | a camera move |
| `d.whip(t, to, { roll, dur = .36, lead = .2 })` | whip pan centred on t, then settle the roll |
| `d.punch(t, framing, { by, dur, roll })` | zoom punch on a cut (flicker hooks) |
| `d.rack(t, from, to, dur)` | rack focus between two distances |
| `d.words(ids, times, { rise, dur })` | live word-by-word reveal (live panel) |
| `d.highlight(el, t, { dur, height })` | highlighter sweep behind inline text (live panel) |
| `d.type(el, text, t0, t1)` | typing (live panel) |
| `d.press(t)` → `{ press, ripple }` | a button press curve; style it in `onSync` |
| `d.onSync(fn)` / `d.bind()` | per-frame DOM writes / wire to HyperFrames |

### `schedule(initial)` → `{ at(t, v), get(ts) }`
Discrete state over time (face-up card, lit tiles, a label). Read it in `onSync`.

### `wall(d, imgs, { cols, rows, w, h, gapX, gapY, radius, order, dim })` → `W`
A grid of image tiles in `W.group` (rotate the group for 3D). `W.light(t, keys, dimTo)` lights some tiles and dims
the rest; `W.frameOn(key, dist, sy)` frames one tile; `W.look.dim` is tweenable. 3 × 9 tiles of 640 × 360 with 40 px
gaps fill a 9:16 frame at distance ≈ 6.6; 9 × 3 fill 16:9.

### `burst(d, items, t, { from, stagger, dur, spin })`
Items `{ p, x, y }` fly from one point to their places, nearest first — a deck opening on the drop.

### `fitText(selector, { margin, step, min })` · `makePanelDom(root, html, w, h, { scale, className })`
Shrink headlines whose text is wider than their box (after `document.fonts.ready`). Build panels from data.

## Promos: a beat grid, a camera, the brand's own material
A promo (the hero insert) is planned in bars, not seconds. `tools/new.py <dir> --music track.mp3 --aspect 16:9` scaffolds it:
it beat-maps the track (`beats.py`), starts the music so its biggest drop is bar 1, and writes `promo/index.tpl` from
`engine/starter.tpl` (it renders as is). Then storyboard **one idea per bar, one element per beat**:

| bar | job | typical shot |
|---|---|---|
| 0 (before the drop) | the hook: a tension, a question, the problem, readable in 1 s | a typed line, a flicker of real images, a slammed question |
| 1 (the drop) | the reveal: the brand, big | a hard cut close + dolly back, a pull-back to a wall, a burst into a grid |
| 2 … n−2 | proof: what it does, how, the numbers | a live card, a list on beats, a whip to one item per beat, number slams |
| n−1, n | the offer and the address | the call to action, a button press, the URL, the wordmark — hold ≥ 1 bar |

Use the track's own events: a silent beat is a freeze or a slam; a pickup hit is one more cut. An app or a site is most
convincing ON a device (`await stage.studio()` then `loadDevice(...)`, below) with the REAL capture on its screen. Check the
drop yourself on the low band (< 120 Hz) before building: a reported drop can sit a fraction of a beat before the bass.
`scenes/hero/` is a finished example (scenes/README.md says how to re-time it to your track).

## Tools (in `tools/`)
| tool | use |
|---|---|
| `new.py <dir> --url --music --drop --drop-bar --bars --aspect` | scaffold a promo (capture, font, beats, `engine/starter.tpl`, link) — the start of a hero promo |
| `capture.py <url> <out> [--lang en-US] [--scheme dark|light]` | brand.json + real screenshots (desktop, mobile, og, logos; bottom-pinned bars lifted out of the full-page shot into `mobile_fixed_bottom@3x.png`). Needs playwright |
| `beats.py <audio> [--anchor s] [--out f]` | tempo, refined beat grid, downbeats, bar loudness, drops (low-band rise) |
| `fonts.py add "Family:wght@…"` / `list` | download Google Fonts (latin + latin-ext) into AI_EDITOR_HOME/vendor/fonts |
| `link.py <project> [--fonts A,B]` | copy the engine, three.js, GSAP, fonts (and the device models if used) into the project, write index.html from index.tpl |
| `render.sh <project> [name] [--fonts A,B] [--alpha]` | link, lint, validate, render (1 worker, one render at a time), mix, encode, sheet |
| `mix.py <cues.json> <video> <out>` | a promo's own music + effects → −14 LUFS, −1.3 dBTP, picture stream-copied |
| `sheet.py <video> <out.png> t1 t2 … [--w] [--cols]` | labelled contact sheet |

## Pitfalls (each cost a render)
| symptom | cause → rule |
|---|---|
| a panel renders empty | its `<canvas layoutsubtree>` had `opacity:0` → hide sources with `z-index:-1`, never opacity |
| lint: no timeline | registered before binding → `await d.bind(); window.__timelines["main"] = tl` in the page |
| fonts missing / StaticGuard | an external stylesheet → `/*FONTS*/` in the template; link.py inlines the `@font-face` blocks |
| "multiple root compositions" | two html files → the source is `index.tpl`, link.py writes `index.html` |
| a blended frame at a cut | the shutter straddled it → cut at `cut(t)` (half-frame) |
| cuts ahead of the music | check the bass onset on the low band (< 120 Hz) at the drop yourself; `beats.py --anchor <onset>` |
| panel type too wide | the engine forces each element's box to its panel's size → centre text with CSS, don't rely on it filling the panel |
| a type slam overruns the frame | `fitText()` after `document.fonts.ready` |
| text unreadable over images | dim the tiles (`wall.light`), rack focus, or a pill behind the line |
| the capture is in the wrong language | `capture.py --lang en-US` |
| a model shows someone's logo / an odd colour | `loadDevice` hides logo meshes; `finish: "#2b2b2e"` recolours the body |
