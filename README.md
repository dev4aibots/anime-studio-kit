# anime-studio-kit

**One command installs the entire pure-code JS anime pipeline** — every skill, library, framework and repo needed to generate anime videos (MP4) with voice and music (MP3/WAV), using only deterministic hand-written JavaScript. No generative video, no AI slop. Built for [OpenCode](https://opencode.ai).

```bash
git clone https://github.com/dev4aibots/anime-studio-kit
cd anime-studio-kit
bash install.sh
```

That's it. `install.sh` checks prerequisites, clones everything, installs all npm packages, and registers 11 skills in OpenCode.

## What gets installed

### Skills (in OpenCode, auto-active)
| Skill | What it teaches |
|---|---|
| `js-animation` | Zero-asset canvas films: storyboard-as-data, pure-function-of-time frames, deterministic RNG, self-check loop |
| `js-soundtrack` | Code-synthesized scores (Web Audio), beat-accurate cuts, sync-check |
| `kinetic-typography` | Kinetic subtitles and title cards |
| `gsap-timeline` / `gsap-core` / `gsap-performance` / `gsap-plugins` | Official GSAP skills (16.4k★) — timelines, best practices, render performance |
| `animation-principles` / `beat-sync-editing` / `shot-composition` | Professional motion craft |
| `ai-video-editor` | three.js 3D engine: 8-sample motion blur, true depth of field, camera rig (slam/whip/punch/rack focus) on HyperFrames |

### Repositories cloned (`~/anime-studio/jsmotion/`)
- `yihui-dev/awesome-opus5-5-videos` — 703 code-animation prompts & patterns
- `BowTiedSwan/animejs-skills` — Anime.js v4 guidance
- `cth9191/animate` — procedural art systems (pixel, riso, crosshatch, cut-paper, sketchbook, isometric…)
- `met4citizen/HeadTTS` — Kokoro TTS with phoneme timestamps + Oculus visemes (JS)
- `met4citizen/TalkingHead` — real-time lip-sync modules (JS)
- `iart-ai/javascript-animation-skills`, `kinetic-typography-skills`, `motion-design-skills`, `webgl-animation-skills`
- `greensock/gsap-skills`

### npm libraries (`~/anime-studio/jsmotion/pipeline/`)
Video: `hyperframes`, `mediabunny` (pure-TS MP4 mux), `@webav/av-cliper` (WebCodecs editor SDK), `@diffusionstudio/core`.
Audio: `kokoro-js` (local neural TTS), `zzfx` (procedural SFX), `rhubarb-lip-sync-wasm` (visemes), `spessasynth` (SoundFont scoring).
Animation: `gsap`, `animejs`, `@mojs/core`, `three`, `pixi.js`, `pixi-particle-system`.

## The pipeline

```
story (JS storyboard-as-data)
  → animation (Canvas/SVG/WebGL + GSAP timelines, pure function of time)
  → render (HyperFrames headless Chrome, --no-low-memory-mode -w 2)
  → voice (Kokoro/Qwen3-TTS) + music (Web Audio synth) + SFX
  → mux (ffmpeg) → MP4
  → verify (full decode, specs, black-frame scan, contact-sheet QC)
```

Key rules (enforced by the skills):
- **Pure code only.** Every pixel computed, every sound synthesized. No generative AI in the pipeline.
- **Deterministic.** Seeded RNG, no `Math.random`, frames are a pure function of time — render and preview always agree.
- **Verify before delivery.** Full stream decode, never header reads.

## Requirements
- Node 18+, npm, Python 3, ffmpeg, git
- Linux/macOS/WSL, CPU-only is fine (no GPU needed)

## License
MIT — except vendored skills, which keep their own licenses (see each skill's folder; all MIT/ISC/Apache-2.0/OFL).
