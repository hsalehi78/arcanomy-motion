# Arcanomy Motion — Complete Video Generation Pipeline

**Purpose:** This document explains the entire video generation process from start to finish, for audit and second-opinion review.

---

## Executive Summary

Arcanomy Motion is a **Python pipeline** that transforms seed content (text + optional chart data) into a **CapCut-ready assembly kit** for short-form video (Instagram Reels, TikTok, YouTube Shorts).

**KEY POINT:** This pipeline does NOT produce a final MP4. It produces:
- Individual 10-second video clips
- Voice audio files
- Caption files (SRT)
- Chart overlays (green-screen MP4s)
- Thumbnail
- Assembly instructions for CapCut

The final video is assembled **manually in CapCut Desktop** using these assets.

---

## Pipeline Overview (Visual Flow)

```
INPUTS                                   OUTPUTS
═══════════════════════════════════════════════════════════════════════════════

inputs/
├── claim.json      ─────────────────────────────────────────────────────────┐
├── seed.md         ─────────────────────────────────────────────────────────┼─┐
├── chart.json?     ─────────────────────────────────────────────────────────┼─┼─┐
                                                                             │ │ │
        ┌────────────────────────────────────────────────────────────────────┘ │ │
        │    ┌─────────────────────────────────────────────────────────────────┘ │
        ▼    ▼                                                                   │
┌───────────────────┐                                                            │
│  1. PLAN (LLM)    │ ──► meta/plan.json                                         │
│  Claude Opus 4.5  │     (voice scripts, segment structure)                     │
└─────────┬─────────┘                                                            │
          │                                                                      │
          ▼                                                                      │
┌───────────────────┐                                                            │
│  2. VISUAL_PLAN   │ ──► meta/visual_plan.json                                  │
│  (LLM)            │     (image prompts, motion prompts)                        │
└─────────┬─────────┘                                                            │
          │                                                                      │
          ▼                                                                      │
┌───────────────────┐                                                            │
│  3. SEED-IMAGES   │ ──► renders/images/composites/*.png                        │
│  (Kie.ai/DALL-E)  │     (AI-generated seed images)                             │
└─────────┬─────────┘                                                            │
          │                                                                      │
          ▼                                                                      │
┌───────────────────┐                                                            │
│  4. VIDPROMPT     │ ──► meta/video_prompts.json                                │
│  (LLM)            │     (refined motion prompts for Kling)                     │
└─────────┬─────────┘                                                            │
          │                                                                      │
          ▼                                                                      │
┌───────────────────┐                                                            │
│  5. VIDEOS        │ ──► renders/videos/clip_*.mp4                              │
│  (Kling AI)       │     (10-second animated clips from images)                 │
└─────────┬─────────┘                                                            │
          │                                                                      │
          ├─────────────────────────────────────────────────────────────────────┐
          ▼                                                                     │
┌───────────────────┐                                                           │
│  6. SUBSEGMENTS   │ ──► subsegments/subseg-*.mp4                              │
│  (FFmpeg)         │     (10s base video clips - currently just dark bg)       │
└─────────┬─────────┘                                                           │
          │                                                                     │
          ▼                                                                     │
┌───────────────────┐                                                           │
│  7. VOICE         │ ──► voice/subseg-*.wav                                    │
│  (ElevenLabs)     │     (10s audio per subsegment)                            │
└─────────┬─────────┘                                                           │
          │                                                                     │
          ▼                                                                     │
┌───────────────────┐                                                           │
│  8. CAPTIONS      │ ──► captions/captions.srt                                 │
│  (FFmpeg silence) │     (line-level SRT aligned to voice)                     │
└─────────┬─────────┘                                                           │
          │                                                                     │
          ▼         ◄───────────────────────────────────────────────────────────┘
┌───────────────────┐      (if chart.json provided)
│  9. CHARTS        │ ──► charts/chart-*.mp4
│  (Remotion)       │     (10s green-screen chart animations)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  10. KIT          │ ──► thumbnail/thumbnail.png
│  (Pillow)         │     guides/capcut_assembly_guide.md
│                   │     meta/quality_gate.json
└───────────────────┘

                                    ▼

                    ╔═══════════════════════════════════════╗
                    ║  MANUAL: Assemble in CapCut Desktop   ║
                    ║  using guides/capcut_assembly_guide.md ║
                    ╚═══════════════════════════════════════╝
```

