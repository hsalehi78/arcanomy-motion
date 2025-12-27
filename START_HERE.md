# Arcanomy Motion — Quick Start Guide

> CapCut-kit pipeline for short-form video production

Run `uv run arcanomy guide` anytime to see this in your terminal.

---

## Quick Start

### Canonical Workflow: Studio Seeds → Motion Kit → CapCut Assembly

Arcanomy Motion does **not** originate reel concepts anymore.
**Arcanomy Studio produces reel seeds**, and Arcanomy Motion converts those seeds into:

- **10.0s assets** (subsegments, charts, voice, captions)
- a **CapCut-ready assembly kit** (guides, thumbnail, quality gate)

CapCut Desktop remains the final editor (canonical doctrine).

### 1) Get a reel seed from Arcanomy Studio

You need these inputs inside a reel folder:

```
content/reels/<reel-id>/
  inputs/
    claim.json      # required
    seed.md         # required
    chart.json      # optional (for data-driven reels)
```

Notes:
- A reel is typically **5–6 subsegments** = **50–60 seconds** (10-second blocks).
- `chart.json` is only needed when the reel benefits from a chart overlay.

```bash
# Run the pipeline on the reel
uv run arcanomy run content/reels/<reel-id>
```

### 2) (Optional) Pro visuals + overrides

Arcanomy Motion supports a “pro” path where it can generate:
- seed images (`renders/images/composites/*.png`)
- 10-second AI video clips (`renders/videos/clip_XX.mp4`)

You can also **override** visuals while learning:
- If you drop in your own `renders/videos/clip_XX.mp4` files, Motion should use them on the next run (and skip regenerating those clips).
- Same idea for seed images in `renders/images/composites/`.

The kit output (voice/captions/charts/guides/quality gate) remains the same.

### 3) Assemble in CapCut

Open `guides/capcut_assembly_guide.md` and follow the instructions.

---

## Pipeline Overview

The pipeline generates a **CapCut-ready assembly kit**, not a final MP4.

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

## Output Structure

```
content/reels/<reel-slug>/
  inputs/
    claim.json           # Required: the sacred claim
    seed.md              # Required: creative brief from Studio
    chart.json           # Optional: chart props (Remotion charts-only)

  meta/
    provenance.json      # Run metadata and hashes
    plan.json            # Segments + subsegments plan
    quality_gate.json    # Pass/fail with reasons

  subsegments/
    subseg-01.mp4        # 10.0s video clips
    subseg-02.mp4
    ...

  renders/               # Optional "pro" assets (if enabled/used)
    images/composites/   # Seed images (inputs to video gen)
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

## CLI Commands

```bash
# Pipeline
uv run arcanomy run                  # Run current reel
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

### Notes on legacy commands

Some legacy commands still exist in the repo for convenience (e.g. blog-based seed creation), but the **canonical path** is:
**Arcanomy Studio generates seeds** → Arcanomy Motion renders the kit → CapCut assembly.

The pipeline uses LLM to transform your Studio seed into a compelling script with:
- Hook that stops the scroll
- Evidence and proof with specific data
- Emotional implication (the stakes)
- Reframe and call to action

Requires an API key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`).

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
# Put Studio seeds in inputs/ (claim.json + seed.md + optional chart.json)
uv run arcanomy run content/reels/<reel-id>
# Open guides/capcut_assembly_guide.md in CapCut Desktop
```
