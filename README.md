# Arcanomy Motion

**AI-powered short-form video production pipeline for financial content.**

Arcanomy Motion is an automated video generation system that transforms data-driven financial insights into polished, brand-consistent short-form videos optimized for Instagram Reels, TikTok, and YouTube Shorts.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | Python 3.10+ | Pipeline control, LLM coordination, state management |
| **Video Rendering** | Remotion (React/TypeScript) | Deterministic chart & typography rendering |
| **Voice Synthesis** | ElevenLabs API | High-quality voiceover generation |
| **Image Generation** | DALL-E 3 / Imagen 2.5 | Static scene generation |
| **Video Generation** | Kling / Runway / Veo 3.1 | Image-to-video motion synthesis |
| **LLM Backend** | OpenAI / Anthropic / Google Gemini | Script writing, research, prompt engineering |
| **Package Management** | uv | Python dependency management |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ARCANOMY MOTION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────────────┐     │
│  │   User       │    │  Python          │    │   External APIs    │     │
│  │   Inputs     │───▶│  Orchestrator    │───▶│                    │     │
│  │              │    │                  │    │  • ElevenLabs      │     │
│  │ • seed.md    │    │  • LLM Agents    │    │  • OpenAI/Anthropic│     │
│  │ • reel.yaml  │    │  • Stage Runner  │    │  • Kling/Runway    │     │
│  │ • CSVs       │    │  • State Manager │    │  • Gemini          │     │
│  └──────────────┘    └────────┬─────────┘    └────────────────────┘     │
│                               │                                          │
│                               ▼                                          │
│                      ┌────────────────────┐                              │
│                      │   Remotion         │                              │
│                      │   (React/TS)       │                              │
│                      │                    │                              │
│                      │   • Charts (D3)    │                              │
│                      │   • Typography     │                              │
│                      │   • Composition    │                              │
│                      └────────┬───────────┘                              │
│                               │                                          │
│                               ▼                                          │
│                      ┌────────────────────┐                              │
│                      │   Final Output     │                              │
│                      │                    │                              │
│                      │   • final.mp4      │                              │
│                      │   • final.srt      │                              │
│                      │   • metadata.json  │                              │
│                      └────────────────────┘                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Design Pattern:** Smart Agent + Dumb Scripts

- **Smart Agents:** LLM-powered orchestrators that read project files, combine prompts, and make decisions
- **Dumb Scripts:** Single-purpose Python scripts that execute one API call (e.g., "generate one image", "render one video")

---

## Folder Structure

```
arcanomy-motion/
├── docs/                     # Project documentation
├── src/                      # Python orchestrator
│   ├── domain/               # Data models (Objective, Segment, Manifest)
│   ├── services/             # API wrappers (LLM, ElevenLabs, Remotion CLI)
│   ├── stages/               # Pipeline stage implementations
│   ├── utils/                # Helpers (IO, logging)
│   ├── main.py               # CLI entry point
│   └── commands.py           # CLI command definitions
├── remotion/                 # Video rendering engine
│   ├── src/
│   │   ├── compositions/     # Entry point compositions (MainReel, Shorts)
│   │   ├── components/       # Charts, typography, layouts
│   │   └── lib/              # Utilities, font loading
│   ├── public/               # Static assets
│   └── package.json
├── content/                  # User data & outputs (git-ignored)
│   └── reels/                # Individual reel projects
├── shared/                   # Global brand assets
│   ├── fonts/
│   ├── logos/
│   ├── audio/                # Intro/outro, watermark
│   └── templates/
├── tests/                    # Python tests
└── pyproject.toml            # Python dependencies
```

---

## Pipeline Stages

The pipeline follows a **granular audit trail** pattern. Every stage produces explicit input prompts (`.input.md`) and output results (`.output.md`, `.output.json`). State is defined entirely by files in the reel folder.