---

## Stage-by-Stage Breakdown

### Stage 0: Input Preparation

**Command:** None (manual or fetched from CDN)

**What happens:**
1. Create or fetch three files in `inputs/`:
   - `claim.json` — The core claim (required)
   - `seed.md` — Creative brief with hook, insight, script structure (required)
   - `chart.json` — Remotion chart configuration (optional)

**Files:**

```
inputs/
├── claim.json    # {"claim_id": "...", "claim_text": "...", ...}
├── seed.md       # # Hook\n# Core Insight\n# Visual Vibe\n# Script Structure\n# Key Data
└── chart.json    # {"chartType": "bar", "data": [...], ...}  (optional)
```

---

### Stage 1: Plan Generation (LLM)

**Command:** `uv run plan`

**What happens:**
1. Reads `inputs/claim.json`, `inputs/seed.md`, `inputs/chart.json`
2. Sends to Claude Opus 4.5 with `src/prompts/plan_system.md` system prompt
3. LLM generates structured script with:
   - 5 subsegments (10 seconds each = 50 seconds total)
   - Voice text for each subsegment (25-30 words each)
   - Visual intent descriptions
   - Chart assignment (if chart.json provided, assigns to subseg-02)
4. Enriches with metadata (zoom plans, sound resets)

**Output:** `meta/plan.json`

**Key Data in plan.json:**
```json
{
  "subsegments": [
    {
      "subsegment_id": "subseg-01",
      "beat": "hook_claim",
      "duration_seconds": 10.0,
      "voice": {"text": "The actual voiceover script..."},
      "visual": {"type": "still", "intent": "Visual description..."},
      "word_count": 27
    },
    // ... subseg-02 through subseg-05
  ],
  "segments": [
    {"segment_id": "seg-01", "subsegments": ["subseg-01"], ...}
  ]
}
```

**Dependencies:** `claim.json`, `seed.md`, `chart.json` (optional)

---

### Stage 2: Visual Planning (LLM)

**Command:** `uv run visual_plan`

**What happens:**
1. Reads `meta/plan.json`
2. Sends to Claude Opus 4.5 with `src/prompts/visual_plan_system.md` system prompt
3. LLM generates for each non-chart subsegment:
   - Full DALL-E/Gemini image prompt (detailed, photorealistic)
   - Motion prompt for Kling/Runway (subtle "breathing photograph" movement)
   - Camera movement instruction
4. Skips chart subsegments (they use the chart animation instead)

**Output:** `meta/visual_plan.json`

**Key Data:**
```json
{
  "global_atmosphere": "Late night urban atmosphere, 2 AM quality light...",
  "assets": [
    {
      "id": "subseg-01-asset",
      "subsegment_id": "subseg-01",
      "image_prompt": "Close-up of hands gripping phone, staring at investment app...",
      "motion_prompt": "Subtle breathing movement. Screen glow pulses. Slow zoom in.",
      "camera_movement": "Slow zoom in",
      "suggested_filename": "subseg-01-asset.png"
    }
  ]
}
```

**Dependencies:** `plan.json`

---

### Stage 3: Seed Image Generation (AI)

**Command:** `uv run seed-images`

**What happens:**
1. Reads `meta/visual_plan.json`
2. For each asset, combines `global_atmosphere` + `image_prompt`
3. Calls image generation API (Kie.ai by default, or DALL-E/Gemini)
4. Saves as PNG files

**Output:** `renders/images/composites/subseg-XX-asset.png`

