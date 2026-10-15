# The look of every graphic (binding)

Every card, diagram, 3D scene and promo in a video obeys this page. Graphics are made with the engine (`engine/`, read
`engine/ENGINE.md` before a scene of your own) on the shared library `gfxlib/gfx.js` (the room, the camera, the springs,
the theme). Anything in `NOTES.md` overrides this page.

## The theme
- **Every graphic declares the theme and the video's accent on its root element**, and copies `gfxlib/gfx.js` FRESH into
  its `assets/` (new_card.py, chapter_cards.py, make_icons.py and logo_clip.py do both):

      <html lang="en" data-theme="warmcream" data-accent="#E0703A">

  gfx.js reads both when it loads, before any text is measured. plan.py says the same (`THEME`, `ACCENT`): the assembler
  frames the face, lays the base and checks for empty frames in that theme. A missing or unknown value falls back to
  warmcream and the theme's own accent.
- **Colours only through the theme's CSS variables** (gfx.js puts them on `:root`): `--bg --surf --surf2 --surf3 --floor
  --ink --mute --line --hi --accent --accent-t --a-rgb --core1 --core2 --shadow --glass-shadow`, and in JS `T` (the resolved
  theme) and `COL`. Never write a hex colour into a template: a theme change has to reach every graphic. Panel drop
  shadows: `shadow(blur, y)` from gfx.js.
- **ONE accent per video**: the product's colour when the video is about one product (`data-accent`: Claude `#D97757`,
  Gemini `#8E75B2`, …), otherwise the theme's own. A white or black brand (OpenAI, X) takes the theme's.

### Warm Cream (`warmcream`, the default)
- Ground `#F2ECE1` (warm cream, one continuous backdrop — no horizon line). Cards warm white `#FFFCF7 → #F7F1E7 → #EAE2D3` (`.glass`), a
  hairline `rgba(70,45,20,.12)` and a soft warm shadow. Ink `#1F1B17`, mute `#7A7064`. Default accent `#E0703A`.
- **No edge light, no mirror floor, no coloured pool.** `world()` enforces all three on a light theme even when a template
  asks for them. Vignette 0.12, grain 0.03, bloom 0.2: accent strokes still glow, softly.
- 3D stands on the floor with a soft **contact shadow** (`W.contact(x, z, w, d, { lift })`; `logo3d` adds its own), never a
  reflection — a laptop or a phone included.
- A grid or dots on the floor: ink at ≤ 8 % alpha, or none — never the accent (it reads busy).
- A panel's `dim` fades it toward the ground (a step back, still readable), not to a grey slab.
- White brand marks (OpenAI, X, GitHub…) take the ink by themselves in `logo3d`; metal is satin, not chrome.

### Noir (`noir`)
- Near-black stage `#050506`, neon red `#ff1e3c` / `#ff2a48`, glass cards, a mirror floor with a dim red pool; world text
  sits ABOVE the reflection line (a mirror shows text upside down). Type in capitals (`--case: uppercase`), Geist 800.
- **The edge light is a whisper**, from kit.js `noir()` / gfx.js `world()` and nowhere else: base 0.015, width 0.045 of the
  screen, a hit never past 0.06. Stronger values were tried and "took over" the frame. Never set `U.edge.value` by hand.
- The scenes in `scenes/` are built in Noir.

### A theme of your own
Copy the `warmcream` entry in the THEMES block of `gfxlib/gfx.js` under a new name, change the colours, `serif` (serif
headlines or not), `case` (`none` or `uppercase`), `light` (true for a light ground), then use that name for `THEME` and
`data-theme`. Render one card, look at it on a phone, then use it for a whole video.

## The balance: the face, the graphic, or both
Every moment is one of three states, kept **even, about a third each**:
- **FACE**: the speaker alone, full frame (punch-in on every other jump cut). The hook, opinions and reactions,
  transitions, teasers, the asks, the verdict, the CTA. No graphic on a line where they talk TO the viewer.
- **BOTH**: the graphic and the face at once. `layout="side"` puts the graphic at 65 % on the left and the face card on
  the right; `layout="corner"` puts a 512×288 face card over the graphic's bottom-right. Explanations, numbers, comparisons, lists.
- **GRAPHIC**: full frame, for showpieces where the visual IS the point (a real page to read, a 3D scene), chapter cards,
  flashes, inserts.

Targets, printed by `assemble.py` with every plan (`balance · face · both · graphic`), with a ⚠ when off: each state 20–45 %
of the runtime (aim ~30–35 %); the face on screen (FACE + BOTH) ≥ 60 %; never more than ~12 s without the face.
Design every graphic to survive both layouts: keep the key content out of the bottom-right ~30 % × 30 % (the corner card
sits there), and size type so it still reads at 65 % (headline ≥ 90 px, body ≥ 48 px). Mark in each brief which layout
a graphic is for.

