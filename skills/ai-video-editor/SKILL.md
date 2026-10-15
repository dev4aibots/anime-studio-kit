---
name: ai-video-editor
description: >-
  Edit a raw talking-head recording into a finished long-form 16:9 YouTube video, end to end, on this computer: transcribe it
  with word timings, cut the mistakes, restarts and long pauses on the waveform, fact-check what is said, plan every line as
  face, graphic or both (about a third each), build motion graphics with HyperFrames and three.js (cards that land on the
  spoken words, chapter cards, line icons, real screens and pages, 3D logos, 3D devices, motion blur, depth of field), mix
  the voice and music, check every frame, and write the publish sheet. Use when someone gives a raw video and asks to edit
  it, cut it, add motion graphics or "do the full edit"; also to re-cut, re-assemble or restyle a video made with it, or to
  add a note that should change every future edit. Not for vertical shorts.
---

# AI video editor

A raw take goes in; a finished 16:9 video, its chapters and its publish sheet come out. Seven jobs, run by you (Claude
Code) with the tools in this folder. **Read `NOTES.md` first, every time**: it holds the creator's own rules, and they
override anything below.

Where things are (`tools/aie.py` resolves them; `python tools/aie.py` prints them):
- `SK` = this skill folder (code: `tools/`, `engine/`, `gfxlib/`, `scenes/`, `templates/`).
- `AI_EDITOR_HOME` (default `~/ai-video-editor`) = everything downloaded or made: `venv/`, `node_modules/`, `vendor/`,
  `models/`, `music/`, `sfx/`, `logos3d/`, and `projects/<slug>/` — one per video: `edit/` (the cut and the plan) and
  `gfx/` (its graphics).
- Run every tool with the venv's Python. Shell variables don't persist between your commands, so start each command with
  the three variables of step 0 (they work whether or not AI_EDITOR_HOME is set). Every tool prints its usage with `--help`.
- Before a first edit, or when something fails: `$PY $SK/tools/doctor.py` (✓ / ✗ per requirement).

## The seven jobs and what each one leaves behind

| job | does | leaves behind (in `projects/<slug>/`) |
|---|---|---|
| 1. Transcriber | every word with its time (whisper.cpp, DTW timings), plus a verbatim pass that writes repeats twice | `edit/work/audio/words.json`, `read.txt`, `edit/work/rep/literal.json` |
| 2. Editor | fact-checks what is said, picks the last clean take of each line, cuts on the waveform, re-listens to its own cut | `edit/keep.json`, `edit/work/edl.json`, `aroll.mp4` + `aroll.wav`, `words_out.json`, the diff report |
| 3. Director | gives every line a state: FACE, BOTH (graphic + face) or GRAPHIC, about a third each, never 12 s without the face | `edit/gfx_slots.py` → `GRAPHICS.md`, `edit/plan.py`, the balance line |
| 4. Motion designer + 2 helpers | builds the graphics on the words they illustrate; the helpers build cards and diagrams in parallel | `gfx/<name>/renders/<name>.mp4` + a contact sheet each |
| 5. Sound engineer | lifts the voice (no compressor), lays the music bed under it, a sound on each cut-in, masters to −16 LUFS | the mix inside `edit/out/final.mp4` |
| 6. Quality control | contact sheets of the whole video, the frames either side of every switch, picture = sound, loudness | `edit/out/qc_sheet_*.png`, `qc_cuts.png`, the report |
| 7. Publisher | titles, description with the chapters, tags, a thumbnail brief from outliers | `publish/publish.md`, `edit/out/chapters.txt`, `renders/<slug>_FINAL.mp4` |

## The workflow

### 0 · A project
```bash
H="${AI_EDITOR_HOME:-$HOME/ai-video-editor}"; SK="$HOME/.claude/skills/ai-video-editor"; PY="$H/venv/bin/python"
P="$H/projects/my-video"; E="$P/edit"; mkdir -p "$E" "$P/gfx"
```
Ask the creator for: the raw file, the video's working title, the product it is about (for the accent colour), and the
script or the sources for any number they say. Long-form 16:9 only; a take that isn't 1920×1080 at 30 fps is conformed once.