| Stage | Name | Input | Output | Action |
|-------|------|-------|--------|--------|
| **0** | Initialization | User creates | `00_seed.md`, `00_reel.yaml`, `00_data/` | Manual setup |
| **1** | Research | Seed + Data | `01_research.output.md` | Ground concept in facts |
| **2** | Story & Segmentation | Research | `02_story_generator.output.json` | Write script, split into 10s blocks |
| **3** | Visual Plan | Story | `03_visual_plan.output.md` | Define visual language |
| **3.5** | Image Prompt Gen | Visual plan | `03.5_generate_assets_agent.output.json` | Create image prompts |
| **4** | Video Prompt Engineering | Image prompts | `04_video_prompt_engineering.output.md` | Define motion directives |
| **4.5** | Video Generation | Motion prompts | `renders/bg_*.mp4` | Execute video API calls |
| **5** | Voice Prompting | Script | `05_voice_prompt_engineer.output.md` | Annotate prosody/emotion |
| **5.5** | Audio Generation | Voice prompts | `renders/voice/*.mp3` | Call ElevenLabs API |
| **6** | Music & SFX | Config | `06_music.output.json` | Select background audio |
| **7** | Assembly & Render | All assets | `final/final.mp4` | Remotion composition |

### Resume & Debug

- **Resume:** Orchestrator checks for last existing `.output.json` and continues from there
- **Debug:** Inspect any `.input.md` to see exact LLM prompt
- **Retry:** Delete `.output.*` files for the stage you want to re-run

---

## Content Duration Model

**All reels are built from 10-second blocks.** This aligns with AI video generation constraints and enforces editorial discipline.

| Length | Blocks | Use Case |
|--------|--------|----------|
| **10s** | 1 | Micro insight, hook, confronting statement |
| **20s** | 2 | **Core explainer (default)** — hook + chart reveal |
| **30s** | 3 | Expanded explainer — setup + data + consequence |
| **40s** | 4 | Transitional essay — psychology + data combo |
| **60s** | 6 | Mini essay — rare, depth over completion rate |

---

## Reel Types

Configure via `type` field in `00_reel.yaml`:

| Type | Description | Default Length |
|------|-------------|----------------|
| `chart_explainer` | Data-driven "show don't tell" — animated chart as visual core | 2–3 blocks |
| `text_cinematic` | Typography-first premium statements | 1 block |
| `story_essay` | Perspective-style psychological insights | 1–2 blocks |

---

## Input Files

### `00_seed.md` — Creative Brief

```markdown
# Hook
Stop trading until you understand this chart.

# Core Insight
Retail traders win 60% of trades but lose money overall 
because their losses are 2x larger than their wins.

# Visual Vibe
Dark, moody, cinematic. Red and black color palette.
Use abstract geometric shapes to represent data.

# Data Sources
- 00_data/trading_psych.csv
```

### `00_reel.yaml` — Machine Config

```yaml
title: "The Sunk Cost Fallacy"
type: "chart_explainer"
duration_blocks: 3          # 30 seconds

voice_id: "eleven_labs_adam"
music_mood: "tense_resolution"

aspect_ratio: "9:16"
subtitles: "burned_in"

audit_level: "strict"       # strict | loose
```

---

## Visual Design System

### Color Palette

| Usage | Color | Hex |
|-------|-------|-----|
| Background | Pure Black | `#000000` |
| Secondary BG | Near Black | `#0A0A0A` |
| Primary Text | Off-White | `#F5F5F5` |
| Highlight | Gold | `#FFD700` |
| Danger | Signal Red | `#FF3B30` |
| Chart Line | Gold | `#FFB800` |

### Typography Rules

- **Hook/Headline:** Bold, 15%+ screen height, off-white
- **Subtitles:** Medium weight, 8%+ screen height, white with black pill background
- **Safe Zone:** Bottom 15% reserved for platform UI — no text

### Motion Principles

- **Text In:** Snap (0–2 frames), no easing
- **Text Out:** Hard cut
- **Transitions:** Fast zoom (0.1s) or hard cut
- **Pacing:** Visual change every 2–3 seconds
- **Charts:** Draw-on animation (0.5–1.0s)

