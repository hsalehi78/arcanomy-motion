# Arcanomy Motion — Quick Start Guide

> AI-powered short-form video production pipeline for financial content

Run `uv run guide` anytime to see this in your terminal.

---

## Quick Start (One Command!)

```bash
uv run full <reel-name>
```

This runs the **entire pipeline** from research to final video automatically.

Example:
```bash
uv run full permission-trap          # Runs all 11 stages
uv run full permission-trap -p openai  # Use OpenAI for all LLM stages
uv run full --fresh                  # Start over (ignore existing outputs)
uv run full --skip-videos            # Skip video generation
```

---

## Workflow Overview

### 1. Create or Select a Reel

**Option A:** Create from scratch
```bash
uv run arcanomy new my-reel-slug
```

**Option B:** Import from Arcanomy blog (interactive picker)
```bash
uv run arcanomy ingest-blog
```

**Option C:** Select an existing reel
```bash
uv run set permission-trap    # Partial match works!
```

---

### 2. Run the Pipeline

**Automated (recommended):**
```bash
uv run full                   # Runs all stages on current reel
```

**Or run stages individually (11 Stages):**

| Stage | Command           | What It Does                                        | Key Output                          |
|-------|-------------------|-----------------------------------------------------|-------------------------------------|
| ALL   | `uv run full`     | **Run entire pipeline automatically**               | `final/final.mp4` (and `final/final_raw.mp4`) |
| 1     | `uv run research` | Research & fact-check the seed concept              | `01_research.output.md`             |
| 2     | `uv run script`   | Write script & split into 10s segments              | `02_story_generator.output.json`    |
| 3     | `uv run plan`     | Create visual plan + image/motion prompts           | `03_visual_plan.output.json`        |
| 3.5   | `uv run assets`   | Generate images from prompts (DALL-E/Gemini)        | `renders/images/*.png`              |
| 4     | `uv run vidprompt`| Refine motion prompts for video AI                  | `04_video_prompt.output.json`       |
| 4.5   | `uv run videos`   | Generate video clips from images (Kling/Runway)     | `renders/videos/*.mp4`              |
| 5     | `uv run voice`    | Voice direction (optimize narration)                | `05_voice.output.json`              |
| 5.5   | `uv run audio`    | Generate narrator audio (ElevenLabs TTS)            | `renders/audio/voice/*.mp3`         |
| 6     | `uv run sfx`      | Create sound effect prompts per clip                | `06_sound_effects.output.json`      |
| 6.5   | `uv run sfxgen`   | Generate sound effects (ElevenLabs SFX)             | `renders/audio/sfx/*.mp3`           |
| 7     | `uv run final`    | Assemble audio + SFX + clips into base video        | `final/final_raw.mp4`               |
| 7.5   | `uv run captions` | Burn karaoke captions + export `.srt`               | `final/final.mp4`, `final/final.srt` |

---

### 3. Preview & Export

```bash
uv run arcanomy preview           # Start Remotion dev server
uv run arcanomy status <path>     # Check pipeline progress
```

---

## Quick Commands Reference

| Command | Description |
|---------|-------------|
| `uv run full` | **Run entire pipeline (all 11 stages)** |
| `uv run guide` | Show this guide in terminal |
| `uv run current` | Show current reel + status |
| `uv run set <slug>` | Set working reel (partial match OK) |
| `uv run research` | Run Stage 1 on current reel |
| `uv run script` | Run Stage 2 on current reel |
| `uv run plan` | Run Stage 3 on current reel |
| `uv run assets` | Run Stage 3.5 on current reel |
| `uv run vidprompt` | Run Stage 4 on current reel |
| `uv run videos` | Run Stage 4.5 on current reel |
| `uv run voice` | Run Stage 5 on current reel |
| `uv run audio` | Run Stage 5.5 on current reel |
| `uv run sfx` | Run Stage 6 on current reel |
| `uv run sfxgen` | Run Stage 6.5 on current reel |
| `uv run final` | Run Stage 7 on current reel |
| `uv run captions` | Run Stage 7.5 on current reel |
| `uv run chart <json>` | Render chart from JSON props file |
| `uv run commit` | Git add + commit + push |

---

## Full Arcanomy CLI Commands

| Command | Description |
|---------|-------------|
| `uv run arcanomy new <slug>` | Create new reel from template |
| `uv run arcanomy ingest-blog` | Import blog (interactive) |
| `uv run arcanomy ingest-blog <id>` | Import specific blog |
| `uv run arcanomy list-blogs` | Show available blogs |
| `uv run arcanomy run <path>` | Run full pipeline |
| `uv run arcanomy run <path> -s 2` | Run specific stage only |
| `uv run arcanomy status <path>` | Show pipeline status |
| `uv run arcanomy preview` | Start Remotion dev server |
| `uv run arcanomy render-chart <json>` | Render chart from JSON |
| `uv run arcanomy guide` | Show workflow guide |

---

## Chart Rendering

Render animated charts from JSON data files:

