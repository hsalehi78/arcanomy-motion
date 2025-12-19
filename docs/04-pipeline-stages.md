# 04 — Pipeline Stages (Detailed)

## Run Everything Automatically

```bash
uv run full <reel-name>
```

This command runs all 11 stages from research to final video, automatically resuming from the last completed stage if interrupted.

Options:
- `uv run full --fresh` — Start over, ignore existing outputs
- `uv run full -p openai` — Use OpenAI for all LLM stages
- `uv run full --skip-videos` — Skip video generation stage

---

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
| 0 | Manual | Initialize reel | `inputs/seed.md`, `inputs/reel.yaml` |
| 1 | Agent | Research & fact-check | `prompts/01_research.output.md` |
| 2 | Agent | Write script & segment | `json/02_story_generator.output.json` |
| 3 | Agent | Visual plan + image prompts | `json/03_visual_plan.output.json` |
| 3.5 | Script | Generate images | `renders/images/*.png` |
| 4 | Agent | Refine video motion prompts | `json/04_video_prompt.output.json` |
| 4.5 | Script | Generate video clips | `renders/videos/*.mp4` |
| 5 | Agent | Voice direction | `prompts/05_voice.output.md` |
| 5.5 | Script | Generate narrator audio | `renders/audio/voice/*.mp3` |
| 6 | Agent | Sound effects prompts | `json/06_sound_effects.output.json` |
| 6.5 | Script | Generate sound effects | `renders/audio/sfx/*.mp3` |
| 7 | Script | Final assembly (FFmpeg) | `final/final.mp4` |

---

## Stage 0: Initialization
**Type:** Manual Input by User

**Goal:** Define the reel concept and configuration.

**Files:**
- `inputs/seed.md`: The creative spark, concept, or raw notes.
- `inputs/reel.yaml`: Configuration (Duration, Voice ID, Music Vibe, Aspect Ratio).
- `inputs/data/`: Optional CSV files for data-driven reels.

---

## Stage 1: Research
**Type:** Smart Agent

**Goal:** Ground the seed concept in facts and identify the "angle".

**Agent Action:** Reads seed + data. Browses web (if enabled). Generates a research summary.

**Files:**
- `prompts/01_research.input.md` (The prompt sent to the LLM)
- `prompts/01_research.output.md` (The research notes and key takeaways)

**System Prompt:** `shared/prompts/01_research_system.md`

---

## Stage 2: Story & Segmentation
**Type:** Smart Agent

**Goal:** Write the script and divide it into 10-second blocks.

**Agent Action:** Writes a voiceover script and splits it into strict time blocks, each with a `visual_intent` description.

**Files:**
- `prompts/02_story_generator.input.md`
- `prompts/02_story_generator.output.md` (Human-readable script)
- `json/02_story_generator.output.json` **(CRITICAL)**: Structured list of segments.

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
- `prompts/03_visual_plan.input.md`
- `prompts/03_visual_plan.output.md` (Human-readable plan with all prompts)
- `json/03_visual_plan.output.json` **(CRITICAL)**: Machine-readable asset manifest.

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
1. Reads `json/03_visual_plan.output.json`
2. For each asset: combines `global_atmosphere` + `image_prompt`
3. Calls image generation API (DALL-E, Midjourney, Gemini, etc.)
4. Saves images to `renders/images/`

**Files:**
- `prompts/03.5_asset_generation.input.md` (Execution log)
- `json/03.5_asset_generation.output.json` (Generation results)
- **Artifacts:** `renders/images/composites/object_clock_chart.png`, etc.

**System Prompt:** `shared/prompts/03.5_asset_generation_system.md`

---

## Stage 4: Video Prompt Engineering
**Type:** Smart Agent

**Goal:** Refine the basic motion prompts from Stage 3 into production-ready video prompts optimized for Kling/Runway.

**Agent Action:**
1. Analyzes motion prompts from `json/03_visual_plan.output.json`
2. Rewrites prompts following video AI best practices (priority hierarchy, plain language, single camera movement)
3. Creates a "Video Shot List" mapping each segment to its optimized prompt
4. Identifies action shots vs. micro-movement shots

**Files:**
- `prompts/04_video_prompt.input.md`
- `prompts/04_video_prompt.output.md` (Human-readable shot list with all prompts)
- `json/04_video_prompt.output.json` **(CRITICAL)**: Machine-readable clips array

```json
{
  "clips": [
    {
      "clip_number": 1,
      "segment_id": 1,
      "seed_image": "renders/images/object_clock_spinning.png",
      "video_prompt": "Clock face glows in dim light. Second hand ticks forward slowly...",
      "camera_movement": "Slow push in",
      "duration_seconds": 10,
      "movement_type": "micro",
      "notes": "Opening tension shot"
    }
  ]
}
```

**System Prompt:** `shared/prompts/04_video_prompt_system.md`

