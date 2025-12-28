# Arcanomy Motion

**CapCut-kit pipeline for short-form video production.**

Arcanomy Motion converts **Arcanomy Studio reel seeds** into a **CapCut-ready assembly kit** for Instagram Reels, TikTok, and YouTube Shorts.

- Seeds (from Studio): `inputs/claim.json`, `inputs/seed.md`, optional `inputs/chart.json`
- Outputs (from Motion): 10-second subsegments, 10-second chart overlays, voice WAVs, line-level SRT captions, guides, thumbnail, and a quality gate
- Final assembly: **manual in CapCut Desktop** (canonical doctrine)

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | Python 3.10+ | Pipeline control, LLM coordination |
| **Charts** | Remotion (React/TypeScript) | Animated chart rendering |
| **Voice Synthesis** | ElevenLabs API | High-quality voiceover generation |
| **LLM Backend** | OpenAI / Anthropic / Gemini | Script writing, planning |
| **Package Management** | uv | Python dependency management |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ARCANOMY MOTION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────┐    ┌──────────────────┐    ┌────────────────┐ │
│  │ Inputs (from Studio)  │    │  Python          │    │ External APIs   │ │
│  │                      │───▶│  Orchestrator    │───▶│ (optional)      │ │
│  │ • claim.json         │    │                  │    │ • ElevenLabs    │ │
│  │ • seed.md            │    │  • Planner       │    │ • LLMs          │ │
│  │ • chart.json (opt)   │    │  • Stage Runner  │    │ • Image/Video   │ │
│  └──────────────────────┘    └────────┬─────────┘    └────────────────┘ │
│                               │                                          │
│                               ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                     Output: CapCut Kit                          │     │
│  │                                                                  │     │
│  │   subsegments/     voice/          charts/       guides/        │     │
│  │   subseg-01.mp4    subseg-01.wav   chart-*.mp4   assembly.md    │     │
│  │   subseg-02.mp4    subseg-02.wav                 checklist.md   │     │
│  │                                                                  │     │
│  │   captions/        thumbnail/      meta/                        │     │
│  │   captions.srt     thumbnail.png   plan.json, provenance.json   │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                               │                                          │
│                               ▼                                          │
│                      ┌────────────────────┐                              │
│                      │   CapCut Desktop   │                              │
│                      │   (manual assembly)│                              │
│                      └────────────────────┘                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1) Fetch a reel from CDN
uv run arcanomy list-reels

# 2) Run each stage
uv run plan          # AI generates script + provenance
uv run visual_plan   # AI creates image prompts
uv run assets        # Generate images
uv run vidprompt     # Refine video prompts
uv run videos        # Generate video clips
uv run subsegments   # Assemble 10s clips
uv run voice         # ElevenLabs TTS
uv run captions      # SRT subtitles
uv run charts        # Animated charts
uv run kit           # Thumbnail + guides

# 3) Assemble in CapCut using guides/capcut_assembly_guide.md
```

See `START_HERE.md` for the full quick start guide.

---

## Pipeline Stages

| Stage | Output | Description |
|-------|--------|-------------|
| **plan** | `meta/plan.json`, `meta/provenance.json` | Generate segments and subsegments |
| **visual_plan** | `meta/visual_plan.json` | Visual prompts for seed images + 10s clips |
| **assets** | `renders/images/composites/*.png` | Generate seed images |
| **vidprompt** | `meta/video_prompts.json` | Refine motion prompts for 10s clips |
| **videos** | `renders/videos/clip_XX.mp4` | Generate 10s AI video clips |
| **subsegments** | `subsegments/subseg-*.mp4` | 10.0s background videos |
| **voice** | `voice/subseg-*.wav` | Voice audio per subsegment |
| **captions** | `captions/captions.srt` | Line-level SRT captions |
| **charts** | `charts/chart-*.mp4` | Animated chart renders |
| **kit** | `thumbnail/`, `guides/` | Final assembly kit |

---

## Folder Structure

```
arcanomy-motion/
├── docs/                     # Documentation
│   ├── README.md             # Full pipeline docs
│   ├── charts/               # Chart templates
│   ├── principles/           # Operating doctrine
│   └── _archive/             # Legacy V1 docs
├── src/                      # Python orchestrator
│   ├── pipeline/             # Pipeline stages
│   ├── services/             # API wrappers
│   ├── domain/               # Data models
│   ├── utils/                # Helpers
│   └── commands.py           # CLI commands
├── remotion/                 # Chart rendering
│   └── src/components/charts/
├── content/                  # User data (git-ignored)
│   └── reels/                # Reel projects
├── shared/                   # Brand assets
└── pyproject.toml
```

---

## Reel Structure

```
content/reels/<slug>/
  inputs/
    claim.json           # Required
    seed.md              # Required
    chart.json           # Optional (Remotion chart props)

  meta/
    provenance.json      # Run metadata
    plan.json            # Segment plan
    quality_gate.json    # Quality check

  subsegments/           # 10.0s video clips
  voice/                 # Voice audio
  captions/              # SRT file
  charts/                # Chart videos
  thumbnail/             # Thumbnail image
  guides/                # Assembly instructions
```

---

## CLI Reference

```bash
# CDN Integration
uv run arcanomy list-reels           # List and fetch reels from CDN

# Pipeline Stages (run in order)
uv run plan          # AI generates script + provenance
uv run visual_plan   # AI creates image prompts
uv run assets        # Generate images
uv run vidprompt     # Refine video prompts
uv run videos        # Generate video clips
uv run subsegments   # Assemble 10s clips
uv run voice         # ElevenLabs TTS
uv run captions      # SRT subtitles
uv run charts        # Animated charts
uv run kit           # Thumbnail + guides

# Reel Management
uv run arcanomy new <slug>           # Create new reel
uv run arcanomy reels                # List/select local reels
uv run current                       # Show current reel
uv run arcanomy status               # Show pipeline status

# Tools
uv run arcanomy preview              # Start Remotion preview
uv run arcanomy render-chart <json>  # Render chart from JSON
uv run guide                         # Show help
uv run commit                        # Git add/commit/push
```

---

## Charts

Render animated charts from JSON:

```bash
uv run arcanomy render-chart docs/charts/bar-chart-basic.json
```

Available types: bar, horizontal bar, stacked bar, pie, line, scatter, progress, number counter.

See `docs/charts/` for templates and full documentation.

---

## Development

### Prerequisites

- Python 3.10+
- Node.js 18+ (for Remotion)
- uv (Python package manager)
- pnpm (Node package manager)

### Installation

```bash
git clone https://github.com/arcanomy/arcanomy-motion.git
cd arcanomy-motion

# Python
uv sync

# Remotion
cd remotion && pnpm install
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
GOOGLE_API_KEY=...
```

---

## Documentation

| Path | Contents |
|------|----------|
| `START_HERE.md` | Quick start guide |
| `docs/README.md` | Full pipeline documentation |
| `docs/charts/` | Chart templates and JSON schema |
| `docs/principles/` | Operating doctrine |
| `docs/_archive/` | Legacy V1 documentation |

---

## License

Proprietary — Arcanomy © 2024
