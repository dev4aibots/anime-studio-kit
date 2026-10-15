# Notes → rules

Read this file before every edit. Each note the creator gives on an edit becomes a rule here, the same day, and applies
to every video after it. A note here overrides SKILL.md and STYLE.md. Keep them short: the date, the note in their own
words, the rule, and what changed (a tool, a template, a number) so it can be undone.

Format:

    ## YYYY-MM-DD — "<the note, in their words>"
    Rule: <what to do from now on, as an instruction>
    Changed: <the file / setting it touched, or "nothing — a habit">

---

## Example (delete it once you have your own) — "I am almost never on screen, there are way too many graphics"
Rule: keep the balance — face alone, graphic with face, graphic alone, about a third each; my face on screen at least 60 %
of the video; never more than 12 seconds without my face. Opinions, reactions and the call to action stay on my face.
Changed: nothing — `assemble.py --plan` already prints the balance; fix the plan until it says ✓.

## Example (delete it once you have your own) — "The glow on the edges is way too strong"
Rule: no edge light at all in Warm Cream; in Noir, the edge light stays a whisper (base 0.015, never above 0.06).
Changed: nothing — kit.js `noir()` and gfx.js `world()` already enforce it.