## Logos: name it, show it
- **Every brand named gets its REAL logo on screen** at that moment. `gfxlib/logos/logos.json` has 50 marks with their
  sources ("says" = the spoken names for each, "mishears" = whisper's versions). A brand that isn't there: fetch its own
  SVG (press kit, its site, or the official file on Wikimedia Commons), add it with its source. Never redraw one.
- **3D wherever it fits.** In a graphic: `logo3d(W, "assets/logos/<slug>.svg", { width, color })` (extruded, bevelled,
  lit, with motion blur and depth of field like any 3D object; a contact shadow on cream), turning slowly or landing on the
  word. In a tag or a small card: the flat mark, `logoSVG(...)`, in place of the dot.
- **On the face** (FACE state): a transparent 3D logo clip from `gfxlib/logo_clip.py <slug>` (rendered once, reused) laid
  beside the head with a LOGOS entry in gfx_slots.py (or `cut(…, layout="sticker", pos="right"|"left"|"tr"|"tl", size=360)`):
  it fades in and out with a pop, and the face stays full frame.
- Not every repeat: the first mention in each section and the key moments (a verdict, a comparison, a price), about one
  logo per 6–10 s at most. `tools/logos_in_take.py <edit>` lists every mention, when, and what is on screen then.
- The brand's own colour on its logo (logos.json "color") may sit next to the one accent: it's their mark, not a second accent.
- Logos are trademarks: show them to name the product you are talking about (nominative use), never as if the brand
  endorsed the video.

## Type
- Headlines in the theme's display face: `var(--display)` / `var(--display-w)` / `var(--display-ls)` = **Instrument Serif
  400** in Warm Cream (Geist 800 in Noir). Labels, tags, body: **Geist 600–700** (`var(--sans)`). Roboto for UI, JetBrains
  Mono for code and terminals. Link with `--fonts "Geist,Instrument Serif"` (+ `Roboto`, `JetBrainsMono` when used).
- **Sentence case, the words as said** ("their social media page", "the Claude app"). Put `text-transform: var(--case)`
  on titles and labels and let the theme decide (Noir capitalises). Never type capitals into a card's text.
- Ink `var(--ink)`; the accent (`var(--accent-t)`) only on one word, a number or the closing period.
- Readable: ≥ 34 px on screen at 1080p, labels Geist 600+, 100–120 px safe margins.
- **An element's box IS its panel** (the engine forces it): centre text with CSS (`justify-content` / `text-align`),
  never rely on text filling the panel. A `.tag` pill shrinks its text to fit (`world()` does it) — still size `tagW`.

## Motion
- Closed-form springs (`spring` / `sp` / `S` / `SF` in gfx.js): a little overshoot on UI ("ui"), none on type ("heavy").
  Every element enters already moving; something changes every ~1 s.
- Real 3D: tilt panels 0.1–0.5 rad; the camera always drifts or dollies, never locked; 8-sample motion blur.
- Depth of field on (`dof: { strength: 26–32, max: 34–42 }`) — but **anything the viewer must read is in focus** (aim the
  target at it, set `cam.focus`, or rack to it). Blurry text is a rejection.
- Camera tweens per shot; never one scene-long tween under shorter ones (it snaps the value back when they end).
- Glow (`state.glow` 1.5–2.6, bloom) only on light sources and strokes (underlines, outlines). UI surfaces and type never glow.
- No fades-in-place, no centred title on a gradient, no corner labels or frame borders, no particles.

## Content
- **Only the speaker's words.** Every word on a card is theirs (from the cut's words_out.json) or real UI chrome from a
  capture. Paraphrases that add words, technical facts they didn't say, invented example comments → out. Numbers: only
  what they said, or real output replayed and labelled as such. **Never invent numbers in a rebuilt UI.**
- Real assets only: captures of the real sites (`tools/capture.py`), the creator's real thumbnails and pages, real code.
  Third-party footage or frames carry an on-screen credit (`@handle · TikTok`). No generated imagery unless the creator
  asks for it.
- Sound: none in graphic renders — the assembly adds the bed and the effects. A promo insert carries its own mix.

## The library (`gfxlib/`) — start from these
- `gfx.js` — `world()` (the room in the theme, camera rig, `P` / `IMG` panels, `neon`, `halo`, `contact`, `reveal`,
  `typeSync`…), `logo3d`, `logoSVG`, `shadow`, `fit`, the theme (`THEMES`, `T`).
- `cards/` + `new_card.py`: `words` (kinetic lines that land on the words), `vs` (two sides; the winner steps forward, the
  other dims), `grid` (a title + tiles), `detail` (1–3 images with tags), `pair` (two images on two screens).
- `cards/chapter/chapter_cards.py` — numbered chapter cards (1.8 s: the number in the accent, the title in the display face,
  a drawn accent stroke, an optional subtitle) and the **chapter pill** the assembler lays top-left for the rest of each chapter.
- `cards/icons/make_icons.py` — Lucide line icons (ISC licence) drawn stroke by stroke in the accent, the words under each,
  an optional flow line between them.
- `tools/screenfollow.py`, `pagebeat.py`, `screenbeat.py`, `capturebeat.py` — real screens and pages (SKILL.md step 5).
- `logo_clip.py` — a transparent turning 3D logo for a sticker. `logos/` — the marks.

## Making one (the loop)
1. Scaffold it in `AI_EDITOR_HOME/projects/<slug>/gfx/<name>/` (new_card.py or the other builders do), `data-duration` =
   the exact slot length, the theme and accent on `<html>`, gfx.js copied fresh.
2. Render ONLY with `bash tools/render.sh <dir> <name> --fonts "Geist,Instrument Serif"` (one worker; it takes the render
   lock and waits its turn). Never start a second render yourself.
3. Look at `renders/<name>-sheet.png` (and `tools/sheet.py <mp4> <png> t1 t2 …` for a frame at each word). Score 1–10:
   readability at phone size, motion, composition, premium feel, accuracy (the speaker's words, real numbers). Fix the
   three worst, re-render. Ship at 8+ everywhere, at most 3 rounds.
