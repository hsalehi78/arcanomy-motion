# 02 — Architecture & Folder Structure (Monorepo)

## Overview

Arcanomy Motion is a **hybrid monorepo** combining:
1.  **Python Orchestrator:** Handles logic, LLM calls, and state management.
2.  **Remotion (React):** Handles deterministic rendering of video, charts, and typography.

We follow a **"Smart Agent + Dumb Scripts"** architecture. Agents orchestrate the flow by reading project files and combining prompts, while simple Python scripts execute single API calls (e.g., "generate one image", "render one video clip").

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

### 3. The Artist (Image Gen)
For every chunk, the robot paints **one beautiful picture**.
If the chunk needs a chart, it draws a sketch of the chart.
*(This creates images in `renders/`)*

### 4. The Animator (Video Gen)
The robot takes that one picture and makes it move for **10 seconds**.
- It decides: "Zoom in slowly" or "Pan left."
- It uses a tool called **Kling** (or Runway) to turn the still picture into a moving video.
*(Now we have `bg_01.mp4`, `bg_02.mp4`...)*

### 5. The Voice Actor (Audio Gen)
The robot reads the script out loud using a tool called **ElevenLabs**.
It makes sure the voice lasts exactly as long as the video chunk.
*(Now we have `voice_01.mp3`, `voice_02.mp3`...)*

### 6. The Editor (Assembly)
Now the robot has a pile of stuff:
- 3 Video clips
- 3 Audio clips
- Background music

It glues them all together in a timeline. It puts the voice *on top* of the video, and the music *underneath* everything.
Finally, it presses "Print" (Render) and gives you **one final MP4 video file**.

---

## Root Layout

```text
arcanomy-motion/
├── docs/                     # Project documentation
├── src/                      # Python Source Code (Orchestrator)
├── remotion/                 # Remotion Project (React/TypeScript)
├── content/                  # User Data & Local Outputs (Git-ignored)
├── shared/                   # Global Assets (fonts, logos, intro/outro)
├── tests/                    # Python Tests
├── pyproject.toml            # Python Dependencies & Config (Poetry/uv)
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
│   ├── llm.py                # OpenAI / Anthropic
│   ├── elevenlabs.py         # Voice generation
│   └── remotion_cli.py       # Wrapper for calling `npx remotion render`
│
├── stages/                   # Pipeline Logic (Pure Python)
│   ├── s01_research.py
│   ├── s02_script.py
│   ├── s03_plan.py
│   ├── s04_assets.py
│   ├── s05_assembly.py
│   └── s06_delivery.py
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
        ├── 02_story_generator.output.json  # [Key] Segmentation source of truth
        │
        ├── 03_character_generation.input.md
        ├── 03_character_generation.output.md
        │
        ├── 03.5_generate_assets_agent.input.md
        ├── 03.5_generate_assets_agent.output.json # Asset list (images/charts)
        │
        ├── 04_video_prompt_engineering.input.md
        ├── 04_video_prompt_engineering.output.md
        │
        ├── 04.5_generate_videos_agent.input.md
        ├── 04.5_generate_videos_agent.output.json # Video file paths
        │
        ├── 05_voice_prompt_engineer.input.md
        ├── 05_voice_prompt_engineer.output.md
        │
        ├── 05.5_generate_audio_agent.input.md
        ├── 05.5_generate_audio_agent.output.json # Audio file paths
        │
        ├── 06_music.input.md
        ├── 06_music.output.json
        │
        ├── 07_assemble_final_agent.input.md
        ├── 07_assemble_final_agent.output.json # Final Remotion timeline
        │
        ├── renders/                 # [Assets] Intermediate media files
        │   ├── bg_01.mp4
        │   ├── bg_02.mp4
        │   ├── intro.png
        │   ├── voice_full.mp3
        │   └── charts/              # Remotion chart renders (optional/cache)
        │
        └── final/                   # [Delivery] Final outputs
            ├── final.mp4
            ├── final.srt
            └── metadata.json
```

### Philosophy: Explicit State

- **Inputs (.input.md):** We save the *exact* prompt sent to the LLM. This allows us to tweak the prompt manually if needed and re-run the step.
- **Outputs (.output.md/.json):** We save the text response (MD) and the structured data (JSON). The JSON is often the input for the next "dumb script" (e.g., a list of image prompts to generate).
- **Renders Folder:** All heavy media files live in `renders/` to keep the root directory text-focused and scannable.

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
├── prompts/                  # System prompts for agents (reusable instructions)
│   ├── research_system.md    # Research assistant instructions
│   ├── script_system.md      # Scriptwriter instructions
│   ├── visual_plan_system.md # Visual director instructions
│   ├── assets_system.md      # Image/video prompt engineer instructions
│   └── voice_system.md       # Voice director instructions
└── templates/                # User-facing templates (starting points)
    └── seed_template.md      # Template for creating new reels
```

**Distinction:**
- **`prompts/`**: System prompts define agent behavior and are loaded by the orchestrator. These are internal instructions that apply globally across all reels.
- **`templates/`**: User-facing templates provide formats/starting points for users to fill in (e.g., `seed_template.md`).

---

## Workflow Summary

1.  **User** creates `00_seed.md` and `00_reel.yaml`.
2.  **Orchestrator** runs step-by-step:
    -   Reads inputs.
    -   Generates `.input.md` (prompt).
    -   Calls Agent/LLM.
    -   Saves `.output.md` and `.output.json`.
    -   Calls "Dumb Scripts" (using the JSON) to generate assets into `renders/`.
3.  **Final Assembly** reads all JSONs and assets, creates a timeline, and calls Remotion to render the final video.
