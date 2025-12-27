# Arcanomy Motion — Pipeline Documentation

## Purpose

Arcanomy Motion converts **Arcanomy Studio reel seeds** into **CapCut-ready assembly kits** for short-form video reels.

**Output:** Subsegments, charts, voice, captions, thumbnail, and assembly guides.  
**Assembly:** Manual in CapCut Desktop (not automated MP4 export).

---

## Canonical Doctrine

All design decisions are governed by **`docs/principles/`**:

- `arcanomy-reels-operating-system.md` — The distribution doctrine (mandatory rules)
- `CapCut_Assembly_Guide.md` — Track layout and assembly steps

### Key Rules

1. **10.0s atomic subsegments** — Every video block is exactly 10 seconds
2. **CapCut is the final editor** — We generate assets, you assemble
3. **Remotion is charts-only** — No full composition, no caption burn-in
4. **3–2–1 retention rule** — 3 zooms, 2 overlays, 1 sound reset per segment
5. **Captions** — Line-level SRT, CapCut applies the styling preset

---

## Pipeline Overview

```
INPUTS                          PIPELINE                         OUTPUTS
─────────────────────────────────────────────────────────────────────────────
inputs/claim.json    ──┐
inputs/seed.md       ──┤──►  init ──► plan ──► subsegments ──► voice
inputs/chart.json?   ──┘                            │
                                                    ▼
                                              captions ──► charts ──► kit
                                                                      │
                                                                      ▼
                                                              CapCut Assembly
                                                              (manual)
```

### Stages

| Stage | Command | Output |
|-------|---------|--------|
| **init** | `--stage init` | `meta/provenance.json` |
| **plan** | `--stage plan` | `meta/plan.json` |
| **subsegments** | `--stage subsegments` | `subsegments/subseg-*.mp4` |
| **voice** | `--stage voice` | `voice/subseg-*.wav` |
| **captions** | `--stage captions` | `captions/captions.srt` |
| **charts** | `--stage charts` | `charts/chart-*.mp4` |
| **kit** | `--stage kit` (default) | `thumbnail/`, `guides/`, `meta/quality_gate.json` |

---

## Quick Start

### Canonical: Studio Seeds → Motion Kit → CapCut Assembly

Arcanomy Studio produces the seed files. Arcanomy Motion renders the kit.

Required inputs (from Studio):
- `inputs/claim.json`
- `inputs/seed.md`

Optional inputs (from Studio):
- `inputs/chart.json` (for chart overlays)

A reel is typically **5–6 subsegments** = **50–60 seconds** (10-second blocks).

```bash
# Run the pipeline on a reel folder
uv run arcanomy run content/reels/<reel-id>
```

### Pro Mode (Optional): Visual Planning + Seed Images + 10s AI Clips

Motion supports an optional “pro” path driven by system prompts:
- `meta/visual_plan.json` (image + motion prompts)
- `renders/images/composites/*.png` (seed images)
- `meta/video_prompts.json` (refined prompts)
- `renders/videos/clip_XX.mp4` (10-second clips)

**Overrides while learning:** if a `renders/videos/clip_XX.mp4` file already exists, Motion should use it (skip regeneration) and still produce the CapCut kit.

### 3. Run the pipeline

```bash
# Run the current reel:
uv run arcanomy run

# With AI script generation:
uv run arcanomy run --ai

# Pick a different reel first:
uv run arcanomy reels
uv run arcanomy run --ai
```

### 4. Assemble in CapCut

Open `guides/capcut_assembly_guide.md` and follow the instructions.

---

## Output Structure

```
content/reels/<reel-slug>/
  inputs/
    claim.json           # Required: the sacred claim
    seed.md              # Required: creative brief from Studio
    chart.json           # Optional: Remotion chart props (charts-only)

  meta/
    provenance.json      # Run metadata and hashes
    plan.json            # Segments + subsegments plan
    quality_gate.json    # Pass/fail with reasons

  subsegments/
    subseg-01.mp4        # 10.0s video clips
    subseg-02.mp4
    ...

  renders/               # Optional "pro" assets (if enabled/used)
    images/composites/   # Seed images
    videos/              # 10s AI clips (clip_XX.mp4)

  voice/
    subseg-01.wav        # Voice per subsegment (10.0s)
    subseg-02.wav

  captions/
    captions.srt         # Line-level, voice-aligned

  charts/
    chart-subseg-02-chart-01.json  # Props
    chart-subseg-02-chart-01.mp4   # 10.0s render

  thumbnail/
    thumbnail.png        # 1080x1920

  guides/
    capcut_assembly_guide.md
    retention_checklist.md
```

---

## Chart Templates

See **`docs/charts/`** for JSON templates and example videos.

Chart types available:
- Bar chart (basic, comparison, highlight, ranking, timeline, negative)
- Horizontal bar chart
- Stacked bar chart
- Line chart
- Pie chart
- Scatter chart
- Number counter
- Progress chart

Usage:
```bash
uv run arcanomy render-chart docs/charts/bar-chart-basic.json
```

---

## CLI Reference

```bash
# Pipeline
uv run arcanomy run                  # Run current reel
uv run arcanomy run --ai             # Run with AI script generation
uv run arcanomy run -s plan          # Run to specific stage
uv run arcanomy run --fresh          # Wipe and rerun
uv run arcanomy status               # Show pipeline status

# Utilities
uv run arcanomy current              # Show current reel
uv run arcanomy set <path>           # Set current reel
uv run arcanomy preview              # Start Remotion preview
uv run arcanomy render-chart <json>  # Render standalone chart
uv run arcanomy guide                # Show help
```

### AI Script Generation (NEW)

Use `--ai` to enable AI-powered script generation from your claim:

```bash
# Pick a reel and run with AI:
uv run arcanomy reels
uv run arcanomy run --ai

# Or directly with partial name matching:
uv run arcanomy run my-reel --ai
```

The AI scriptwriter:
- Transforms your claim into a compelling 50-second script
- Follows the Arcanomy dramatic arc (Hook → Support → Implication → Landing)
- Generates 25-30 words per subsegment (optimized for 10s of speech)
- Names the psychological trap or fallacy being exposed

See `docs/plans/ai-reel-creation.md` for implementation details.

---

## Archived Documentation

Legacy V1 pipeline docs are in **`docs/_archive/`**.

These describe the old FFmpeg-based auto-assembly pipeline which is no longer the default.
The code is preserved in **`src/_archive/`** for reference.

---

## Principles

See **`docs/principles/`** for the canonical operating doctrine:

- **arcanomy-reels-operating-system.md** — The rules. Non-negotiable.
- **CapCut_Assembly_Guide.md** — How to assemble in CapCut.

The pipeline exists to serve these principles, not the other way around.

## Production Quality

If you’re still learning to make pro reels, start here:
- `docs/production/quality-playbook.md`
