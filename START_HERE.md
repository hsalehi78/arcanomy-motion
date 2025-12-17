# Arcanomy Motion — Quick Start Guide

> AI-powered short-form video production pipeline for financial content

Run `uv run guide` anytime to see this in your terminal.

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

### 2. Run the Pipeline (6 Stages)

Once you've set your reel, run each stage in order:

| Stage | Command | What It Does |
|-------|---------|--------------|
| 1 | `uv run research` | Gathers facts, stats, psychology from seed |
| 2 | `uv run script` | Writes voiceover + 10-second segments |
| 3 | `uv run plan` | Defines characters, style, mood |
| 4 | `uv run assets` | Generates image/video prompts |
| 5 | `uv run assemble` | Creates Remotion manifest |
| 6 | `uv run deliver` | Renders final MP4 |

Or run the full pipeline at once:
```bash
uv run arcanomy run content/reels/2025-12-15-my-reel
```

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
| `uv run guide` | Show this guide in terminal |
| `uv run current` | Show current reel + status |
| `uv run set <slug>` | Set working reel (partial match OK) |
| `uv run research` | Run Stage 1 on current reel |
| `uv run script` | Run Stage 2 on current reel |
| `uv run plan` | Run Stage 3 on current reel |
| `uv run assets` | Run Stage 4 on current reel |
| `uv run assemble` | Run Stage 5 on current reel |
| `uv run deliver` | Run Stage 6 on current reel |
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
| `uv run arcanomy guide` | Show workflow guide |

---

## Reel Folder Structure

```
content/reels/2025-12-15-my-reel/
├── 00_seed.md                          <- Your creative brief (edit this)
├── 00_reel.yaml                        <- Config: duration, voice, type
├── 00_data/                            <- CSV files for charts
│
├── 01_research.input.md                <- Prompt sent to LLM
├── 01_research.output.md               <- Stage 1: Research notes
│
├── 02_story_generator.input.md
├── 02_story_generator.output.md        <- Stage 2: Human-readable script
├── 02_story_generator.output.json      <- Stage 2: Segments for pipeline
│
├── 03_character_generation.input.md
├── 03_character_generation.output.md   <- Stage 3: Visual plan
│
├── renders/                            <- Generated media assets
│   ├── bg_01.mp4
│   ├── voice_01.mp3
│   └── ...
│
└── final/
    ├── final.mp4                       <- The output video
    ├── final.srt                       <- Subtitle file
    └── metadata.json                   <- Audit trail
```

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

**Debug prompts:** Check `*.input.md` files to see exactly what was sent to the LLM

**View status:** 
```bash
uv run current                    # Quick status of current reel
uv run arcanomy status <path>     # Full pipeline status
```

---

## The 10-Second Block Philosophy

All Arcanomy reels are built from **10-second blocks**. This aligns with:
- AI video generation constraints
- Editorial discipline (every block must earn its place)
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

**Ready to start?**

```bash
uv run arcanomy ingest-blog    # Pick a blog
uv run research                # Stage 1
uv run script                  # Stage 2
# ... continue through stages
```

