# 02 — Architecture & Folder Structure (Monorepo)

## Overview

Arcanomy Motion is a **hybrid monorepo** combining:
1.  **Python Orchestrator:** Handles logic, LLM calls, and state management.
2.  **Remotion (React):** Handles deterministic rendering of video, charts, and typography.

We follow a **"Smart Agent + Dumb Scripts"** architecture:
- **Smart Agent Stages** (1, 2, 3, 4, 5, 6): LLM plans, writes prompts, makes creative decisions
- **Dumb Script Stages** (3.5, 4.5, 5.5, 6.5, 7): Automated execution of API calls/FFmpeg, no creativity

---

## 🧐 How It Works (Explain Like I'm 5)

Imagine you are making a LEGO movie. Here is how our robot factory does it:

### 1. The Idea (The Seed)
You tell the robot **"Make a movie about Bitcoin."**
You also give it a rules list: **"Use a serious man's voice"** and **"Make it 30 seconds long."**
*(This is `00_seed.md` and `00_reel.yaml`)*

### 2. The Writer (Story & Research)
The robot reads your idea. It goes to the library (Google) to check facts.
Then, it writes a script. But it doesn't just write paragraphs; it cuts the script into **10-second chunks**, like LEGO blocks.
*(This creates `02_story_generator.output.json`)*

> **Chunk 1:** "Bitcoin is digital gold." (Show a gold coin)
> **Chunk 2:** "It is scarce." (Show a chart going up)

### 3. The Art Director (Visual Plan)
For every chunk, the robot writes detailed instructions for painting a picture.
It describes exactly what the image should look like, what textures, what lighting.
*(This creates `03_visual_plan.output.json` with complete image prompts)*

### 4. The Artist (Image Gen)
A "dumb" robot reads those instructions and paints the pictures.
It uses tools like **DALL-E** or **Midjourney** to create one image per chunk.
*(This creates images in `renders/images/`)*

### 5. The Director (Video Prompts)
Before animating, another smart robot reads the images and refines the animation instructions.
- It makes sure the motion matches what's in the image ("image anchor" logic).
- It puts instructions in the right order: what moves → how it moves → camera movement.
*(This creates `04_video_prompt.output.json`)*

### 6. The Animator (Video Gen)
The robot takes each picture and makes it "breathe" for **10 seconds**.
- It adds subtle movement: "Zoom in slowly" or "Rain falling in background."
- It uses tools like **Kling AI** or **Runway** to animate the still images.
*(Now we have `renders/videos/clip_01.mp4`, `clip_02.mp4`...)*

### 7. The Voice Actor (Audio Gen)
The robot reads the script out loud using a tool called **ElevenLabs**.
It makes sure the voice matches the video timing.
*(Now we have `renders/voice/voice_01.mp3`, etc.)*

### 8. The Sound Effects Designer (SFX)
The robot creates atmospheric sound effects for each scene.
It uses **ElevenLabs Sound Effects API** to generate ambient audio.
*(Now we have `renders/sfx/clip_01_sfx.mp3`, etc.)*

### 9. The Editor (Final Assembly)
Now the robot has a pile of stuff:
- Video clips
- Voice narration
- Sound effects

It uses **FFmpeg** to:
1. Center the voice in each 10-second clip
2. Mix voice with sound effects (voice 100%, SFX 25%)
3. Combine the mixed audio with video
4. Concatenate all clips into **one final MP4 video file**.

---

## Root Layout

```text
arcanomy-motion/
├── docs/                     # Project documentation
├── src/                      # Python Source Code (Orchestrator)
├── remotion/                 # Remotion Project (React/TypeScript)
├── content/                  # User Data & Local Outputs (Git-ignored)
├── shared/                   # Global Assets (fonts, logos, prompts)
├── tests/                    # Python Tests
├── pyproject.toml            # Python Dependencies & Config (uv)
└── .gitignore
```

---

## 1. `src/` (Python Orchestrator)

The brain of the system. It reads the inputs, calls APIs via scripts, and manages the detailed step-by-step pipeline.

