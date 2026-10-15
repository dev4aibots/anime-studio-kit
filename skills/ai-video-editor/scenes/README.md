# The 3D scenes (levels 7–10)

Seven finished scenes from real videos, kept as starting points. Each is one `index.tpl` built straight on the engine
(`engine/launch.js` + `kit.js`), not on `gfxlib/gfx.js`.

**Before you use one, know three things:**
- They are built in the dark **Noir** look (near-black room, red neon, a mirror floor, kit.js `noir()`). To use one in a
  Warm Cream video, either play it as a dark "trailer" insert, or move it onto gfx.js `world()` (the room, the floor,
  the glow); the camera moves and timings stay as they are.
- They need **your own images** in `assets/` (listed below). Every number and every word on screen must be real and
  yours: capture your own page with `tools/capture.py`, never type a view count you don't have.
- **Every word on screen in them is from the video they were made for** (the typed search, the labels, the pills, the
  placeholder page text). Replace all of it with your own words before you render, and re-time the moves to your words.
- They were rendered many times in the videos they come from, but not re-rendered from this pack. Expect to adjust.

| scene | what it shows | length | needs in `assets/` |
|---|---|---|---|
| `motion-blur-subframes` | the 8 sub-frames averaged into one frame, then a whip across a wall of thumbnails | 22.4 s | `thumbs/t00.jpg` … `t26.jpg` (27 frames or thumbnails, 16:9) |
| `depth-of-field` | a row of cards receding on the floor, the depth pass itself (white near, black far), a rack focus | 9.0 s | `thumbs/t05.jpg`, `t09`, `t01`, `t08`, `t02`, `t04`, `t22` (7 images, 16:9) |
| `laptop-reskin` | a site on a 3D MacBook; the room takes the site's colours; the screen swipes to a second page | 12.1 s | `pl.png`, `yt.png` (two 2880×1800 captures) + the MacBook model |
| `exploded-phone` | a phone's page lifts off in layers (wireframe → metal), each layer a real piece of the page | 19.3 s | `brand/player.jpg` (a 16:9 frame), `brand/avatar.jpg`, `brand/community_cover.jpg` + the iPhone model |
| `hero` | the beat-synced promo: a search bar types, the phone spins in on the drop, pop-outs lift off the glass, the wordmark | 15.7 s | the same three `brand/` images + the iPhone model + your music (below) |
| `library-wall` | a wall of everything you made, lit in a wave as the camera pulls back | 6.4 s | `tiles/t00.jpg` … `t21.jpg` (22 frames, 16:9) |
| `paid-vs-free` | a paid route (three pills joined by a line) steps back while "$0" comes forward | 16.0 s | nothing (edit the pill names to your own words) |

## Use one

```bash
H="${AI_EDITOR_HOME:-$HOME/ai-video-editor}"; SK="$HOME/.claude/skills/ai-video-editor"; G="$H/projects/my-video/gfx/hero"
mkdir -p "$G/assets" "$G/renders" && cp "$SK/scenes/hero/index.tpl" "$G/" && cp "$SK/gfxlib/project/"*.json "$G/"
# put your images in $G/assets/ (table above), replace every placeholder text in index.tpl with your real page's text
bash "$SK/tools/render.sh" "$G" hero_v1 --fonts "Geist,Roboto"
```

Render one at a time (render.sh waits for any other render). At 8-sample motion blur a 16 s scene takes about
1–1.5 minutes per 20 s of video on a recent laptop, longer on an older one.

## The hero: re-time it to your own track

The hero's moves are written on a beat grid (`beatGrid(0.6307)`: 95.1 BPM, the drop on bar 1 = 2.523 s). With your
own track:
1. Pick a licensed track with a clear drop (Mixkit's free music works: mixkit.co/free-stock-music, Mixkit License).
2. `python tools/beats.py track.mp3 --out beats.json` prints the tempo and the drops. Then check the bass onset yourself
   on the low band (< 120 Hz): on one track the reported drop sat 0.31 s before the bass actually came in, so every
   beat-synced move landed early. Use `--anchor <the real onset>`.
3. Put the period in `beatGrid(<seconds per beat>)` and start the music so its drop lands on bar 1: write
   `audio/cues.json` = `{"duration": 15.7, "music": {"file": "track.mp3", "start": <onset − 2.523>, "fade_out": 1.0},
   "sfx": []}` with the track copied into `audio/`. render.sh mixes it in (mix.py).
4. In the edit, the hero plays as an insert with its own sound: `HERO` + `HERO_AFTER` in `plan.py`.