### 1 · Transcribe (≈ 4 min for a 10-min take)
```bash
$PY $SK/tools/transcribe.py "$E" "/path/to/raw-take.mov"
$PY $SK/tools/literal_asr.py "$E/work/audio/take16k.wav" "$E/work/rep/literal.json"
$PY $SK/tools/islands.py "$E"            # the take as speech islands: the reading view
```
Whisper smooths repeats away ("and it, and it connects" → "and it connects"); the verbatim pass doesn't. Read both.
Names the creator says often (products, people) go in `AI_EDITOR_HOME/vocab.txt`, one per line: whisper gets them as a
hint. Spellings to treat as the same word when a cut is checked go in `AI_EDITOR_HOME/folds.json` (`{"cloud": "claude"}`).

### 2 · Fact-check and choose what to keep → `keep.json`
Read `islands.py`'s output top to bottom. For each idea keep the LAST clean take. Check every claim and number against a
source (the creator's script, the product's own page). Wrong → cut it; never "correct" the speaker with words they didn't
say. Also cut flubs, asides about things not tested, sentences said twice. Write `edit/keep.json`
(`templates/keep.example.json`): `[t0, t1, "the words in it, spelled as meant", "s"|"m"]` per kept range, in order.
Show the creator anything you cut for being false.

### 3 · Cut, then check the cut by ear (≈ 10 min)
```bash
$PY $SK/tools/island_cut.py "$E"          # keep.json → work/edl.json (edges found on the waveform)
$PY $SK/tools/aroll_audio.py "$E"         # the cut's voice only, fast
$PY $SK/tools/words_out.py "$E"           # every kept word's OUTPUT time (whisper on the cut + keep.json's spelling)
$PY $SK/tools/literal_asr.py "$E/work/aroll_check16k.wav" "$E/work/rep/cut_literal.json"
$PY $SK/tools/cut_diff.py "$E"            # intended words vs heard, each difference at its nearest splice
$PY $SK/tools/assemble_aroll.py "$E"      # the A-roll picture + voice, trimmed by frame count
```
Every difference cut_diff prints is a clipped word, a leaked restart or a kept repeat until you've heard it
(`hear.py "$E" "$E/work/aroll_check.wav" t0 t1`). Fix the edge in keep.json (`splice.py "$E" t0 t1` shows the waveform
around it; a 5th item "in"/"out"/"both" keeps a hand-measured edge exactly) and redo step 3.
A clean take with no retakes can use the quick path instead: `cutfix.json` (`templates/cutfix.example.json`) →
`cut.py` → `assemble_aroll.py` → `verify_cut.py`.

### 4 · The graphics plan (the director)
Copy `templates/gfx_slots.py` and `templates/plan.py` into `$E/`. In gfx_slots.py write one slot per graphic, anchored on
the words with `T("phrase")`: name · start → end · layout(s) · builder · what it shows. `python gfx_slots.py` writes
`GRAPHICS.md`. Then fill plan.py (THEME, ACCENT, GFX = `$AI_EDITOR_HOME/projects/<slug>/gfx`, BEDS, PUNCH, CHAPTERS).
```bash
$PY $SK/tools/assemble.py "$E" --plan     # what goes where + the balance line; renders nothing
$PY $SK/tools/logos_in_take.py "$E"       # every brand named, when, and what is on screen then
```
Fix the plan until the balance line ends in ✓ (rules below). Show the creator GRAPHICS.md before building: it is the
cheapest moment to change their mind.

### 5 · Build the graphics (the longest step: hours, not minutes)
- **Cards that land on the words** (level 2): `gfxlib/cards/new_card.py words|vs|grid|detail|pair <gfx>/<name> --cfg …
  --dur <slot> --accent <ACCENT>` (examples in `gfxlib/cards/examples/`). Times inside a card = the word's time in
  words_out.json − the slot's start.
- **Chapter cards + the chapter pill** (level 3): `gfxlib/cards/chapter/chapter_cards.py <gfx> chapters.json --accent …`
  (one 1.8 s card per chapter, and `_pills/` the assembler lays top-left for the rest of each chapter).
- **Icons that draw themselves** (level 3): `gfxlib/cards/icons/make_icons.py <gfx>/<name> --items '[["search","the words",0.2],…]' --flow`.
- **Real screens and pages** (level 5): `tools/screenfollow.py` (a screen recording that zooms and circles the line being
  said; OCR on macOS), `tools/pagebeat.py` and `tools/screenbeat.py` (a page capture: zoom + circle, spotlight, underline),
  `tools/capturebeat.py` (a browser types the URL, the real page loads). Captures: `tools/capture.py <url> <dir>`.
