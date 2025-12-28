# Arcanomy Motion

## Quick Start

```bash
uv run arcanomy list-reels  # 1. Fetch a reel from CDN
uv run plan                 # 2. AI generates script
uv run visual_plan          # 3. AI creates image prompts
uv run assets               # 4. Generate images
uv run vidprompt            # 5. Refine video prompts
uv run videos               # 6. Generate video clips
uv run subsegments          # 7. Assemble 10s clips
uv run voice                # 8. ElevenLabs TTS
uv run captions             # 9. SRT subtitles
uv run charts               # 10. Animated charts
uv run kit                  # 11. Thumbnail + guides
```

## Other Commands

```bash
uv run current      # Show current reel + status
uv run guide        # Full help
uv run commit       # Git add/commit/push
```

## Setup

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - `ANTHROPIC_API_KEY`
   - `ELEVENLABS_API_KEY`

## Output

After running, check `guides/capcut_assembly_guide.md` for CapCut assembly instructions.

```
content/reels/<reel>/
  meta/           # plan.json, visual_plan.json, quality_gate.json
  renders/        # images/, videos/
  subsegments/    # 10s video clips
  voice/          # audio files
  captions/       # captions.srt
  charts/         # animated chart overlays
  thumbnail/      # thumbnail.png
  guides/         # assembly instructions
```
