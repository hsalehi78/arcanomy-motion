# Arcanomy Motion

## Quick Start

```bash
uv run reels        # 1. Pick a reel
uv run init         # 2. Create provenance
uv run plan         # 3. AI generates script
uv run visual_plan  # 4. AI creates image prompts
uv run assets       # 5. Generate images
uv run vidprompt    # 6. Refine video prompts
uv run videos       # 7. Generate video clips
uv run subsegments  # 8. Assemble 10s clips
uv run voice        # 9. ElevenLabs TTS
uv run captions     # 10. SRT subtitles
uv run charts       # 11. Animated charts
uv run kit          # 12. Thumbnail + guides
```

Or run all at once: `uv run run-all`

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