- **3D logos** (level 6): `gfxlib/logo_clip.py <brand>` renders a turning 3D logo once into `AI_EDITOR_HOME/logos3d/`;
  every later video reuses it (LOGOS in gfx_slots.py puts it beside the head). Inside a graphic: `logo3d()` from gfx.js.
- **3D devices, motion blur, depth of field, the exploded view, the beat-synced phone promo** (levels 7–10): the scenes in
  `scenes/` (read `scenes/README.md`: they are dark-theme starting points that need the creator's own images).
- **Stickers and overlays on the face**: `tools/stickers.py subscribe|slash`, `tools/overlays.py logos|ring`.
- **Render** every graphic ONLY with `bash $SK/tools/render.sh <dir> <name> --fonts "Geist,Instrument Serif"`: one render
  at a time on this computer (it holds a lock and waits for any other render). Then LOOK at `renders/<name>-sheet.png` and
  score it 1–10 on readability at phone size, motion, composition, accuracy (the speaker's words, real numbers). Fix the
  three worst things, re-render; ship at 8+, at most 3 rounds.
- **Two helpers in parallel**: send `BRIEFS.md` brief 1 (cards) and brief 2 (diagrams) as background agents with their
  rows of GRAPHICS.md, in priority order (the longest face-only stretches first). They render through the same lock.

### 6 · Assemble (first pass ≈ 25 min; later passes 5–10 min, only changed pieces re-encode)
```bash
$PY $SK/tools/assemble.py "$E"            # → edit/out/final.mp4
```
The face punch-in on every other jump cut; each graphic cut in on its word; `side`/`corner` cards composited with the
face; logo stickers; the chapter pill; graphics not rendered yet are skipped (the face stays); the music bed (`BEDS`, from
`AI_EDITOR_HOME/music/`) about 28 dB under the voice; a whoosh/pop/shutter on each cut-in (from `AI_EDITOR_HOME/sfx/`);
master −16 LUFS, ≤ −1 dBTP, measured on the encoded file. Re-run whenever graphics land; a render written in the last
90 s waits for the next pass (it may still be being written), so "not rendered yet" right after a render is normal.

### 7 · Quality control (≈ 3 min + your eyes)
```bash
$PY $SK/tools/qc.py "$E" 8                # contact sheets every 8 s + the frames either side of every switch
```
LOOK at `out/qc_sheet_*.png` and `out/qc_cuts.png`: every sample is what the plan says; no empty-stage frame at a switch;
no word on screen the speaker didn't say at that moment; picture = sound within a frame (qc prints the Δ).

### 8 · Finish and the publish sheet
```bash
$PY $SK/tools/finish.py "$E"              # renders/<slug>_FINAL.mp4, out/chapters.txt, the loudness check
```
Then write `publish/publish.md` for the creator: three title options (the noun and the number, no hype words), a
description whose first two lines say what the video is, more exact than the video (correct any spoken shortcut there),
the chapters from `out/chapters.txt`, 3 hashtags, tags that include likely misspellings, and a thumbnail brief: find
3–5 outlier videos on the topic (views ÷ that channel's median of its last 30 uploads, ≥ 3×) and describe two
thumbnails on their layouts with the same words. Nothing is uploaded or posted for the creator; they do that.

## The rules (what makes it look like this)
- **Only the speaker's words on screen.** Every word on a card is theirs (from words_out.json) or real UI from a capture.
  No paraphrase that adds words, no invented example text. **Only real numbers**: what they said, or real output labelled
  as replayed. Never a made-up view count, score or "12K likes" in a fake UI.
- **The balance.** FACE (the hook, opinions, reactions, transitions, asks, the verdict, the CTA), BOTH (`side` / `corner`:
  explanations, numbers, comparisons, lists) and GRAPHIC (full frame: showpieces, real pages, chapter cards): each 20–45 %
  of the runtime, aiming at about a third; the face on screen (FACE + BOTH) ≥ 60 %; never more than ~12 s without the face.
  Split a long showpiece: full frame for its key moment, then `side` for the next line.
- **Name it, show it.** Every brand named gets its REAL logo on screen then — in 3D where it fits (`logo3d`, or a
  `logo_clip.py` sticker beside the head), about one logo per 6–10 s at most. Logos come from `gfxlib/logos/` (50 marks
  with sources); a brand that isn't there: fetch its own SVG (press kit, its site, Wikimedia Commons), add it to
  logos.json with its source. Never redraw one.
- **Cut on the waveform, check by ear.** Never cut on transcript timestamps alone; never skip step 3's checks.
- **The voice** is lifted, never processed (`tools/voicechain.py`): no compressor, gate, EQ, noise reduction, loudnorm,
  no speed-up. A computer fan: `FANPRINT` in plan.py (≥ 20 s of room tone), never deeper than −8 dB.
- **One render at a time**, always through `render.sh`. Never kill a process you didn't start.
- **Look before you show.** Every graphic's contact sheet, both QC sheets. Send the creator the file or the sheet, not a
  description of it.

## The look (and how to change it)
The theme lives in ONE place: the `THEMES` block at the top of `gfxlib/gfx.js` (strict JSON between `/*THEMES*/`
markers; `tools/theme.py` reads the same block for the assembler and QC).
- **Warm Cream** (`warmcream`, default): cream ground `#F2ECE1`, warm white cards, ink `#1F1B17`, Instrument Serif
  headlines, Geist labels, one accent (default warm orange `#E0703A`), soft shadows, no glow except on accent strokes.
- **Noir** (`noir`): near-black, red neon accent, glass cards, a mirror floor, capitals.
- Per video: `THEME` and `ACCENT` in plan.py, and the same `data-theme` / `data-accent` on every graphic
  (`new_card.py … --theme … --accent …`). One accent per video: the product's colour when the video is about one product.
- A look of your own: copy the `warmcream` entry in THEMES under a new name, change its colours and `serif`/`case`, and
  pass that name as the theme. Read `STYLE.md` before building any graphic: it is binding.

## Notes become rules
Every note the creator gives on an edit ("the red is too strong", "I'm never on screen") goes into `NOTES.md` as a rule,
with their words and the date, the same day — then applies to every later video. Read NOTES.md before step 1 and before
building graphics. If a note contradicts this file, the note wins. When a note changes a number a tool uses (a threshold,
a level), change the tool too and say so in the note.

## Time and cost (honest)
- **It runs on the creator's own Claude plan** (Claude Code) and their own computer. No paid API is needed by the tools.
  A full edit is a long session, longer with two helper agents; on a smaller plan it can reach the usage limit, so split
  it across sessions: every step writes its output into the project folder, so the next session picks up where it stopped.
- **Computer time** (measured on a 16 GB Apple-silicon laptop): transcription ≈ 4 min per 10 min of take; the cut and
  its checks ≈ 15 min; graphics render at ≈ 1–1.5 min per 20 s of video at 8-sample motion blur; a 10-minute video with
  ~40 graphics takes **hours** of computer time end to end, most of it graphics (one video's 28 graphics took ≈ 3 hours
  of agent time). An older or 8 GB machine is slower; keep to one render at a time.
- **Disk**: the whisper model is 1.5 GB; HyperFrames downloads its own headless Chrome (~200 MB) on the first render unless Google Chrome is installed; each video
  uses a few GB while it is being edited.
- **The first video takes longest**: the logo clips, the chapter look and NOTES.md are reused by every later one.

## Pitfalls (each one cost a video time)
| what went wrong | the rule now |
|---|---|
| removed words survived the cut, a false number among them | cut on the waveform; check the cut by ear (step 3) every time |
| a doubled phrase was transcribed once, so the cut kept it | the verbatim pass (literal_asr.py) on the take AND on the cut |
| an anchor vanished: whisper stamped a word early | words_out.py moves each onset back to the voice; T() finds phrases, not single words |
| the picture drifted 3 frames behind the voice over a long take | assemble_aroll.py trims the picture by frame count and asserts the total |
| a graphic was re-rendered while the assembler read it | the assembler skips files younger than 90 s and works from snapshots |
| two renders started together and one failed | render.sh's lock: one render at a time |
| labels said things the speaker didn't | only their words; a scene's clip must not carry a label from another moment |
| invented numbers in a rebuilt UI | real output only, labelled as replayed |
| the hero's beat-synced moves sat 0.31 s early | check the bass onset on the low band yourself before building on a beat grid |
| a blank cream frame read as a dip at a switch | the assembler starts a graphic on its first frame with something on it (theme.py) |
| the edge light "took over" the frame (noir) | kit.js `noir()` keeps it a whisper; none at all on Warm Cream |
