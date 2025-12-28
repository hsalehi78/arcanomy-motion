# Arcanomy Motion Pipeline - Deep Dive

> A comprehensive breakdown of how this system generates short-form videos for CapCut assembly.

## TL;DR - What This System Does

This is an **AI-powered video kit generator** that takes a claim/idea and produces:
- Background video clips (10s each)
- AI voiceover audio
- SRT captions
- Animated charts (Remotion)
- Thumbnail
- CapCut assembly instructions

The final output is a **kit** that you manually assemble in CapCut - this system does NOT produce a finished video.

---

## Quick Reference: The 11 Pipeline Stages

```
INPUTS                              OUTPUTS
───────────────────────────────────────────────────────────
claim.json + seed.md + chart.json   (your content)
        ↓
1. init         → meta/provenance.json
2. plan         → meta/plan.json (AI: Claude Opus 4.5)
3. visual_plan  → meta/visual_plan.json (AI: Claude Opus 4.5)
4. seed-images  → renders/images/composites/*.png (AI: Kie nano-banana-pro)
5. vidprompt    → meta/video_prompts.json (AI: Claude Opus 4.5)
6. videos       → renders/videos/*.mp4 (AI: Kling 2.5)
7. subsegments  → subsegments/*.mp4 (FFmpeg - placeholder backgrounds)
8. voice        → voice/*.wav (AI: ElevenLabs v3)
9. captions     → captions/captions.srt (FFmpeg silence detection)
10. charts      → charts/*.mp4 (Remotion)
11. kit         → thumbnail/ + guides/ + meta/quality_gate.json
```

---

## Stage-by-Stage Breakdown

### Stage 1: `init`

**What it does:**
- Creates the folder structure
- Writes `meta/provenance.json` with run metadata

**Input files required:**
- `inputs/claim.json` (required)
- `inputs/seed.md` (optional but recommended)
- `inputs/chart.json` (optional)

**Output:**
- `meta/provenance.json` - Immutable run metadata

**Implementation:** `src/pipeline/runner.py`

---

### Stage 2: `plan`

**What it does:**
- Reads seed.md + claim.json + chart.json
- Calls LLM (Claude Opus 4.5 by default) to generate a structured script
- Outputs a plan.json with:
  - 4 segments (hook, proof, implication, landing)
  - 5 subsegments (10 seconds each)
  - Voice text for each subsegment
  - Chart assignments
  - Zoom/overlay instructions

**LLM Prompt:**
- System: `src/prompts/plan_system.md`
- User: Compiled from claim + seed + chart data

**Output:**
```json
{
  "version": "2.1",
  "reel": { "duration_seconds": 50, "subsegment_count": 5 },
  "segments": [...],
  "subsegments": [
    {
      "subsegment_id": "subseg-01",
      "duration_seconds": 10.0,
      "voice": { "text": "..." },
      "visual": { "intent": "..." },
      "charts": [],
      "overlays": [...]
    }
  ]
}
```

**Implementation:** `src/pipeline/planner.py`

**⚠️ POTENTIAL ISSUE:**
If the LLM call fails or returns malformed JSON, this stage crashes. No retry logic.

---

### Stage 3: `visual_plan`

**What it does:**
- Reads `plan.json`
- Calls LLM to generate:
  - `global_atmosphere` - consistent visual style description
  - Image prompts (for DALL-E/Gemini/Kie)
  - Motion prompts (for Kling/Runway)
  - Camera movement instructions

**Output:**
- `meta/visual_plan.json`

**Implementation:** `src/pipeline/visual_plan.py`

**⚠️ POTENTIAL ISSUE:**
- Chart subsegments are filtered out (LLM only handles image-based subsegments)
- The `_enrich_visual_plan()` function adds chart subsegments back, but with null prompts

---

### Stage 4: `seed-images` (assets)

**What it does:**
- Reads `visual_plan.json`
- For each asset, calls image generation API
- Default provider: **Kie (nano-banana-pro)**

**How it works:**
1. Combines `global_atmosphere` + `image_prompt` for each asset
2. Calls `scripts/generate_asset.py` as a subprocess
3. Saves to `renders/images/composites/subseg-XX-asset.png`

**Implementation:** `src/pipeline/assets.py`

