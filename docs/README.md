# Arcanomy Motion — Pipeline Documentation

## Purpose

Arcanomy Motion generates **CapCut-ready assembly kits** for short-form video reels.

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
                       ├──►  init ──► plan ──► subsegments ──► voice
inputs/data.json     ──┘                            │
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

### 1. Create a new reel

```bash
uv run arcanomy new my-reel-slug
```

This creates:
- `content/reels/YYYY-MM-DD-my-reel-slug/inputs/claim.json`
- `content/reels/YYYY-MM-DD-my-reel-slug/inputs/data.json`

### 2. Edit the inputs

**claim.json** (required):
```json
{
  "claim_id": "my-reel",
  "claim_text": "The average person wastes 10 years waiting for the right moment.",
  "supporting_data_ref": "ds-01",
  "audit_level": "basic"
}
```

**data.json** (required, even if empty):
```json
{
  "type": "none",
  "datasets": [],
  "charts": []
}
```

### 3. Run the pipeline

```bash
uv run arcanomy run content/reels/YYYY-MM-DD-my-reel-slug
```

### 4. Assemble in CapCut

Open `guides/capcut_assembly_guide.md` and follow the instructions.

---

## Output Structure

```
content/reels/<reel-slug>/
  inputs/
    claim.json           # Required: the sacred claim
    data.json            # Required: chart data (or type: "none")
    seed.md              # Optional: personal notes

  meta/
    provenance.json      # Run metadata and hashes
    plan.json            # Segments + subsegments plan
    quality_gate.json    # Pass/fail with reasons

  subsegments/
    subseg-01.mp4        # 10.0s video clips
    subseg-02.mp4
    ...

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
uv run arcanomy new <slug>           # Create new reel
uv run arcanomy run <path>           # Run full pipeline
uv run arcanomy run <path> -s plan   # Run to specific stage
uv run arcanomy run <path> --fresh   # Wipe and rerun
uv run arcanomy status <path>        # Show pipeline status
uv run arcanomy reels                # List/select reels
uv run arcanomy current              # Show current reel
uv run arcanomy set <path>           # Set current reel
uv run arcanomy preview              # Start Remotion preview
uv run arcanomy render-chart <json>  # Render standalone chart
uv run arcanomy guide                # Show help
```

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