### Subtitle System

- Style: Karaoke (active word highlighted in gold)
- Active word scaled to 110%
- Semi-transparent black pill background (#000 @ 70%)
- Positioned in bottom 20%, centered

---

## Remotion Constants

```typescript
export const COLORS = {
  bg: "#000000",
  bgSecondary: "#0A0A0A",
  textPrimary: "#F5F5F5",
  textSecondary: "#FFFFFF",
  highlight: "#FFD700",
  chartLine: "#FFB800",
  danger: "#FF3B30",
};

export const SIZES = {
  hookHeightPercent: 0.15,
  subtitleHeightPercent: 0.08,
  safeZoneBottomPercent: 0.15,
};

export const ANIMATION = {
  textInFrames: 0,
  zoomDuration: 3,        // frames (0.1s @ 30fps)
  chartDrawDuration: 30,  // frames (1s @ 30fps)
};
```

---

## Output Artifacts

Each completed reel produces:

```
content/reels/YYYY-MM-DD-slug/
├── renders/
│   ├── bg_01.mp4, bg_02.mp4...    # Background video segments
│   ├── voice/                     # Narrator audio from Stage 5.5
│   │   ├── voice_01.mp3
│   │   └── voice_02.mp3
│   └── charts/                    # Optional chart cache
└── final/
    ├── final.mp4                  # Production-ready video (9:16)
    ├── final.srt                  # Subtitle file
    └── metadata.json              # Audit trail
```

### `metadata.json` Structure

```json
{
  "version": "1.0",
  "created_at": "2024-05-20T12:00:00Z",
  "config": { /* reel.yaml contents */ },
  "data_sources": ["00_data/trading.csv"],
  "model_ids": {
    "llm": "gpt-4o",
    "voice": "eleven_labs_adam",
    "video": "kling-v1"
  },
  "prompts_hash": "sha256:...",
  "render_duration_seconds": 120
}
```

---

## Development

### Prerequisites

- Python 3.10+
- Node.js 18+ (for Remotion)
- uv (Python package manager)
- pnpm (Node package manager) — `npm install -g pnpm`

### Installation

```bash
# Clone repository
git clone https://github.com/arcanomy/arcanomy-motion.git
cd arcanomy-motion

# Install Python dependencies
uv sync

# Install Remotion dependencies
cd remotion && pnpm install
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
KLING_API_KEY=...
GOOGLE_API_KEY=...
```

### CLI Commands (Planned)

```bash
# Create new reel from template
uv run arcanomy new "my-reel-slug"

# Run full pipeline
uv run arcanomy run content/reels/2024-05-20-sunk-cost/

# Run specific stage
uv run arcanomy run --stage 3 content/reels/2024-05-20-sunk-cost/

# Preview in Remotion
cd remotion && npm run preview

# Render final video
uv run arcanomy render content/reels/2024-05-20-sunk-cost/
```

---

## Quality Checklist

Before shipping any reel:

- [ ] **Frame 0:** Is the hook text fully visible?
- [ ] **Mobile Test:** Is text readable at 25% scale?
- [ ] **Safe Zone:** Is bottom 15% empty?
- [ ] **Pacing:** Does something change every 3 seconds?
- [ ] **Contrast:** Is it Black/White/Gold?
- [ ] **Auditability:** Can you trace every number to a CSV?

---

## Non-Negotiables

1. **Local orchestration** — Python + agents run locally; API calls go out as needed
2. **CSV is source-of-truth** — All numbers shown on screen must trace to owned data files
3. **ElevenLabs for voice** — Consistent, high-quality speech synthesis
4. **Output = final MP4** — Distribution is out of scope
5. **Subtitles burned in** — Accessibility and retention by default
6. **Remotion for deterministic rendering** — Charts and typography are pixel-perfect
7. **Video models for vibe only** — Never for charts or text overlays

---

## License

Proprietary — Arcanomy © 2024