```text
src/
├── domain/                   # Data Classes & Types
│   ├── objective.py          # Objective model & parsing logic
│   ├── segment.py            # Segment definition
│   └── manifest.py           # The "Render Manifest" sent to Remotion
│
├── services/                 # External API Wrappers
│   ├── llm.py                # OpenAI / Anthropic / Google
│   ├── elevenlabs.py         # Voice generation
│   ├── image_gen.py          # DALL-E / Midjourney / Gemini
│   └── remotion_cli.py       # Wrapper for calling `npx remotion render`
│
├── stages/                   # Pipeline Logic (Pure Python)
│   ├── s01_research.py
│   ├── s02_script.py
│   ├── s03_plan.py
│   ├── s04_assets.py         # Image generation execution
│   ├── s04_vidprompt.py      # Video prompt engineering
│   ├── s05_voice.py
│   ├── s05_audio.py          # Voice audio generation execution
│   ├── s06_sfx.py            # Sound effects prompt engineering
│   ├── s06_sfx_gen.py        # Sound effects generation execution
│   ├── s06_delivery.py       # Legacy assembly (Remotion-based)
│   └── s07_final.py          # Final assembly (FFmpeg-based)
│
├── utils/                    # Helpers
│   ├── io.py                 # Safe file reading/writing
│   └── logger.py
│
├── main.py                   # Entry point (CLI)
└── commands.py               # Click/Typer command definitions
```

---

## 2. `remotion/` (Visual Engine)

A standard Remotion project. It takes a JSON payload (the "Timeline" or "Manifest") and renders pixels. It does **not** make decisions.

```text
remotion/
├── src/
│   ├── compositions/         # Top-level Entry Points
│   │   ├── MainReel.tsx      # The primary composition
│   │   └── Shorts.tsx
│   │
│   ├── components/           # Reusable UI
│   │   ├── charts/           # D3/Visx wrappers
│   │   ├── typography/       # Text animations
│   │   └── layouts/          # Screen arrangements (e.g., SplitScreen)
│   │
│   ├── lib/                  # Helpers
│   │   ├── load-fonts.ts
│   │   └── utils.ts
│   │
│   └── Root.tsx              # Remotion registration
│
├── public/                   # Static assets for preview
├── package.json
└── tsconfig.json
```

---

## 3. `content/` (User Data & Artifacts)

This is where the magic happens. We follow a granular, step-by-step file structure where every stage produces an explicit **input prompt** and **output result**. This allows us to inspect, debug, and manually intervene at any point.

**Structure per Reel:**

```text
content/
└── reels/
    └── 2024-05-20-sunk-cost/        # Unique Reel Slug
        ├── 00_seed.md               # [Input] The initial user concept/brief
        ├── 00_reel.yaml             # [Input] Machine settings (voice, music, etc.)
        ├── 00_data/                 # [Input] Local CSVs for charts
        │   └── trading.csv
        │
        ├── 01_research.input.md     # [Gen] Exact prompt sent to research agent
        ├── 01_research.output.md    # [Gen] Research findings
        │
        ├── 02_story_generator.input.md
        ├── 02_story_generator.output.md
        ├── 02_story_generator.output.json  # [Key] Segments with visual_intent
        │
        ├── 03_visual_plan.input.md
        ├── 03_visual_plan.output.md        # Human-readable plan + prompts
        ├── 03_visual_plan.output.json      # [Key] Asset manifest with prompts
        │
        ├── 03.5_asset_generation.input.md
        ├── 03.5_asset_generation.output.json  # Image generation results
        │
        ├── 04_video_prompt.input.md
        ├── 04_video_prompt.output.md          # Refined video prompts
        ├── 04_video_prompt.output.json        # Video shot list
        │
        ├── 04.5_video_generation.input.md
        ├── 04.5_video_generation.output.json  # Video generation results
        │
        ├── 05_voice.input.md
        ├── 05_voice.output.md              # Voice direction annotations
        │
        ├── 05.5_audio_generation.input.md
        ├── 05.5_audio_generation.output.json  # Audio file paths
        │
        ├── 06_sound_effects.input.md
        ├── 06_sound_effects.output.md        # Human-readable SFX prompts
        ├── 06_sound_effects.output.json      # SFX prompts for generation
        │
        ├── 06.5_sound_effects_generation.input.md
        ├── 06.5_sound_effects_generation.output.json  # SFX file paths
        │
        ├── 07_final.input.md                 # Final assembly execution log
        ├── 07_final.output.json              # Assembly results
        │
        ├── renders/                 # [Assets] Generated media files
        │   ├── images/              # Static images from Stage 3.5
        │   │   ├── object_clock_chart.png
        │   │   └── character_professional.png
        │   ├── videos/              # Video clips from Stage 4.5
        │   │   ├── clip_01.mp4
        │   │   └── clip_02.mp4
        │   ├── sfx/                 # Sound effects from Stage 6.5
        │   │   ├── clip_01_sfx.mp3
        │   │   └── clip_02_sfx.mp3
        │   └── voice/               # Audio from Stage 5.5
        │       ├── voice_01.mp3
        │       └── voice_02.mp3
        │
        └── final/                   # [Delivery] Final output
            └── final.mp4            # Assembled video from Stage 7
```

