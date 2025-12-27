# 03 — Seed & Config Format

> **LEGACY (v1) NOTICE:** This document describes `inputs/reel.yaml` and a v1-style seed workflow.  
> **Canonical** inputs today (from Arcanomy Studio) are:
> - `inputs/claim.json`
> - `inputs/seed.md`
> - optional `inputs/chart.json`
>
> See `docs/arcanomy-studio-integration/01-file-formats.md` and `docs/README.md`.

## Overview

In the new architecture, the "Objective" is split into two distinct user-input files:

1.  **`inputs/seed.md`**: The creative brief (Markdown).
2.  **`inputs/reel.yaml`**: The machine configuration (YAML).

These are the **only** files a user must create to start a reel.

---

## 1. `inputs/seed.md` (Creative Brief)

This file captures the *idea*. It is free-text but follows a structure to guide the Agent in Stage 1 & 2.

**Location:** `content/reels/YYYY-MM-DD-slug/inputs/seed.md`

### Required Headers

#### `# Hook`
*The "Grab". What is the first thing the viewer sees or hears?*
> **Example:** "Stop trading until you understand this chart."

#### `# Core Insight`
*The "Meat". What is the single lesson or data point?*
> **Example:** "Retail traders win 60% of trades but lose money overall because their losses are 2x larger than their wins."

#### `# Visual Vibe`
*The "Look". Describe the mood for the image generator.*
> **Example:** "Dark, moody, cinematic. Red and black color palette. Use abstract geometric shapes to represent data."

#### `# Data Sources`
*The "Proof". List any CSV files in `inputs/data/`.*
> **Example:**
> - `inputs/data/trading_psych.csv`

---

## 2. `inputs/reel.yaml` (Machine Config)

This file controls the "mechanical" settings for the pipeline.

**Location:** `content/reels/YYYY-MM-DD-slug/inputs/reel.yaml`

### Schema

```yaml
# METADATA
title: "The Sunk Cost Fallacy"
type: "chart_explainer"   # Options: chart_explainer, text_cinematic, story_essay
duration_blocks: 3        # How many 10-second segments? (3 = 30s)

# AUDIO
voice_id: "eleven_labs_adam"
music_mood: "tense_resolution" # Keywords for music search

# VISUALS
aspect_ratio: "5:4"
subtitles: "burned_in"

# GENERATION SETTINGS
audit_level: "strict"     # strict = fail if data missing; loose = hallucinate OK
```

---

## Why Split Them?

1.  **Clarity:** `seed.md` is for humans (writing prose). `reel.yaml` is for machines (configuration).
2.  **Parsability:** We don't need complex regex to extract settings from Markdown frontmatter. We just load the YAML file.
3.  **Validation:** We can validate `reel.yaml` against a strict schema before reading the creative text.

