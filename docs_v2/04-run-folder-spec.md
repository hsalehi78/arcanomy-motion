# Run Folder Spec (`runs/YYYY-MM-DD_blogslug_dayN/`)

This is the on-disk contract for one daily reel run.

## Folder layout

```
runs/YYYY-MM-DD_blogslug_dayN/
  run_context.json

  01_claim/
    claim_candidates.json
    dedupe_report.json
    claim_locked.json

  02_script/
    script_v1.json
    beat_sheet_v1.json
    asset_requirements.json
    script_verified.json

  03_assets/
    asset_manifest.json
    clips/
      clip-01.mp4
      clip-02.mp4
      ...
    music/
      selected.mp3

  04_audio/
    vo.wav
    captions.srt
    emphasis.json

  06_overlays/
    chart.mp4                  # optional
    fallback_math_card.png     # optional

  07_capcut_kit/
    imports/
      vo.wav
      captions.srt
      clips/
        clip-01.mp4
        ...
      music/
        selected.mp3
      overlays/
        chart.mp4              # optional
        fallback_math_card.png # optional
    edit_plan.md

  99_provenance/
    provenance.json
    logs.txt
```

## Immutability rules

- **Inputs referenced by the run** must be captured in `run_context.json` (blog identifier + hash, ledger query window, library index hashes).
- If you regenerate, increment versioned filenames or store `*_v2.json` rather than overwriting silently.