**API Used:** Kie.ai (nano-banana-pro) by default, or OpenAI (gpt-image-1.5), or Gemini

**Dependencies:** `visual_plan.json`

---

### Stage 4: Video Prompt Refinement (LLM)

**Command:** `uv run vidprompt`

**What happens:**
1. Reads `meta/visual_plan.json`
2. Checks which images exist in `renders/images/composites/`
3. Sends to Claude Opus 4.5 with `src/prompts/video_prompt_system.md`
4. LLM refines motion prompts for optimal Kling/Runway results:
   - Core action FIRST
   - Specific details
   - Camera movement LAST

**Output:** `meta/video_prompts.json`

**Key Data:**
```json
{
  "clips": [
    {
      "clip_number": 1,
      "subsegment_id": "subseg-01",
      "seed_image": "renders/images/composites/subseg-01-asset.png",
      "video_prompt": "Subtle breathing movement. Eyes blink once. Slow zoom in.",
      "camera_movement": "Slow zoom in",
      "duration_seconds": 10
    }
  ]
}
```

**Dependencies:** `visual_plan.json`, generated images

---

### Stage 5: Video Generation (AI)

**Command:** `uv run videos`

**What happens:**
1. Reads `meta/video_prompts.json`
2. For each clip, takes the seed image + video prompt
3. Calls Kling AI API (image-to-video)
4. Generates 10-second animated video clip
5. Saves as MP4 files

**Output:** `renders/videos/clip_XX.mp4`

**API Used:** Kling AI (kling/v2-5-turbo-image-to-video-pro)

**Dependencies:** `video_prompts.json`, seed images

---

### Stage 6: Subsegment Background Generation (FFmpeg)

**Command:** `uv run subsegments`

