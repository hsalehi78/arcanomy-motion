# 04 — Pipeline Stages (Detailed)

## Philosophy: Granular Audit Trail

We strictly follow the **"Smart Agent + Dumb Scripts"** model:
- **Smart Agent Stages** = LLM plans, writes prompts, makes creative decisions
- **Dumb Script Stages** = Automated execution of API calls, no creativity

The pipeline is broken down into granular steps. Each step has a clear **Input** (Prompt) and **Output** (Result).

The state of a reel is defined entirely by the files in its folder. To "resume" a reel, the orchestrator simply checks which files already exist.

---

## The Pipeline Overview

| Stage | Type | Goal | Key Output |
|-------|------|------|------------|
| 0 | Manual | Initialize reel | `00_seed.md`, `00_reel.yaml` |
| 1 | Agent | Research & fact-check | `01_research.output.md` |
| 2 | Agent | Write script & segment | `02_story_generator.output.json` |
| 3 | Agent | Visual plan + image prompts | `03_visual_plan.output.json` |
| 3.5 | Script | Generate images | `renders/images/*.png` |
| 4.5 | Script | Generate video clips | `renders/videos/*.mp4` |
| 5 | Agent | Voice direction | `05_voice.output.md` |
| 5.5 | Script | Generate audio | `renders/voice_*.mp3` |
| 6 | Agent | Music & SFX selection | `06_music.output.json` |
| 7 | Script | Final assembly | `final/final.mp4` |

---

## Stage 0: Initialization
**Type:** Manual Input by User

**Goal:** Define the reel concept and configuration.

**Files:**
- `00_seed.md`: The creative spark, concept, or raw notes.
- `00_reel.yaml`: Configuration (Duration, Voice ID, Music Vibe, Aspect Ratio).
- `00_data/`: Optional CSV files for data-driven reels.

---

## Stage 1: Research
**Type:** Smart Agent

**Goal:** Ground the seed concept in facts and identify the "angle".

**Agent Action:** Reads seed + data. Browses web (if enabled). Generates a research summary.

**Files:**
- `01_research.input.md` (The prompt sent to the LLM)
- `01_research.output.md` (The research notes and key takeaways)

**System Prompt:** `shared/prompts/01_research_system.md`

---

## Stage 2: Story & Segmentation
**Type:** Smart Agent

**Goal:** Write the script and divide it into 10-second blocks.

**Agent Action:** Writes a voiceover script and splits it into strict time blocks, each with a `visual_intent` description.

**Files:**
- `02_story_generator.input.md`
- `02_story_generator.output.md` (Human-readable script)
- `02_story_generator.output.json` **(CRITICAL)**: Structured list of segments.

```json
{
  "title": "The Perfect Timing Fallacy",
  "total_duration_seconds": 20,
  "segments": [
    { "id": 1, "duration": 10, "text": "...", "visual_intent": "...", "word_count": 30 },
    { "id": 2, "duration": 10, "text": "...", "visual_intent": "...", "word_count": 30 }
  ]
}
```

**System Prompt:** `shared/prompts/02_script_system.md`

---

## Stage 3: Visual Plan & Asset Prompts
**Type:** Smart Agent

**Goal:** Create the complete visual plan INCLUDING all image generation prompts.

**Agent Action:**
1. Analyzes script segments and their `visual_intent`
2. Creates an Asset Manifest (list of all required images)
3. Maps each segment to its asset(s)
4. Writes Global Atmosphere Block (consistency engine)
5. Writes complete image prompts (ready for DALL-E/Midjourney)
6. Writes video motion prompts (ready for Kling/Runway)

**Files:**
- `03_visual_plan.input.md`
- `03_visual_plan.output.md` (Human-readable plan with all prompts)
- `03_visual_plan.output.json` **(CRITICAL)**: Machine-readable asset manifest.

```json
{
  "global_atmosphere": "Late night urban atmosphere, 2 AM quality light...",
  "assets": [
    {
      "id": "object_clock_chart",
      "name": "Analog Clock (Over Trading Screen)",
      "type": "object",
      "used_in_segments": [1],
      "image_prompt": "Macro shot of vintage analog clock with brushed metal finish...",
      "motion_prompt": "Static camera on clock face. Second hand ticks slowly...",
      "suggested_filename": "object_clock_chart.png"
    }
  ]
}
```

**System Prompt:** `shared/prompts/03_visual_plan_system.md`

**Key Concepts:**
- **Breathing Photograph:** Each asset is a static image that will be animated with ONE subtle movement
- **One Asset Per Segment:** Minimum of one image per 10-second segment
- **Global Atmosphere:** Same lighting/weather/color grade applied to all assets

---

## Stage 3.5: Image Generation
**Type:** Dumb Script (Execution)

**Goal:** Generate all images by executing the prompts from Stage 3.

