# Arcanomy Reels v2 — Documentation Pack (Copy Into New Repo)

This `docs_v2/` folder is a **ground-up blueprint** for rebuilding the Arcanomy reel generator with the correct core primitive:

**Beat Sheet → Asset Resolver → CapCut Kit**

It is designed so you can copy `docs_v2/` into a brand-new repository and begin implementation without importing the old pipeline assumptions.

## What this v2 app produces (MVP)

- `claim_locked.json`
- `script_verified.json`
- `beat_sheet.json` (asset-complete)
- `asset_manifest.json` (resolved clips + windows)
- `vo.wav` + `captions.srt` + `emphasis.json`
- `chart.mp4` (optional) or `fallback_math_card.png`
- `capcut_kit/` folder + `edit_plan.md`
- Concept Ledger entry append (so dedupe is real tomorrow)

## Index

- **Product + philosophy**
  - `01-product-goals.md`
  - `02-core-primitive.md`

- **System design**
  - `03-repo-layout.md`
  - `04-run-folder-spec.md`
  - `05-domain-model.md`
  - `06-json-schemas.md`

- **Daily runbook**
  - `07-daily-workflow.md`
  - `08-deterministic-verification.md`

- **Assets + libraries**
  - `09-broll-library.md`
  - `10-music-library.md`
  - `11-chart-overlays.md`

- **Storage**
  - `12-r2-storage.md`
  - `13-blog-source-store.md`

- **Database**
  - `14-supabase-concept-ledger.md`

- **CLI + ops**
  - `15-cli-contract.md`
  - `16-observability-and-provenance.md`

- **Migration**
  - `17-v1-to-v2-migration.md`

## Placeholders you must fill

Search for `TODO(V2)` in this folder and replace:
- **CDN base URLs / buckets** (if changing from current `cdn.arcanomydata.com`)
- **Supabase project + schema/table names**
- **Auth** (service role vs user auth) for writes
- **B-roll + music licensing / allowed sources**