**What happens:**
1. Reads `meta/plan.json` for subsegment count
2. Uses FFmpeg to generate deterministic 10-second "breathing" background clips:
   - Near-black color (#050505)
   - Subtle Ken Burns-like drift
   - Light temporal grain for texture
3. Each clip is exactly 10.0 seconds (validated to ±1 frame at 30fps)

**Output:** `subsegments/subseg-01.mp4` through `subseg-05.mp4`

**⚠️ ISSUE:** These are just dark backgrounds, NOT the AI-generated video clips!

**Dependencies:** `plan.json`

---

### Stage 7: Voice Generation (ElevenLabs)

**Command:** `uv run voice`

**What happens:**
1. Reads `meta/plan.json` for voice text per subsegment
2. For each subsegment, sends text to ElevenLabs TTS API
3. Converts output to WAV format
4. Pads/trims to exactly 10.0 seconds

**Output:** `voice/subseg-01.wav` through `subseg-05.wav`

**API Used:** ElevenLabs (eleven_v3 model, "Rachel" voice by default)

**Fallback:** If no API key, generates stub beep tones

**Dependencies:** `plan.json`

---

### Stage 8: Caption Generation (FFmpeg)

**Command:** `uv run captions`

**What happens:**
1. Reads `meta/plan.json` for voice text
2. Reads `voice/subseg-*.wav` files
3. Uses FFmpeg silencedetect to find speech boundaries
4. Splits text into line-level chunks (max 9 words, 42 chars)
5. Generates SRT with timestamps that:
   - Never cross 10-second subsegment boundaries
   - Are proportionally spaced based on text length

**Output:** `captions/captions.srt`

**Dependencies:** `plan.json`, voice WAV files

---

### Stage 9: Chart Rendering (Remotion)

**Command:** `uv run charts`

**What happens:**
1. Reads `meta/plan.json` for chart jobs
2. For each subsegment with a chart:
   - Normalizes chart props (enforces 10s duration, green-screen background)
   - Calls Remotion CLI to render React-based animated chart
   - Outputs 10-second MP4 with green (#00FF00) background

**Output:** `charts/chart-subseg-02-chart-01.mp4` (and props JSON)

**Dependencies:** `plan.json`, `chart.json`, Remotion project in `remotion/`

**Green-Screen:** Use CapCut's Chroma Key to remove green and overlay on video

---

### Stage 10: Kit Generation (Pillow/Python)

**Command:** `uv run kit`

**What happens:**
1. **Thumbnail:** Generates 1080×1920 PNG with claim text
2. **CapCut Assembly Guide:** Markdown with:
   - Track layout (V1: video, V2: charts, A1: voice, etc.)
   - Per-subsegment instructions
   - Zoom timing, overlay assignments, sound reset placement
3. **Retention Checklist:** 3-2-1 rule compliance checklist
4. **Quality Gate:** JSON with pass/fail status and issues list

**Output:**
- `thumbnail/thumbnail.png`
- `guides/capcut_assembly_guide.md`
- `guides/retention_checklist.md`
- `meta/quality_gate.json`

**Dependencies:** `plan.json`, all previous stage outputs

---

## Complete Output Structure

After running all stages:

```
content/reels/YYYY-MM-DD-slug/
├── inputs/
│   ├── claim.json           # INPUT: Core claim
│   ├── seed.md              # INPUT: Creative brief
│   └── chart.json           # INPUT: Chart config (optional)
│
├── meta/
│   ├── provenance.json      # Run metadata
│   ├── plan.json            # Voice scripts + structure
│   ├── visual_plan.json     # Image/motion prompts
│   ├── video_prompts.json   # Refined video prompts
│   └── quality_gate.json    # Pass/fail status
│
├── renders/
│   ├── images/
│   │   └── composites/
│   │       ├── subseg-01-asset.png    # AI seed images
│   │       ├── subseg-03-asset.png
│   │       └── ...
│   └── videos/
│       ├── clip_01.mp4      # AI-animated clips (from Kling)
│       ├── clip_03.mp4
│       └── ...
│
├── subsegments/
│   ├── subseg-01.mp4        # 10s background clips (dark + drift)
│   ├── subseg-02.mp4
│   └── ...
│
├── voice/
│   ├── subseg-01.wav        # 10s voice audio
│   ├── subseg-02.wav
│   └── ...
│
├── captions/
│   └── captions.srt         # Line-level subtitles
│
├── charts/
│   └── chart-subseg-02-chart-01.mp4   # Green-screen chart animation
│
├── thumbnail/
│   └── thumbnail.png        # 1080×1920 thumbnail
│
└── guides/
    ├── capcut_assembly_guide.md
    └── retention_checklist.md
```

---

## Critical Issues & Observations

### Issue 1: Subsegments vs. Renders Disconnect

**Problem:** The `subsegments/` folder contains dark background videos generated by FFmpeg, NOT the AI-generated clips from `renders/videos/`.

**Evidence:**
- `visuals.py` generates subsegments as dark backgrounds with subtle drift
- The AI clips from Kling are stored in `renders/videos/clip_*.mp4`
- The CapCut guide says to use `subsegments/subseg-*.mp4` on V1

**Expected:** Either:
1. The AI clips should BE the subsegments, OR
2. The assembly guide should tell users to use `renders/videos/clip_*.mp4` instead

**Actual:** Two separate sets of video files exist with unclear relationship.

---

### Issue 2: Missing clip_02

**Observation:** In the sample reel, there's no `clip_02.mp4` in `renders/videos/`.

**Reason:** Subseg-02 is a chart subsegment, so it uses the pre-rendered chart animation instead of an AI-generated video clip. This is correct behavior, but may be confusing.

---

### Issue 3: What Goes on V1?

**Question:** What video should be the background layer in CapCut?

**Options:**
1. `subsegments/subseg-*.mp4` — Dark backgrounds (currently generated)
2. `renders/videos/clip_*.mp4` — AI-animated clips (from Kling)
3. Something else?

**The guides say use subsegments/**, but those are just dark backgrounds. The actual interesting visuals are in `renders/videos/`.

---

### Issue 4: Chart Rendering Dependencies

**Observation:** Chart rendering requires:
1. Node.js installed
2. Remotion project set up in `remotion/`
3. `pnpm install` run in that folder

**Potential Issue:** If Remotion isn't set up, the charts stage will fail.

---

## API Dependencies

| Stage | Provider | Model | Required API Key |
|-------|----------|-------|------------------|
| plan | Anthropic | claude-opus-4-5 | `ANTHROPIC_API_KEY` |
| visual_plan | Anthropic | claude-opus-4-5 | `ANTHROPIC_API_KEY` |
| seed-images | Kie.ai | nano-banana-pro | `KIE_API_KEY` |
| vidprompt | Anthropic | claude-opus-4-5 | `ANTHROPIC_API_KEY` |
| videos | Kling | v2-5-turbo | (via fal.ai or direct) |
| voice | ElevenLabs | eleven_v3 | `ELEVENLABS_API_KEY` |

---

## Commands Quick Reference

```bash
# Full pipeline
uv run plan          # 1. AI generates script
uv run visual_plan   # 2. AI creates image prompts
uv run seed-images   # 3. Generate images
uv run vidprompt     # 4. Refine video prompts
uv run videos        # 5. Generate video clips
uv run subsegments   # 6. Assemble 10s clips (dark backgrounds)
uv run voice         # 7. ElevenLabs TTS
uv run captions      # 8. SRT subtitles
uv run charts        # 9. Animated charts
uv run kit           # 10. Thumbnail + guides

# Or run everything at once:
uv run arcanomy run
```

---

## The 10-Second Rule

Every output is designed around **exactly 10.0 seconds** per subsegment:

| Output | Duration | Tolerance |
|--------|----------|-----------|
| subsegments/*.mp4 | 10.0s | ±1 frame at 30fps |
| voice/*.wav | 10.0s | ±1 frame at 30fps |
| renders/videos/clip_*.mp4 | 10.0s | Variable (API dependent) |
| charts/*.mp4 | 10.0s | ±1 frame at 30fps |

A typical reel is **5 subsegments = 50 seconds**.

---

## What's Missing?

1. **Video composition** — The renders/videos clips are NOT automatically placed as the main video layer
2. **Audio mixing** — No music track is added
3. **Effect application** — Zooms, overlays, transitions are applied manually in CapCut
4. **Final export** — CapCut exports the final MP4

This is BY DESIGN — the pipeline is a "kit generator" for CapCut assembly, not an automated video renderer.

---

## Questions for Second Opinion

1. **Should subsegments/ contain the AI clips or dark backgrounds?**
   - Current: Dark backgrounds
   - Alternative: AI clips from renders/videos/

2. **Is the two-tier video structure (subsegments + renders) intentional?**
   - subsegments/ = background layer
   - renders/videos/ = main visual content
   - Or should these be merged?

3. **Are the assembly instructions clear enough for CapCut?**
   - Should the guide explicitly say "use renders/videos/ for main visuals"?

4. **Is the 10-stage pipeline too complex?**
   - Could some stages be merged?
   - Are all stages necessary?

5. **What happens when APIs fail?**
   - Some stages have fallbacks, others don't
   - Is error handling sufficient?

---

## Conclusion

The pipeline is a **complex 10-stage process** that generates individual assets for manual assembly in CapCut. The design philosophy prioritizes:

1. **Modularity** — Each stage has a single responsibility
2. **Immutability** — Outputs are not overwritten without `--force`
3. **Determinism** — Reproducible results (where possible)
4. **10-second atomic blocks** — Everything aligns to 10s subsegments

**Potential Issues:**
- The relationship between `subsegments/` and `renders/videos/` is unclear
- The final composition is entirely manual in CapCut
- Multiple AI API dependencies create points of failure

The system works but may benefit from clearer documentation on how the various video outputs should be assembled.