### Philosophy: Explicit State

- **Inputs (.input.md):** We save the *exact* prompt sent to the LLM. This allows us to tweak the prompt manually if needed and re-run the step.
- **Outputs (.output.md/.json):** We save the text response (MD) and the structured data (JSON). The JSON is often the input for the next "dumb script" (e.g., a list of image prompts to generate).
- **Renders Folder:** All heavy media files live in `renders/` with subdirectories for organization.

---

## 4. `shared/` (Global Assets)

Assets and configuration that apply to *all* reels (brand identity and agent instructions).

```text
shared/
├── fonts/
├── logos/
├── audio/
│   ├── intro.mp3
│   └── watermark.mp3
├── prompts/                         # System prompts for agents
│   ├── 01_research_system.md        # Research assistant instructions
│   ├── 02_script_system.md          # Scriptwriter instructions
│   ├── 03_visual_plan_system.md     # Visual director + prompt engineer
│   ├── 03.5_asset_generation_system.md  # Automated image generation
│   ├── 04_video_prompt_system.md    # Video prompt specialist
│   ├── 04.5_video_generation_system.md  # Automated video generation
│   ├── 05_voice_system.md           # Voice director instructions
│   ├── 06_sound_effects_system.md   # Sound effects designer
│   └── 06.5_sound_effects_generation_system.md  # SFX generation
│   # Note: Stage 7 (Final Assembly) uses FFmpeg, no LLM needed
└── templates/                       # User-facing templates
    └── seed_template.md             # Template for creating new reels
```

**Distinction:**
- **`prompts/`**: System prompts define agent behavior and are loaded by the orchestrator. These are internal instructions that apply globally across all reels.
- **`templates/`**: User-facing templates provide formats/starting points for users to fill in (e.g., `seed_template.md`).

---

## Pipeline Summary

| Stage | Type | What Happens | Key Output |
|-------|------|--------------|------------|
| 0 | Manual | User creates seed + config | `00_seed.md`, `00_reel.yaml` |
| 1 | Agent | Research & fact-check | `01_research.output.md` |
| 2 | Agent | Write script + segment | `02_story_generator.output.json` |
| 3 | Agent | Visual plan + all prompts | `03_visual_plan.output.json` |
| 3.5 | Script | Generate images | `renders/images/*.png` |
| 4 | Agent | Refine video motion prompts | `04_video_prompt.output.json` |
| 4.5 | Script | Generate videos | `renders/videos/*.mp4` |
| 5 | Agent | Voice direction | `05_voice.output.md` |
| 5.5 | Script | Generate narrator audio | `renders/voice/*.mp3` |
| 6 | Agent | Sound effects prompts | `06_sound_effects.output.json` |
| 6.5 | Script | Generate sound effects | `renders/sfx/*.mp3` |
| 7 | Script | Final assembly (FFmpeg) | `final/final.mp4` |

---

## Workflow Summary

1.  **User** creates `00_seed.md` and `00_reel.yaml`.
2.  **Orchestrator** runs step-by-step:
    -   Reads inputs.
    -   Generates `.input.md` (prompt).
    -   Calls Agent/LLM (for Smart Agent stages).
    -   Saves `.output.md` and `.output.json`.
    -   Calls "Dumb Scripts" (for execution stages) to generate assets into `renders/`.
3.  **Final Assembly** reads all JSONs and assets, creates a timeline, and calls Remotion to render the final video.

---

## The "Breathing Photograph" Approach

Key constraint that shapes the entire pipeline:

- Each segment gets **ONE static image**
- The image is animated with **ONE subtle micro-movement** for 10 seconds
- Video AI (Kling, Runway) adds: zoom, drift, rain falling, breathing, etc.
- This is NOT action sequences — it's "photographs that breathe"

This constraint means:
- Stage 3 creates prompts for **static state images** and initial motion descriptions
- Stage 4 refines motion prompts for video AI (priority order, plain language, camera movement)
- Motion prompts describe **subtle animation**, not complex choreography
- Assets are designed to sustain 10 seconds of micro-movement
