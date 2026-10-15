# The two helper briefs

A 10-minute video needs 25–45 graphics. You (the main session) build the 3D scenes, the chapter cards, the logos and the
real pages; two background agents build the rest in parallel: **cards** (kinetic type, UI cards, CTAs) and **diagrams**
(explainers, flows, code). Fill in the `{…}` and send each brief as an Agent prompt that runs in the background. Give
them their rows in priority order (the longest face-only stretches first), so the cut fills up from the biggest gaps.
One video's 28 graphics took about 3 hours of agent time this way.

Before sending: the cut is final (step 3's checks clean), `work/words_out.json` exists, and `python gfx_slots.py` has
written GRAPHICS.md (name · slot start → end · layout · the exact words in the slot · what it shows).

---

## Brief 1 — cards and kinetic type

You are building the CARDS for a video: "{title}", theme **{theme}** (Warm Cream unless plan.py says noir), accent
**{accent}**. The skill is at {SK}; AI_EDITOR_HOME is {HOME}; run Python as {PY}. Read, in this order:
1. `{SK}/NOTES.md` (the creator's rules: they win), then `{SK}/STYLE.md` — binding, "The theme" first. Every graphic's root
   element is `<html lang="en" data-theme="{theme}" data-accent="{accent}">` and gfx.js is copied FRESH into its `assets/`
   (`gfxlib/cards/new_card.py` does both). Colours ONLY through the theme's CSS variables, `shadow(blur, y)` for panel
   shadows, never a hex colour in a template. Headlines in `var(--display)`, labels in Geist; sentence case, the words as
   said. **Logos**: every brand named in your slot shows its REAL logo, in 3D where it fits (`logo3d` from gfx.js; copy the
   SVGs you need from `{SK}/gfxlib/logos/` into the card's `assets/logos/`), or `logoSVG(...)` in a tag. Never redraw one.
   Each slot says its LAYOUT: a `corner` card keeps its bottom-right ~30 % × 30 % free; a `side` card is seen at 65 %
   (headline ≥ 90 px, body ≥ 48 px); a `graphic` slot is full frame.
2. `{SK}/engine/ENGINE.md` — the engine, and `{SK}/gfxlib/` — start from the templates (`new_card.py words|vs|grid|detail|pair`,
   examples in `cards/examples/`), line icons from `cards/icons/make_icons.py`.

Deliver each card to `{GFX}/<name>/renders/<name>.mp4`, 1920×1080, silent, `data-duration` = its slot.
The slots, in PRIORITY ORDER:
{rows of GRAPHICS.md for builder A}

Rules that are not negotiable:
- **Only the speaker's words on screen** — from `{E}/work/words_out.json` (`w` = word, `t` = output seconds). No paraphrase
  that adds words, no fact they didn't say, no invented example text. **No invented numbers** — not in a headline, not in
  a rebuilt UI. Real UI chrome from captures is fine.
- Time the beats to the words: a card's key word lands when it is said (its `t` minus the slot's start).
- Render ONLY with `bash {SK}/tools/render.sh <dir> <name> --fonts "Geist,Instrument Serif"` (one render at a time on
  this computer; it waits its turn). Never kill a process you didn't start.
- Critique loop per STYLE.md: contact sheet → score 1–10 on readability, motion, composition, premium, accuracy → fix the
  three worst → re-render, until all 8+, at most 3 rounds.
- **Ship each card the moment it passes** — the assembler picks up new renders on its next pass (it ignores files touched
  in the last 90 s, so re-rendering a shipped card is safe).
Report: a table — name · duration · last round · the five scores — and every place you deviated from the brief.

---

## Brief 2 — diagrams and explainers

You are building the DIAGRAMS for a video: "{title}", theme **{theme}**, accent **{accent}** — the parts that explain how
something works: flows, pipelines, before/after, a formula, code, a real terminal replayed. Read NOTES.md, STYLE.md,
ENGINE.md and gfxlib exactly as in Brief 1 (the theme rules are the same). For a list or a process,
`gfxlib/cards/icons/make_icons.py` (icons drawn in the accent, with `--flow`) is often the right start; for a screen
recording, `tools/screenfollow.py`; for a real page, `tools/pagebeat.py` / `screenbeat.py`; for a 3D look, a scene from
`scenes/` (read its README: they are dark-theme starting points).

Deliver to `{GFX}/<name>/renders/<name>.mp4`. The slots, in PRIORITY ORDER:
{rows of GRAPHICS.md for builder B}

Rules: everything in Brief 1, and —
- Real material only: real code, real tool output (label a replay "Real output · replayed"), real captures. Third-party
  footage or frames carry an on-screen credit (`@handle · TikTok`).
- A replayed terminal shows only lines the tools really printed — no scores or stats written for the shot.
- A diagram's nodes use the speaker's words for their labels.
- Long explainers (> 20 s) need a change every 1–2 s (a node lights, the camera moves, a value fills in) — never a static
  diagram held while they talk.
Report: name · duration · scores · decisions the main session should check (credits, labels, timing choices).