**⚠️ POTENTIAL ISSUES:**
1. **Subprocess pattern** - runs `scripts/generate_asset.py` via subprocess, not direct import
2. **5-minute timeout** per image
3. **No retry logic** on failure
4. **Skips chart subsegments** (they have `image_prompt: null`)

---

### Stage 5: `vidprompt`

**What it does:**
- Reads `visual_plan.json`
- Calls LLM to refine motion prompts for Kling/Runway
- Adds video generation metadata

**Output:**
- `meta/video_prompts.json` with clips array

**Implementation:** `src/pipeline/vidprompt.py`

**⚠️ POTENTIAL ISSUE:**
This stage feels redundant - it's just re-prompting the same LLM to refine prompts that were already generated in visual_plan stage.

---

### Stage 6: `videos`

**What it does:**
- Reads `video_prompts.json` (falls back to `visual_plan.json`)
- For each clip, calls Kling API to animate the seed image
- Default: **Kling 2.5 Turbo**

**How it works:**
1. Finds seed image in `renders/images/composites/`
2. Calls `scripts/generate_video.py` as subprocess
3. Saves to `renders/videos/clip_XX.mp4`

**Implementation:** `src/pipeline/videos.py`

**⚠️ POTENTIAL ISSUES:**
1. **15-minute timeout** per video
2. **Requires seed images** - if seed-images stage failed, this blocks
3. **Pre-rendered clips** (charts) are skipped with `movement_type: "pre-rendered"`
4. **Subprocess pattern** again

---

### Stage 7: `subsegments`

**What it does:**
- Reads `plan.json`
- Creates **PLACEHOLDER** background videos using FFmpeg
- Each output is exactly 10.0 seconds

**CRITICAL: This does NOT use the generated videos from stage 6!**

