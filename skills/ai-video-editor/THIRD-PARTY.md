# Third-party material: what is in this folder, what the setup downloads, and under which terms

## In this folder
| what | where | source | terms |
|---|---|---|---|
| 96 line icons | `gfxlib/cards/icons/lucide/` | lucide-static 0.454.0 (lucide.dev) | ISC licence (`lucide/LICENSE`) |
| 50 brand marks | `gfxlib/logos/` | Simple Icons 15.22.0 (most), Wikimedia Commons (DeepSeek: MIT; Grok, xAI, Microsoft, Adobe After Effects: public domain), the HyperFrames repository (Apache-2.0) — every file's source is in `logos.json` | the icon data is free to use; the marks are their owners' trademarks: use them to name the product you talk about, never to suggest the brand endorses you |

## Downloaded by the setup, from the original source (not redistributed here)
| what | from | terms |
|---|---|---|
| HyperFrames 0.8.137 (renders HTML to video) | npm | Apache-2.0. It downloads its own headless Chrome on the first render (Google's terms) |
| three.js 0.181.2 (3D) | npm | MIT |
| GSAP 3.14.2 (animation timelines) | npm | GreenSock "Standard No Charge" licence: gsap.com/standard-license |
| Fonts: Geist, Instrument Serif, Roboto, JetBrains Mono, Fraunces | Google Fonts (woff2) and the google/fonts repository (ttf + OFL.txt) | SIL Open Font License 1.1 |
| iPhone and MacBook 3D models | the HyperFrames registry block `vfx-iphone-device` (github.com/heygen-com/hyperframes, pinned commit, sha256-checked) | the repository is Apache-2.0; the models' own origin isn't documented in the block, so they are fetched from there rather than copied into this pack |
| whisper.cpp + the `ggml-medium.en` model | Homebrew (`whisper-cpp`) and huggingface.co/ggerganov/whisper.cpp | MIT (whisper.cpp; OpenAI's Whisper weights) |
| ffmpeg | Homebrew | LGPL/GPL, depending on the build |
| numpy, Pillow, opencv-python-headless (+ playwright, optional) | PyPI | BSD / MIT-CMU / Apache-2.0 (Apache-2.0) |

## Not included, on purpose
- **Music and sound effects.** Use tracks and effects you have a licence for, and put them in `AI_EDITOR_HOME/music/` and
  `AI_EDITOR_HOME/sfx/<whoosh|pop|shutter|riser>/`. A free option is Mixkit (mixkit.co/free-stock-music and
  mixkit.co/free-sound-effects). In Mixkit's own words (mixkit.co/license, read 12 October 2026): music under its Stock
  Music Free License "can be used in your commercial and non-commercial projects for free", YouTube videos included (if a
  claim comes in, they ask you to forward it to them), but not in CDs/DVDs, TV or radio, or video games, not remixed into a
  music-only track, and not claimed as your own or registered on a rights-management service. Sound effects under its
  Sound Effects Free License can't be redistributed "on its own, as stock, in a tool or template" — which is why none ship
  with this pack. Check the licence page of whatever you download; terms change.
- Any image of a real person, and any generated imagery.
