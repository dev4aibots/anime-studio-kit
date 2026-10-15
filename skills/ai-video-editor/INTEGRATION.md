# INTEGRATION.md — ai-video-editor skill × our JS anime pipeline

Source: user's Drive pack, installed 2026-10-15 at `~/workspace/custom-skills/ai-video-editor/`
(also at `~/workspace/ai-video-editor/drive-pack/` with the zips + PDF + README).
Pure code throughout — no generative AI. Compatible with the standing pure-code order.

## What we take (ranked by value to anime production)

### 1. engine/ — the 3D motion-graphics renderer (HIGHEST VALUE)
`engine/launch.js` + `engine/kit.js` + `engine/ENGINE.md`
- A real three.js camera over HTML panels, rendered frame-by-frame by **HyperFrames**
  (the same renderer our pipeline already uses).
- **8-sample true motion blur** (`samples`, `shutter`) — our anime action cuts (chases,
  impacts, whip pans) get real motion blur instead of fake smear frames.
- **True depth of field** (`dof.strength`, `focus`, `aperture`) — rack focus between
  character and background, cinematic closeups (e.g. the tiger-eye shot).
- **Director helpers** (`kit.js`): `d.slam`, `d.whip`, `d.punch`, `d.rack`, `d.move`,
  `d.cutTo`, `d.words` (word-by-word reveal), `d.type` (typing), `d.highlight`.
- **beatGrid**: plan motion on music bars/beats; `cut(t)` for frame-exact cuts.
- **Units**: 1 world unit = 1000 CSS px; `stage.unitDistance()` for 1:1 panels.
- **When to use**: any anime shot that wants camera choreography — title cards, impact
  frames, transitions, promo/credit sequences, 3D logo stings. NOT for character
  animation itself (that's Live2D/Canvas); this is the camera + graphics layer.
- **Cost note**: 8-sample motion blur multiplies render time ~8×. Use `samples: 1`
  for drafts, 8 for finals. One render at a time (`tools/render.sh` holds a lock).

### 2. gfxlib/gfx.js — themed motion-graphics cards
- `world()`, `logo3d()`, card builders on top of the engine.
- **THEMES block** (strict JSON between `/*THEMES*/` markers): `warmcream` (default),
  `noir`. One accent colour per video.
- **Use**: dialogue cards, chapter cards, name plates, stat cards in anime episodes;
  style new anime UI (pause menus, credit rolls) by copying a theme entry.
- Read `STYLE.md` before building any graphic — it is binding for the look.

### 3. tools/qc.py + tools/sheet.py — quality control
- `qc.py`: contact sheets every N seconds + frames either side of every switch.
- Adopt for our pipeline: after every anime render, generate the contact sheet and
  LOOK at it before delivery (this is the "look before you show" rule).

### 4. tools/beats.py — beat mapping
- Tempo, beat grid, downbeats, drops (low-band rise) from an audio track.
- Use for music-synced anime motion (openings, AMV-style cuts, beat-synced promos).

### 5. scenes/ — 7 finished 3D scenes (study, don't copy blindly)
`hero`, `depth-of-field`, `motion-blur-subframes`, `exploded-phone`, `laptop-reskin`,
`library-wall`, `paid-vs-free`. Read `scenes/README.md`; they are dark-theme
starting points — re-skin with our anime art, don't ship their placeholders.

### 6. The workflow discipline (adopt as doctrine)
- **Only real words/numbers on screen** — never invented text in graphics.
- **Cut on the waveform, check by ear** — never cut on transcript timestamps alone.
- **Look before you show** — every graphic's contact sheet before delivery.
- **NOTES.md becomes rules** — every user correction goes in as a dated rule.
- **One render at a time**, always through the render lock.

## What we DON'T take
- The talking-head pipeline (transcribe → cut → face/BOTH/GRAPHIC balance) — built
  for 16:9 YouTube talking-head, not anime. The *tools* transfer, the *workflow* doesn't.
- `tools/capture.py` screen-capture flow — needs playwright + macOS OCR; skip unless
  a video needs real page captures.
- Brand logos (`gfxlib/logos/`) — trademarks; only to name a product actually discussed.

## Wiring checklist for next anime project
- [ ] `tools/link.py`-style: vendor three.js + GSAP + engine into the project dir
- [ ] Build the shot with `engine/starter.tpl` as the page template
- [ ] `d.bind()` + `window.__timelines["main"] = tl` (HyperFrames seek wiring)
- [ ] Draft at `samples: 1`, final at `samples: 8`
- [ ] QC with contact sheets before delivery