The generated backgrounds are:
- Near-black (#050505) with subtle noise
- Ken Burns-like slow drift
- Purely deterministic

**Implementation:** `src/pipeline/visuals.py`

**⚠️ MAJOR DISCONNECT:**
The videos generated in stage 6 (`renders/videos/clip_XX.mp4`) are NOT used here.
This stage creates **new** placeholder backgrounds, not composites of the AI-generated content.
The AI videos are apparently meant to be manually added in CapCut?

---

### Stage 8: `voice`

**What it does:**
- Reads `plan.json` for voice text
- Calls ElevenLabs TTS API
- Outputs 10-second WAV files (padded/trimmed)

**Provider:** ElevenLabs v3 with "Rachel" voice

**Fallback:** If no API key, generates a deterministic beep tone (for testing)

**Output:** `voice/subseg-XX.wav`

**Implementation:** `src/pipeline/voice.py`

---

### Stage 9: `captions`

**What it does:**
- Reads `plan.json` for voice text
- Uses FFmpeg `silencedetect` on the WAV files to find speech boundaries
- Splits text into caption lines (max 9 words or 42 chars)
- Generates `captions/captions.srt`

**Hard rule:** No caption crosses a 10-second subsegment boundary

**Implementation:** `src/pipeline/captions.py`

---

### Stage 10: `charts`

**What it does:**
- Reads `plan.json` for chart jobs
- Normalizes chart props (10s duration, green screen background)
- Calls Remotion to render animated charts
- Output: `charts/chart-subseg-XX-chart-XX.mp4`

**Remotion Integration:**
- Uses `src/services/chart_renderer.py`
- Chart components in `remotion/src/compositions/`
- Renders with `#00FF00` green screen for CapCut chroma key

**Implementation:** `src/pipeline/charts.py`

---

### Stage 11: `kit`

**What it does:**
- Generates `thumbnail/thumbnail.png` (black bg, white text)
- Generates `guides/capcut_assembly_guide.md`
- Generates `guides/retention_checklist.md`
- Generates `meta/quality_gate.json` (pass/fail validation)

**Quality Gate checks:**
- All subsegment videos exist and are 10.0s
- All voice WAVs exist and are 10.0s
- All chart videos are 300 frames
- Captions don't cross boundaries
- Overlay instructions present
- Zoom plans present (3 per segment)

**Implementation:** `src/pipeline/kit.py`

---

## The Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUTS                                  │
│  claim.json        seed.md           chart.json (optional)      │
│  (the claim)    (hook, insight,      (bar chart props)          │
│                  visual vibe)                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. init                                                        │
│  Creates folder structure + provenance.json                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. plan (LLM: Claude Opus 4.5)                                 │
│  Generates: plan.json                                           │
│  - 5 subsegments with voice scripts                             │
│  - 4 segments with zoom/overlay instructions                    │
│  - Chart assignments                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. visual_plan (LLM: Claude Opus 4.5)                          │
│  Generates: visual_plan.json                                    │
│  - Image prompts for each subsegment                            │
│  - Motion prompts for video generation                          │
│  - Global atmosphere description                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
          ▼                                   ▼
┌─────────────────────┐            ┌─────────────────────┐
│  4. seed-images     │            │  10. charts         │
│  (Kie API)          │            │  (Remotion)         │
│                     │            │                     │
│  Generates PNG      │            │  Renders chart      │
│  images for non-    │            │  animations with    │
│  chart subsegments  │            │  green screen       │
└──────────┬──────────┘            └──────────┬──────────┘
           │                                  │
           ▼                                  │
┌─────────────────────┐                       │
│  5. vidprompt       │                       │
│  (LLM: Claude)      │                       │
│                     │                       │
│  Refines motion     │                       │
│  prompts            │                       │
└──────────┬──────────┘                       │
           │                                  │
           ▼                                  │
┌─────────────────────┐                       │
│  6. videos          │                       │
│  (Kling 2.5 API)    │                       │
│                     │                       │
│  Animates images    │                       │
│  into video clips   │                       │
└──────────┬──────────┘                       │
           │                                  │
           ▼                                  │
┌─────────────────────────────────────────────┴───────────────────┐
│  7. subsegments (FFmpeg)                                        │
│  ⚠️ Creates NEW placeholder backgrounds!                        │
│  Does NOT composite the AI-generated videos!                    │
│                                                                 │
│  Output: subsegments/subseg-XX.mp4 (dark "breathing" backgrounds)│
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. voice (ElevenLabs)                                          │
│  Generates: voice/subseg-XX.wav                                 │
│  10-second audio files with TTS narration                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  9. captions                                                    │
│  Generates: captions/captions.srt                               │
│  Uses silence detection to align text timing                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  11. kit                                                        │
│  Generates:                                                     │
│  - thumbnail/thumbnail.png                                      │
│  - guides/capcut_assembly_guide.md                              │
│  - guides/retention_checklist.md                                │
│  - meta/quality_gate.json                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚨 Identified Issues & Concerns

### 1. **Disconnected AI Video Pipeline**

The biggest issue: Stages 4-6 generate AI images and videos, but stage 7 **ignores them completely** and creates new placeholder backgrounds.

**What the code does:**
- Stage 4: Generates `renders/images/composites/subseg-XX-asset.png`
- Stage 6: Generates `renders/videos/clip_XX.mp4`
- Stage 7: Creates `subsegments/subseg-XX.mp4` from scratch (black backgrounds)

**The AI videos are never composited into the final subsegments.**

The apparent intention is that you manually layer these in CapCut:
- V1: Dark backgrounds (subsegments/*.mp4)
- V2: Chart overlays (charts/*.mp4) - with chroma key
- V3: Captions
- A1: Voice

But the AI-generated images/videos from stages 4-6 are... just sitting there in `renders/`.

### 2. **Subprocess Anti-Pattern**

`assets.py` and `videos.py` call external Python scripts via subprocess:
```python
subprocess.run([sys.executable, str(cli_script), "--prompt", prompt, ...])
```

This is unusual and fragile. Direct imports would be cleaner and more debuggable.

### 3. **Redundant LLM Stages**

The pipeline calls the LLM 3 times for prompt generation:
1. `plan` - generates voice scripts + visual intent
2. `visual_plan` - generates image prompts + motion prompts
3. `vidprompt` - refines motion prompts

Stage 5 (vidprompt) feels redundant - it's just re-processing what stage 3 already generated.

### 4. **Immutability Without Cleanup**

Files are marked "immutable" - they won't be overwritten without `--force`. But there's no cleanup mechanism if you want to regenerate a specific stage. You have to manually delete files or use `--force` everywhere.

### 5. **Error Handling Gaps**

- No retry logic on API failures
- Timeouts (5min for images, 15min for videos) may not be enough
- LLM failures crash the whole pipeline
- No partial recovery - if stage 6 fails halfway, you start over

### 6. **Missing Video Compositing**

The system generates:
- AI background images (`renders/images/`)
- AI animated videos (`renders/videos/`)
- Placeholder backgrounds (`subsegments/`)

But there's no stage that **combines** these. The expectation seems to be manual CapCut assembly, but this isn't documented clearly.

---

## API Dependencies

| Stage | API | Model | Purpose |
|-------|-----|-------|---------|
| plan | Anthropic | claude-opus-4.5 | Script generation |
| visual_plan | Anthropic | claude-opus-4.5 | Image/motion prompts |
| seed-images | Kie | nano-banana-pro | Image generation |
| vidprompt | Anthropic | claude-opus-4.5 | Prompt refinement |
| videos | Kling | v2-5-turbo | Image-to-video |
| voice | ElevenLabs | eleven_v3 | Text-to-speech |

**Required API Keys:**
- `ANTHROPIC_API_KEY`
- `KIE_API_KEY`
- `ELEVENLABS_API_KEY`

**Optional (alternatives):**
- `OPENAI_API_KEY` - for OpenAI models
- `GEMINI_API_KEY` - for Gemini models

---

## File Structure After Pipeline Run

```
content/reels/<reel>/
├── inputs/
│   ├── claim.json         # Your claim (required)
│   ├── seed.md            # Creative brief (recommended)
│   └── chart.json         # Chart props (optional)
├── meta/
│   ├── provenance.json    # Run metadata
│   ├── plan.json          # AI-generated script/structure
│   ├── visual_plan.json   # Image/motion prompts
│   ├── video_prompts.json # Refined video prompts
│   └── quality_gate.json  # Pass/fail validation
├── renders/
│   ├── images/
│   │   └── composites/    # AI-generated images ⚠️ NOT USED IN FINAL OUTPUT
│   │       └── subseg-XX-asset.png
│   └── videos/            # AI-generated videos ⚠️ NOT USED IN FINAL OUTPUT
│       └── clip_XX.mp4
├── subsegments/           # PLACEHOLDER backgrounds (what quality_gate validates)
│   └── subseg-XX.mp4
├── voice/
│   └── subseg-XX.wav
├── captions/
│   └── captions.srt
├── charts/
│   └── chart-subseg-XX-chart-XX.mp4
├── thumbnail/
│   └── thumbnail.png
└── guides/
    ├── capcut_assembly_guide.md
    └── retention_checklist.md
```

---

## Questions for Review

1. **Is the renders/ folder supposed to be used?** The AI generates images and videos there, but the subsegments stage ignores them completely.

2. **What's the intended final video assembly?** The system outputs a "kit" for CapCut, but the relationship between `subsegments/*.mp4`, `renders/videos/*.mp4`, and the final video is unclear.

3. **Why the subprocess pattern?** `generate_asset.py` and `generate_video.py` could be directly imported instead of spawned as subprocesses.

4. **Is the vidprompt stage necessary?** It seems to just re-prompt the LLM on prompts that were already generated.

5. **Should there be a compositing stage?** A stage that layers the AI videos onto the subsegments before final output would make the pipeline more complete.

---

## Recommendations

### Option A: This is Working as Designed
If the intent is truly a "CapCut kit" where humans do the compositing:
- Document this clearly
- Consider removing stages 4-6 since they're not used in the validated output
- Or rename `renders/` to something like `reference_assets/`

### Option B: Add a Compositing Stage
If the AI videos should be in the final output:
- Add a stage between `videos` and `subsegments` that composites them
- Update `subsegments` stage to use `renders/videos/` as backgrounds
- Remove the placeholder background generation

### Option C: Simplify the Pipeline
The current flow is:
1. Generate script (LLM)
2. Generate image prompts (LLM)
3. Generate images (API)
4. Refine video prompts (LLM) ← redundant?
5. Generate videos (API)
6. Create backgrounds (FFmpeg) ← ignores #5?
7. Generate voice (API)
8. Generate captions (FFmpeg)
9. Generate charts (Remotion)
10. Generate kit

A simpler flow might be:
1. Generate script + image prompts (single LLM call)
2. Generate images → videos → composite into subsegments
3. Generate voice → captions
4. Generate charts
5. Generate kit

---

*Generated for review on December 27, 2025*