**Key Concepts:**
- **Priority Hierarchy:** Core Action → Specific Details → Context → Camera (in that order)
- **Plain Language:** Simple, clear sentences with specific body parts/elements named
- **Single Camera Movement:** Every clip ends with exactly ONE camera directive (e.g., "Slow zoom in")
- **10-Second Awareness:** Motion must be sustainable for full clip duration

---

## Stage 4.5: Video Generation
**Type:** Dumb Script (Execution)

**Goal:** Animate the static images into 10-second video clips.

**Script Action:**
1. Reads `json/04_video_prompt.output.json` for optimized prompts (fallback: `json/03_visual_plan.output.json`)
2. Reads images from `renders/images/composites/`
3. Calls video generation API (Kling AI, Runway, etc.)
4. Downloads/saves video clips to `renders/videos/`

**Files:**
- `prompts/04.5_video_generation.input.md` (Execution log)
- `json/04.5_video_generation.output.json` (Map of clip numbers to file paths)
- **Artifacts:** `renders/videos/clip_01.mp4`, `renders/videos/clip_02.mp4`, etc.

**System Prompt:** `shared/prompts/04.5_video_generation_system.md`

---

## Stage 5: Voice Prompting
**Type:** Smart Agent

**Goal:** Define *how* the lines should be read (prosody, emotion, emphasis).

**Agent Action:** Annotates the script with direction tags for ElevenLabs.

**Files:**
- `prompts/05_voice.input.md`
- `prompts/05_voice.output.md` (Annotated script with voice direction)

**System Prompt:** `shared/prompts/05_voice_system.md`

---

## Stage 5.5: Audio Generation
**Type:** Dumb Script (Execution)

**Goal:** Generate speech audio from the annotated script.

**Script Action:** Calls ElevenLabs API with voice direction.

**Files:**
- `prompts/05.5_audio_generation.input.md` (Execution log)
- `json/05.5_audio_generation.output.json` (Audio file paths)
- **Artifacts:** `renders/audio/voice/voice_01.mp3`, `renders/audio/voice/voice_02.mp3`, etc.

---

## Stage 6: Sound Effects Prompt Engineering
**Type:** Smart Agent

**Goal:** Create atmospheric sound effect prompts for each video segment.

**Agent Action:**
1. Reads script segments from Stage 2
2. Analyzes visual plan from Stage 3 for scene context
3. Creates 10-second sound effect prompts for each clip
4. Ensures continuous ambient bed with action sounds layered on top

**Files:**
- `prompts/06_sound_effects.input.md` (The prompt sent to the LLM)
- `prompts/06_sound_effects.output.md` (Human-readable SFX prompts with table)
- `json/06_sound_effects.output.json` **(CRITICAL)**: Machine-readable SFX prompts

```json
{
  "total_clips": 2,
  "sound_effects": [
    {
      "clip_number": 1,
      "segment_id": 1,
      "scene_summary": "Opening scene - urban night",
      "environment": "city street, night, rainy",
      "continuous_sounds": ["rain", "distant traffic", "city hum"],
      "action_sounds": ["footsteps", "phone notification"],
      "mood": "tense anticipation",
      "prompt": "Continuous late night city ambience with steady rain pattering...",
      "duration_seconds": 10
    }
  ]
}
```

**System Prompt:** `shared/prompts/06_sound_effects_system.md`

**Key Concepts:**
- **Continuous Ambience:** Each prompt must establish a continuous ambient bed (rain, traffic, wind, etc.)
- **NO Silence:** Every second should have environmental sound
- **Action Layered On Top:** Footsteps, impacts, movement sounds added to the ambient bed
- **10-Second Duration:** Each sound effect matches the video clip duration
- **Documentary Style:** Realistic, atmospheric, subtle background layer

---

## Stage 6.5: Sound Effects Generation
**Type:** Dumb Script (Execution)

**Goal:** Generate sound effect audio using ElevenLabs Sound Effects API.

**Script Action:**
1. Reads `json/06_sound_effects.output.json`
2. For each clip: calls ElevenLabs Sound Effects API with the prompt
3. Saves audio to `renders/audio/sfx/clip_XX_sfx.mp3`

**Files:**
- `prompts/06.5_sound_effects_generation.input.md` (Execution log)
- `json/06.5_sound_effects_generation.output.json` (Generation results)
- **Artifacts:** `renders/audio/sfx/clip_01_sfx.mp3`, `renders/audio/sfx/clip_02_sfx.mp3`, etc.

**System Prompt:** `shared/prompts/06.5_sound_effects_generation_system.md`

**Audio Mixing Notes:**
Sound effects are designed as background layer:
- **Narrator voice:** 100% volume (primary audio)
- **Sound effects:** 20-30% volume (subtle background)
- **Crossfade:** 0.5s transitions between clips

---

## Stage 7: Final Assembly
**Type:** Dumb Script (Execution)

**Goal:** Assemble the final video using FFmpeg.

**Script Action:**
1. Mixes voice (centered) + sound effects for each clip
2. Combines mixed audio with video clips
3. Concatenates all clips into final video

