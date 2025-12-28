# CLI Contract (v2)

The CLI should map directly to the daily workflow.

## Commands (MVP)

### `reels init`

- inputs: `blog_identifier` (or local blog path)
- outputs: creates run folder + `run_context.json`

### `reels claim`

- outputs: `01_claim/claim_candidates.json`, `dedupe_report.json`, `claim_locked.json`

### `reels script`

- outputs: `02_script/script_v1.json`, `beat_sheet_v1.json`, `asset_requirements.json`

### `reels verify`

- outputs: `02_script/script_verified.json`

### `reels resolve-assets`

- outputs: `03_assets/asset_manifest.json` + resolved files in `03_assets/`

### `reels audio`

- outputs: `04_audio/vo.wav`, `captions.srt`, `emphasis.json`

### `reels overlays`

- outputs: `06_overlays/chart.mp4` or `fallback_math_card.png`

### `reels kit`

- outputs: `07_capcut_kit/` + `edit_plan.md`

### `reels ledger append`

- writes: Concept Ledger entry to Supabase

### `reels run`

- runs all steps in order and stops on first gate failure.

## Global flags

- `--run <path>`: operate on an existing run folder
- `--dry-run`: do not write external systems (no Supabase writes)
- `--force`: allow overwrites (should still version files)

