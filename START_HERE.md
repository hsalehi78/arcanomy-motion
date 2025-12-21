# Arcanomy Motion — Quick Start Guide

> CapCut-kit pipeline for short-form video production

Run `uv run arcanomy guide` anytime to see this in your terminal.

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

Or set the reel as current and run:
```bash
uv run arcanomy set my-reel-slug
uv run arcanomy run
```

### 4. Assemble in CapCut

Open `guides/capcut_assembly_guide.md` and follow the instructions.

---

## Pipeline Overview

The pipeline generates a **CapCut-ready assembly kit**, not a final MP4.

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

## CLI Commands

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

## Chart Rendering

Render animated charts from JSON templates:

```bash
uv run arcanomy render-chart docs/charts/bar-chart-basic.json
```

See `docs/charts/` for all templates and documentation.

---

## Documentation

| File | Purpose |
|------|---------|
| `docs/README.md` | Full pipeline documentation |
| `docs/charts/` | Chart templates and JSON schema |
| `docs/principles/` | Operating doctrine and assembly rules |

---

## Environment Setup

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY`)
   - `ELEVENLABS_API_KEY`

---

**Ready to start?**

```bash
uv run arcanomy new my-first-reel
# Edit inputs/claim.json and inputs/data.json
uv run arcanomy run
# Open guides/capcut_assembly_guide.md in CapCut
```
