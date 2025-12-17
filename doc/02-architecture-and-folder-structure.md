# 02 — Architecture & Workflow (Draft)

> **Status:** Draft (intentionally verbose, UX-first). This document prioritizes *clarity of workflow* over elegance. We will refine later.

---

## Goal of This System

Arcanomy Motion exists to reliably turn a **written seed idea** (often derived from an Arcanomy essay) into a **high-quality short video** composed of **multiple 10-second segments**, each with:

- clear narrative purpose
- explicit visual intent
- optional charts (data-driven, auditable)
- shared voice and music

The system is designed so that:
- every step is inspectable
- every artifact can be regenerated
- a human can open a folder and immediately understand what happened

---

## Core Constraints (Non-Negotiable)

1. **Video model constraint:** background video generation happens in **exact 10-second clips**.
2. **Narrative control:** segmentation must be decided *early* (not during rendering).
3. **Auditability:** all data comes from CSV files stored alongside the reel.
4. **Reproducibility:** rerunning any step overwrites its outputs deterministically.
5. **UX over cleverness:** folder structure should be obvious to humans, not optimized for minimal files.

---

## Mental Model (High Level)

A reel is a **container** with two layers:

1. **Reel-wide layer** (things shared across the whole video)
   - research
   - story + script
   - characters / visual identity
   - voice
   - music

2. **Segment layer** (repeated N times)
   - each segment = one 10s block
   - each segment has its own visuals and (optionally) charts

Segments are not an afterthought — they are first-class objects.

---

## Repo-Level Structure (Context)

```
arcanomy-motion/
  docs/
    01-vision-and-reel-types.md
    02-architecture-and-workflow.md  ← this document

  prompts/
    system/
      01_system_research.md
      02_system_story_generator.md
      03_system_character_generation.md
      03.5_system_assets_manifest.md
      04_system_video_prompt_engineering.md
      05_system_voice_prompt_engineer.md
      06_system_music.md
      07_system_assemble_final.md

  scripts/
    run.py
    stages/
      ...

  content/
    reels/
      YYYY-MM-DD-slug-01/
        ...
```

---

## Per-Reel Folder Structure (Draft)

```
content/reels/YYYY-MM-DD-slug-01/
  00_seed.md
  00_reel.yaml
  00_data/
    *.csv

  prompts/                     # text artifacts: what went into / came out of LLM steps

  global/                      # reel-wide rendered or shared assets
    characters/
    style/
    audio/
      voice.mp3
      music.mp3
    frames/
      intro.png
      outro.png

  segments/                    # N segment folders (one per 10s block)
    01/
    02/
    03/
    ...

  assemble/                    # final assembly manifests

  final/
    preview.mp4
    final.mp4
    final.srt
    metadata.json
```

> **Note:** This structure is intentionally verbose. We prefer discoverability over compactness.

---

## Workflow — Step by Step

### Step 0 — Create a Reel

The user manually creates:

```
00_seed.md        # free-form text (essay excerpt, idea, outline)
00_reel.yaml      # settings (models, voice, style toggles)
00_data/*.csv     # optional, auditable numeric inputs
```

No other files exist at this point.

---

### Step 01 — Research (Reel-Wide)

**Purpose:** Turn the seed into grounded research and framing.

- **System prompt:** `prompts/system/01_system_research.md`
- **User content:** `00_seed.md`

Python combines these *verbatim* and writes:

```
prompts/01_research.input.md
```

This file is exactly what is sent to the LLM.

The LLM response is saved as:

```
prompts/01_research.output.md
```

Rerunning this step overwrites both files.

---

### Step 02 — Story Generator (Reel-Wide)

**Purpose:** Produce the full narrative *and* decide segmentation.

This step outputs:
- the **script** (continuous narration)
- the **number of 10s segments**
- a **per-segment intent** (what happens visually and conceptually)

Outputs:

```
prompts/02_story_generator.input.md
prompts/02_story_generator.output.md
prompts/02_story_generator.output.json
```

The JSON is the **source of truth** for:
- number of segments
- per-segment beats
- which segments require charts

---

### Step 03 — Character & Visual Identity (Reel-Wide)

**Purpose:** Define recurring visual elements.

In Arcanomy, “characters” may include:
- a narrator persona (faceless)
- recurring visual motifs
- framing rules (editorial, calm, serious)

Outputs:

```
prompts/03_character_generation.input.md
prompts/03_character_generation.output.md
```

---

### Step 03.5 — Assets Manifest (Bridge Step)

**Purpose:** Translate story + identity into a concrete asset plan.

This step decides:
- intro / outro frames
- how many background videos (one per segment)
- which segments need charts
- music requirements

Output:

```
prompts/03.5_assets_manifest.output.json
```

This file drives **segment folder creation**.

---

### Step 04 — Segment Creation (Structural)

Based on the manifest, Python creates:

```
segments/01/
segments/02/
segments/03/
...
```

Each segment folder is initialized with:

```
segment.yaml          # intent for this 10s block
```

Segments are now first-class units.

---

### Step 04.x — Per-Segment Visual Prompting & Rendering

For **each segment**:

- Generate a video prompt describing the 10s background
- Render a 10s background clip
- Attach chart specs if needed

Example segment folder:

```
segments/02/
  segment.yaml
  prompts/
    video_prompt.input.md
    video_prompt.output.md
  renders/
    bg.mp4
  chart/
    chart_spec.json   # optional
```

Charts are **rendered later inside Remotion** using CSV data.

---

### Step 05 — Voice (Reel-Wide)

- Script → voice instructions
- ElevenLabs generates **one continuous voice track**

```
global/audio/voice.mp3
```

Voice is later sliced per segment during assembly.

---

### Step 06 — Music (Reel-Wide)

- Select or generate background music

```
global/audio/music.mp3
```

---

### Step 07 — Assembly (Final)

Remotion builds the timeline:

- intro frame
- segment 01 (bg + optional chart + voice slice)
- segment 02 …
- outro frame

Outputs:

```
final/final.mp4
final/final.srt
final/metadata.json
```

---

## Open Questions (Intentionally Deferred)

- Should intro/outro frames count toward timing?
- Should segments allow optional start/end still frames?
- How aggressive should per-segment regeneration be?

These will be resolved iteratively.

---

> **Reminder:** This document optimizes for *understandability*, not minimalism. Refinement will come later.