```bash
# Render a bar chart
uv run chart my-chart.json

# With custom output path
uv run chart my-chart.json -o output/revenue-chart.mp4

# Full command
uv run arcanomy render-chart path/to/chart.json
```

### Chart JSON Format

Create a JSON file with your data:

```json
{
  "chartType": "bar",
  "title": "Monthly Revenue ($K)",
  "animationDuration": 45,
  "data": [
    { "label": "Jan", "value": 120 },
    { "label": "Feb", "value": 85 },
    { "label": "Mar", "value": 200, "color": "#FF3B30" }
  ]
}
```

### Available Options

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `chartType` | `"bar"` | Required | Chart type |
| `title` | string | `"Chart"` | Title at top |
| `animationDuration` | number | `45` | Animation frames (30 = 1 sec) |
| `data` | array | Required | Data points |

Templates and full documentation in `docs/charts/`

---

## Reel Folder Structure

```
content/reels/2025-12-15-my-reel/
├── inputs/
│   ├── seed.md                          <- Your creative brief (edit this)
│   ├── reel.yaml                        <- Config: duration, voice, type
│   └── data/                            <- CSV files for charts
│
├── prompts/
│   ├── 01_research.input.md             <- Prompt sent to LLM
│   └── 01_research.output.md            <- Stage 1: Research notes
│
├── prompts/
│   ├── 02_story_generator.input.md
│   └── 02_story_generator.output.md     <- Stage 2: Human-readable script
├── json/
│   └── 02_story_generator.output.json   <- Stage 2: Segments with visual_intent
│
├── prompts/
│   ├── 03_visual_plan.input.md
│   └── 03_visual_plan.output.md         <- Stage 3: Visual plan + prompts
├── json/
│   └── 03_visual_plan.output.json       <- Stage 3: Asset manifest (machine-readable)
│
├── prompts/
│   └── 03.5_asset_generation.input.md
├── json/
│   └── 03.5_asset_generation.output.json <- Stage 3.5: Image generation results
│
├── prompts/
│   ├── 04_video_prompt.input.md
│   └── 04_video_prompt.output.md        <- Stage 4: Refined video prompts
├── json/
│   └── 04_video_prompt.output.json      <- Stage 4: Video shot list (machine-readable)
│
├── prompts/
│   └── 04.5_video_generation.input.md
├── json/
│   └── 04.5_video_generation.output.json <- Stage 4.5: Video generation results
│
├── prompts/
│   ├── 05_voice.input.md
│   └── 05_voice.output.md               <- Stage 5: Voice direction (human-readable)
├── json/
│   └── 05_voice.output.json             <- Stage 5: Voice direction (machine-readable)
├── prompts/
│   └── 05.5_audio_generation.input.md
├── json/
│   └── 05.5_audio_generation.output.json <- Stage 5.5: Audio generation results
│
├── prompts/
│   ├── 06_sound_effects.input.md
│   └── 06_sound_effects.output.md       <- Stage 6: SFX prompts (human-readable)
├── json/
│   └── 06_sound_effects.output.json     <- Stage 6: SFX prompts (machine-readable)
├── prompts/
│   └── 06.5_sound_effects_generation.input.md
├── json/
│   └── 06.5_sound_effects_generation.output.json <- Stage 6.5: SFX generation results
│
├── renders/                            <- Generated media assets
│   ├── images/                         <- Static images (from Stage 3.5)
│   │   ├── composites/                  <- Anchor images for video gen
│   │   │   ├── object_clock_chart.png
│   │   │   └── character_professional.png
│   │   ├── characters/                  <- Optional (future split)
│   │   ├── backgrounds/                 <- Optional (future split)
│   │   └── objects/                     <- Optional (future split)
│   ├── videos/                         <- Video clips (from Stage 4.5)
│   │   ├── clip_01.mp4
│   │   └── clip_02.mp4
│   └── audio/
│       ├── sfx/                         <- Sound effects (from Stage 6.5)
│       │   ├── clip_01_sfx.mp3
│       │   └── clip_02_sfx.mp3
│       └── voice/                       <- Audio (from Stage 5.5)
│           ├── voice_01.mp3
│           └── voice_02.mp3
│
└── final/
    ├── final_raw.mp4                   <- Base output (audio/SFX correct, no captions)
    ├── final.mp4                       <- Captioned output (burned-in karaoke)
    ├── final.srt                       <- Subtitle file (export)
    └── metadata.json                   <- Audit trail
```

---

## The Pipeline Philosophy

**Smart Agent + Dumb Script:**
- **Agent stages** (1, 2, 3, 4, 5, 6): LLM plans, writes prompts, makes creative decisions
- **Script stages** (3.5, 4.5, 5.5, 6.5, 7): Automated execution of API calls, no creativity

**Stage 3 is the keystone:**
- Creates complete image prompts (ready for DALL-E/Kie.ai)
- Creates initial motion prompts
- Outputs machine-readable JSON for automation

**Stage 4 refines for video AI:**
- Optimizes motion prompts for Kling 2.5/Runway
- Adds proper camera movements (always last in prompt)
- Ensures prompts match seed images ("image anchor" logic)

