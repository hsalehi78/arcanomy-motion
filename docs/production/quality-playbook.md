# Quality Playbook (Worldclass Reels)

This is the practical “how to ship daily” mapping from `docs/principles/` to what Arcanomy Motion outputs and what you do in CapCut.

---

## What Arcanomy Motion Guarantees

- **10.0s blocks**: `subsegments/subseg-XX.mp4` are exactly 10 seconds each.
- **Charts-only Remotion overlays**: `charts/chart-subseg-XX-*.mp4` are 10 seconds and green-screen (`#00FF00`) for CapCut chroma key.
- **Voice per block**: `voice/subseg-XX.wav` aligned to a 10-second timeline.
- **Captions**: `captions/captions.srt` is line-level, voice-aligned, and never crosses 10-second boundaries.
- **Assembly instructions**: `guides/capcut_assembly_guide.md` + `guides/retention_checklist.md`.
- **Quality gate**: `meta/quality_gate.json` tells you pass/fail and exactly what’s missing.

---

## What You Do in CapCut (Operator Loop)

Follow `guides/capcut_assembly_guide.md`. The goal is **mechanical execution** only.

### Track layout (canonical)

- **V1**: `subsegments/subseg-XX.mp4` (background/base)
- **V2**: chart overlays `charts/*.mp4` (apply chroma key to remove `#00FF00`)
- **V3**: captions + overlays (CapCut preset)
- **A1**: voice `voice/subseg-XX.wav`
- **A2**: music (manual selection)
- **A3**: sound resets (manual placement from a fixed library)

### Captions (doctrine)

- Import `captions/captions.srt`
- Apply the Arcanomy captions preset (yellow text + black stroke + glow + keyword highlighting)
- Keep the bottom UI safe zone clear

---

## The 3–2–1 Retention Rule (Non-negotiable)

Per segment:
- **3 zooms**: apply at the timestamps listed in the guide (these are instructions, not auto-keyframed)
- **2 overlays**:
  - 1 informational max (chart or one key image)
  - 1 emotional (emoji)
- **1 sound reset**: at each segment boundary

Motion encodes these as instructions in the guide and validates **presence** in `meta/quality_gate.json`.

---

## “Pro Mode” (Optional): Better visuals while learning

Pro mode is the pipeline path that produces:
- seed images: `renders/images/composites/*.png`
- 10-second AI video clips: `renders/videos/clip_XX.mp4`

### Overrides (recommended while learning)

If you already have a better clip:
- drop it in `renders/videos/clip_XX.mp4`
- rerun the pipeline
- Motion should keep using your clip and still produce voice/captions/charts/guides/quality gate

---

## Practical quality checks (fast)

- **Frame 0 readability**: can you read the hook instantly?
- **Mobile scale**: zoom to 25% and verify legibility
- **Chart readability**: 2–6 items max, labels short
- **No caption clutter**: one thought per line, safe zone respected
- **No “creative decisions” in CapCut**: only execute the kit

