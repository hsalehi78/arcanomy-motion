# Arcanomy Reels Generator — Project Docs (Index)

These docs are intentionally split into small, focused files in the `docs/` folder.

## What we agreed (non-negotiables)
- **Local orchestration** (Python + agents run locally; API calls go out as needed)
- **CSV is source-of-truth** for any numbers shown on screen (auditability)
- **ElevenLabs** for voice AND sound effects (TTS + SFX APIs)
- **Output = final MP4** (distribution is out of scope)
- **Subtitles burned in by default**
- **Remotion** for deterministic charts + typography
- Optional: **video model** for background "vibe" clips (never for charts/text)

## Doc set
1. `01-vision-and-reel-types.md` — motivation, reel types, length bands, goals
2. `02-architecture-and-folder-structure.md` — repo layout + pipeline folder model + audit trail
3. `03-seed-and-config-format.md` — seed file and config YAML format
4. `04-pipeline-stages.md` — step-by-step pipeline (inputs/outputs per stage)
5. `05-visual-style-and-subtitles.md` — v1 style rules (Arcanomy look) + subtitle policy
6. `06-blog-ingestion.md` — importing content from Arcanomy blog

## Pipeline Overview

**Run everything with one command:**
```bash
uv run full <reel-name>
```

Or run stages individually:

| Stage | Type | Goal | Command |
|-------|------|------|---------|
| ALL | Auto | **Run entire pipeline** | `uv run full` |
| 0 | Manual | Initialize reel | `uv run arcanomy new` |
| 1 | Agent | Research & fact-check | `uv run research` |
| 2 | Agent | Write script & segment | `uv run script` |
| 3 | Agent | Visual plan + image prompts | `uv run plan` |
| 3.5 | Script | Generate images | `uv run assets` |
| 4 | Agent | Refine video motion prompts | `uv run vidprompt` |
| 4.5 | Script | Generate video clips | `uv run videos` |
| 5 | Agent | Voice direction | `uv run voice` |
| 5.5 | Script | Generate narrator audio | `uv run audio` |
| 6 | Agent | Sound effects prompts | `uv run sfx` |
| 6.5 | Script | Generate sound effects | `uv run sfxgen` |
| 7 | Script | Final assembly (FFmpeg) | `uv run final` |
| 7.5 | Script | Captions burn-in (Remotion) | `uv run captions` |

## Configuration

Model and provider settings are in `src/config.py`. See `START_HERE.md` for details.

## Next build milestone (MVP)
**MVP = 1 reel end-to-end** that produces:
- `final.mp4` (9:16, 20–35s target)
- `final.srt` (also exported even though we burn captions)
- `metadata.json` (audit: CSV used, prompts, model IDs, timestamps)

When you're ready, ask: **"Define the repo skeleton + commands for MVP."**