**Two-Stage Process:**

### Stage 7.1: Mix Individual Clips
For each clip:
1. Detect voice duration using ffprobe
2. Calculate padding to center voice in 10-second timeline
3. Create centered voice track (silence + voice + silence)
4. Mix centered voice with SFX (voice 100%, SFX 25% default)
5. Combine mixed audio with video

### Stage 7.2: Concatenate All Clips
Combine all mixed clips into one final video using FFmpeg concat demuxer.

**Files:**
- `prompts/07_final.input.md` (Execution log)
- `json/07_final.output.json` (Assembly results)

**Final Output:**
- `final/final.mp4`

**Audio Mixing Formula:**
```
Final Audio = Centered Voice (100%) + Sound Effects (25%)

Centering Formula:
padding_seconds = (10.0 - voice_duration) / 2.0

Example (8.2s voice):
[0.9s silence] [8.2s voice] [0.9s silence] = 10.0s centered track
```

**Command:**
```bash
uv run final              # Run with defaults
uv run final --sfx 0.3    # SFX at 30% volume
uv run final --dry-run    # Validate files only
uv run final --keep       # Keep intermediate files
```

**Requirements:**
- FFmpeg must be installed
- All video clips in `renders/videos/clip_XX.mp4`
- All voice files in `renders/audio/voice/voice_XX.mp3`
- All SFX files in `renders/audio/sfx/clip_XX_sfx.mp3`

---

## Complete Reel Folder Structure

After full pipeline execution:

```
content/reels/2024-05-20-sunk-cost/
├── inputs/
│   ├── seed.md
│   ├── reel.yaml
│   └── data/
│       └── trading.csv
│
├── prompts/
│   ├── 01_research.input.md
│   ├── 01_research.output.md
│   ├── 02_story_generator.input.md
│   ├── 02_story_generator.output.md
│   ├── 03_visual_plan.input.md
│   ├── 03_visual_plan.output.md
│   ├── 03.5_asset_generation.input.md
│   ├── 04_video_prompt.input.md
│   ├── 04_video_prompt.output.md
│   ├── 04.5_video_generation.input.md
│   ├── 05_voice.input.md
│   ├── 05_voice.output.md
│   ├── 05.5_audio_generation.input.md
│   ├── 06_sound_effects.input.md
│   ├── 06_sound_effects.output.md
│   ├── 06.5_sound_effects_generation.input.md
│   └── 07_final.input.md
│
├── json/
│   ├── 02_story_generator.output.json    ← Segments with visual_intent
│   ├── 03_visual_plan.output.json        ← Asset manifest with prompts
│   ├── 03.5_asset_generation.output.json
│   ├── 04_video_prompt.output.json       ← Video shot list with optimized prompts
│   ├── 04.5_video_generation.output.json
│   ├── 05_voice.output.json
│   ├── 05.5_audio_generation.output.json
│   ├── 06_sound_effects.output.json      ← SFX prompts per clip
│   ├── 06.5_sound_effects_generation.output.json
│   └── 07_final.output.json              ← Assembly results
│
├── renders/
│   ├── images/
│   │   ├── composites/
│   │   │   ├── object_clock_spinning.png
│   │   │   └── character_professional_stride.png
│   │   ├── characters/
│   │   ├── backgrounds/
│   │   └── objects/
│   ├── videos/
│   │   ├── clip_01.mp4
│   │   └── clip_02.mp4
│   └── audio/
│       ├── sfx/                      ← Sound effects from Stage 6.5
│       │   ├── clip_01_sfx.mp3
│       │   └── clip_02_sfx.mp3
│       └── voice/                    ← Narrator audio from Stage 5.5
│           ├── voice_01.mp3
│           └── voice_02.mp3
│
└── final/
    └── final.mp4                     ← Final assembled video
```

---

## Resuming & Debugging

- **To Debug:** Open any `.input.md` file to see exactly what the agent was asked. Open `.output.md`/`.output.json` to see what it produced.

- **To Resume:** The system looks for the last existing stage output file. If `json/03_visual_plan.output.json` exists but `json/03.5_asset_generation.output.json` does not, it starts at Stage 3.5.

- **To Retry:** Delete the `.output.*` files of the stage you want to re-run.

---

## System Prompts Reference

| Stage | System Prompt File |
|-------|-------------------|
| 1 | `shared/prompts/01_research_system.md` |
| 2 | `shared/prompts/02_script_system.md` |
| 3 | `shared/prompts/03_visual_plan_system.md` |
| 3.5 | `shared/prompts/03.5_asset_generation_system.md` |
| 4 | `shared/prompts/04_video_prompt_system.md` |
| 4.5 | `shared/prompts/04.5_video_generation_system.md` |
| 5 | `shared/prompts/05_voice_system.md` |
| 6 | `shared/prompts/06_sound_effects_system.md` |
| 6.5 | `shared/prompts/06.5_sound_effects_generation_system.md` |
| 7 | N/A (FFmpeg-based, no LLM) |