**Script Action:**
1. Reads `03_visual_plan.output.json`
2. For each asset: combines `global_atmosphere` + `image_prompt`
3. Calls image generation API (DALL-E, Midjourney, Gemini, etc.)
4. Saves images to `renders/images/`

**Files:**
- `03.5_asset_generation.input.md` (Execution log)
- `03.5_asset_generation.output.json` (Generation results)
- **Artifacts:** `renders/images/object_clock_chart.png`, etc.

**System Prompt:** `shared/prompts/03.5_asset_generation_system.md`

---

## Stage 4.5: Video Generation
**Type:** Dumb Script (Execution)

**Goal:** Animate the static images into 10-second video clips.

**Script Action:**
1. Reads `03_visual_plan.output.json` for motion prompts
2. Reads images from `renders/images/`
3. Calls video generation API (Kling AI, Runway, Veo, etc.)
4. Downloads/saves video clips to `renders/videos/`

**Files:**
- `04.5_video_generation.input.md` (Execution log)
- `04.5_video_generation.output.json` (Map of segment IDs to file paths)
- **Artifacts:** `renders/videos/bg_01.mp4`, `renders/videos/bg_02.mp4`, etc.

---

## Stage 5: Voice Prompting
**Type:** Smart Agent

**Goal:** Define *how* the lines should be read (prosody, emotion, emphasis).

**Agent Action:** Annotates the script with direction tags for ElevenLabs.

**Files:**
- `05_voice.input.md`
- `05_voice.output.md` (Annotated script with voice direction)

**System Prompt:** `shared/prompts/05_voice_system.md`

---

## Stage 5.5: Audio Generation
**Type:** Dumb Script (Execution)

**Goal:** Generate speech audio from the annotated script.

**Script Action:** Calls ElevenLabs API with voice direction.

**Files:**
- `05.5_audio_generation.input.md` (Execution log)
- `05.5_audio_generation.output.json` (Audio file paths)
- **Artifacts:** `renders/voice_full.mp3` or `renders/voice_01.mp3`, etc.

---

## Stage 6: Music & SFX
**Type:** Smart Agent

**Goal:** Select background track and sound effects.

**Files:**
- `06_music.input.md`
- `06_music.output.json` (Selected track path / SFX list)

---

## Stage 7: Assembly & Rendering
**Type:** Dumb Script (Execution)

**Goal:** Put it all together using Remotion.

**Script Action:**
1. Orchestrator creates a "Manifest" for Remotion
2. Remotion renders the final video with all layers

**Files:**
- `07_assembly.input.md` (Execution log)
- `07_assembly.output.json` (The Timeline/Manifest sent to Remotion)

**Final Output:**
- `final/final.mp4`
- `final/final.srt`
- `final/metadata.json`

---

## Complete Reel Folder Structure

After full pipeline execution:

```
content/reels/2024-05-20-sunk-cost/
├── 00_seed.md
├── 00_reel.yaml
├── 00_data/
│   └── trading.csv
│
├── 01_research.input.md
├── 01_research.output.md
│
├── 02_story_generator.input.md
├── 02_story_generator.output.md
├── 02_story_generator.output.json    ← Segments with visual_intent
│
├── 03_visual_plan.input.md
├── 03_visual_plan.output.md
├── 03_visual_plan.output.json        ← Asset manifest with prompts
│
├── 03.5_asset_generation.input.md
├── 03.5_asset_generation.output.json
│
├── 04.5_video_generation.input.md
├── 04.5_video_generation.output.json
│
├── 05_voice.input.md
├── 05_voice.output.md
│
├── 05.5_audio_generation.input.md
├── 05.5_audio_generation.output.json
│
├── 06_music.input.md
├── 06_music.output.json
│
├── 07_assembly.input.md
├── 07_assembly.output.json
│
├── renders/
│   ├── images/
│   │   ├── object_clock_chart.png
│   │   └── character_professional_decisive.png
│   ├── videos/
│   │   ├── bg_01.mp4
│   │   └── bg_02.mp4
│   └── voice_full.mp3
│
└── final/
    ├── final.mp4
    ├── final.srt
    └── metadata.json
```

---

## Resuming & Debugging

- **To Debug:** Open any `.input.md` file to see exactly what the agent was asked. Open `.output.md`/`.output.json` to see what it produced.

- **To Resume:** The system looks for the last existing `.output.json`. If `03_visual_plan.output.json` exists but `03.5_asset_generation.output.json` does not, it starts at Stage 3.5.

- **To Retry:** Delete the `.output.*` files of the stage you want to re-run.

---

## System Prompts Reference

| Stage | System Prompt File |
|-------|-------------------|
| 1 | `shared/prompts/01_research_system.md` |
| 2 | `shared/prompts/02_script_system.md` |
| 3 | `shared/prompts/03_visual_plan_system.md` |
| 3.5 | `shared/prompts/03.5_asset_generation_system.md` |
| 5 | `shared/prompts/05_voice_system.md` |