---

## Tips & Tricks

**Partial matching:** `uv run set permission` finds `2025-12-15-permission-trap-waiting-game`

**Resume pipeline:** Just re-run a stage; it reads previous outputs automatically

**Retry a stage:** Delete its `.output.*` files, then re-run

**Switch LLM provider:** Add `-p anthropic` or `-p gemini` to any stage command
```bash
uv run research -p anthropic
uv run script -p gemini
```

**Switch image provider:** Default is Gemini (Nano Bananao style). Use `-p openai` for DALL-E
```bash
uv run assets                     # Uses Gemini (default, Nano Bananao style)
uv run assets -p openai           # Use DALL-E 3 instead
uv run assets --dry-run           # Just save prompts, don't call API
```

**Direct CLI for single assets:**
```bash
python scripts/generate_asset.py --prompt "Your prompt here" --output "output.png" --provider openai
```

**Debug prompts:** Check `*.input.md` files to see exactly what was sent to the LLM

**View status:** 
```bash
uv run current                    # Quick status of current reel
uv run arcanomy status <path>     # Full pipeline status
```

---

## The 10-Second Block Philosophy

All Arcanomy reels are built from **10-second blocks**. This aligns with:
- AI video generation constraints (Kling/Runway clip limits)
- "Breathing Photograph" approach (one image → one 10s animated clip)
- Short-form platform requirements

| Duration | Blocks | Use Case |
|----------|--------|----------|
| 10s | 1 | Micro insight, single statement |
| 20s | 2 | Core explainer (default) |
| 30s | 3 | Expanded explainer with consequence |
| 40s | 4 | Transitional essay |
| 60s | 6 | Mini essay (rare) |

> If an idea doesn't earn the next 10 seconds, it doesn't belong in the reel.

---

## Environment Setup

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY`)
   - `ELEVENLABS_API_KEY`
   - `KIE_API_KEY` (for Kie.ai image/video generation)

---

## Model Configuration (`src/config.py`)

All AI models are configured in `src/config.py`. Edit this file to:

**Switch LLM models:**
```python
MODELS = {
    "openai": {"default": "gpt-5.2"},      # or "gpt-4o", "o3"
    "anthropic": {"default": "claude-opus-4-5-20251101"},
    "gemini": {"default": "gemini-3-pro"},
}
```

**Switch image/video models:**
```python
IMAGE_MODELS = {
    "kie": {"default": "nano-banana-pro"},
    "openai": {"default": "gpt-image-1.5"},
    "gemini": {"default": "gemini-3-pro-image-preview"},
}
```

**Change default providers per stage:**
```python
DEFAULT_PROVIDERS = {
    "research": "openai",    # Which LLM for research
    "script": "anthropic",   # Which LLM for script writing
    "assets": "kie",         # Which API for images
    "videos": "kling",       # Which API for videos
    # ... etc
}
```

To use OpenAI for everything, change all LLM stages to `"openai"`.

---

## Documentation

Full docs are in the `docs/` folder:

| File | Contents |
|------|----------|
| `01-vision-and-reel-types.md` | Philosophy, reel types, length bands |
| `02-architecture-and-folder-structure.md` | Repo layout, pipeline model |
| `03-seed-and-config-format.md` | How to write seed.md and reel.yaml |
| `04-pipeline-stages.md` | Detailed stage-by-stage breakdown |
| `05-visual-style-and-subtitles.md` | Arcanomy visual system |

---

## System Prompts

The LLM instructions are in `shared/prompts/`:

| File | Stage | Purpose |
|------|-------|---------|
| `01_research_system.md` | 1 | Research assistant |
| `02_script_system.md` | 2 | Scriptwriter |
| `03_visual_plan_system.md` | 3 | Visual director + prompt engineer |
| `03.5_asset_generation_system.md` | 3.5 | Automated image generation |
| `04_video_prompt_system.md` | 4 | Video prompt specialist |
| `04.5_video_generation_system.md` | 4.5 | Automated video generation |
| `05_voice_system.md` | 5 | Voice director |
| `06_sound_effects_system.md` | 6 | Sound effects designer |
| `06.5_sound_effects_generation_system.md` | 6.5 | Automated SFX generation |

---

**Ready to start?**

**Option 1: Fully Automated (recommended)**
```bash
uv run arcanomy ingest-blog    # Pick a blog
uv run full                    # Run entire pipeline!
```

**Option 2: Run stages individually**
```bash
uv run arcanomy ingest-blog    # Pick a blog
uv run research                # Stage 1
uv run script                  # Stage 2
uv run plan                    # Stage 3
uv run assets                  # Stage 3.5
uv run vidprompt               # Stage 4
uv run videos                  # Stage 4.5
uv run voice                   # Stage 5
uv run audio                   # Stage 5.5
uv run sfx                     # Stage 6
uv run sfxgen                  # Stage 6.5
uv run final                   # Stage 7
uv run captions                # Stage 7.5
```
