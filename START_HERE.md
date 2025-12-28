# Arcanomy Motion — Quick Start

## The Workflow (2 commands)

```bash
uv run arcanomy list-reels   # Pick a reel from CDN
uv run arcanomy run          # Generate the CapCut kit
```

Then open `guides/capcut_assembly_guide.md` in CapCut Desktop.

---

## What This Pipeline Does

**Input:** Reel seeds from Arcanomy Studio (on CDN)  
**Output:** CapCut-ready assembly kit

```
Studio uploads seed → You fetch it → Pipeline generates kit → You assemble in CapCut
```

---

## Output Files

After running, you get:

| Folder | Contents |
|--------|----------|
| `subsegments/` | 10-second video clips |
| `voice/` | Voice audio per clip |
| `captions/` | SRT subtitle file |
| `charts/` | Animated chart overlays (if any) |
| `thumbnail/` | Thumbnail image |
| `guides/` | CapCut assembly instructions |

---

## Commands

| Command | What it does |
|---------|--------------|
| `uv run arcanomy list-reels` | List CDN reels, select to fetch |
| `uv run arcanomy run` | Run pipeline on current reel |
| `uv run arcanomy current` | Show current reel |
| `uv run arcanomy validate` | Check reel files are valid |
| `uv run arcanomy guide` | Show help |

---

## Setup

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
   - `ELEVENLABS_API_KEY`

---

## More Docs

- `docs/README.md` — Full pipeline documentation
- `docs/arcanomy-studio-integration/` — Seed file specifications
- `docs/charts/` — Chart templates
