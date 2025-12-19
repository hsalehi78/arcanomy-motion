# Arcanomy Reels Generator — Project Docs (Index)

These docs are intentionally split into small, focused files in the `docs/` folder.

## What we agreed (non-negotiables)
- **Local orchestration** (Python + agents run locally; API calls go out as needed)
- **CSV is source-of-truth** for any numbers shown on screen (auditability)
- **ElevenLabs** for voice (even if it’s “your voice,” it’s still ElevenLabs)
- **Output = final MP4** (distribution is out of scope)
- **Subtitles burned in by default**
- **Remotion** for deterministic charts + typography
- Optional: **video model** for background “vibe” clips (never for charts/text)

## Doc set
1. `01-vision-and-reel-types.md` — motivation, reel types, length bands, goals
2. `02-architecture-and-folder-structure.md` — repo layout + pipeline folder model + audit trail
3. `03-seed-and-config-format.md` — seed file and config YAML format
4. `04-pipeline-stages.md` — step-by-step pipeline (inputs/outputs per stage)
5. `05-visual-style-and-subtitles.md` — v1 style rules (Arcanomy look) + subtitle policy
6. `06-blog-ingestion.md` — importing content from Arcanomy blog

## Next build milestone (MVP)
**MVP = 1 reel end-to-end** that produces:
- `final.mp4` (9:16, 20–35s target)
- `final.srt` (also exported even though we burn captions)
- `metadata.json` (audit: CSV used, prompts, model IDs, timestamps)

When you’re ready, ask: **“Define the repo skeleton + commands for MVP.”**
