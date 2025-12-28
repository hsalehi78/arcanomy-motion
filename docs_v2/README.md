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

- **Reference**
  - `00-glossary.md` — Terms, thresholds, defaults

- **Product + philosophy**
  - `01-product-goals.md`
  - `02-core-primitive.md`

- **System design**
  - `03-repo-layout.md`
  - `04-run-folder-spec.md`
  - `05-domain-model.md`
  - `06-json-schemas.md`

- **Daily runbook**
  - `07-daily-workflow.md` — End-to-end phases + failure modes
  - `08-deterministic-verification.md`
  - `21-beat-sheet-sanity-check.md` — Deterministic timing invariants gate

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

- **CapCut assembly**
  - `18-capcut-kit-spec.md`

- **Open items**
  - `19-clarifications-needed.md` — Remaining `TODO(V2)` placeholders

- **Quality**
  - `20-testing-strategy.md` — Schema validation, unit tests, CI

## Schemas (`schemas/`)

| Schema | Purpose |
|--------|---------|
| `run_context.schema.json` | Phase 0 output |
| `claim_candidates.schema.json` | Phase 1 internal |
| `claim_locked.schema.json` | Phase 1 output |
| `dedupe_report.schema.json` | Phase 1 output |
| `script.schema.json` | Phase 2 internal |
| `beat_sheet.schema.json` | Phase 2 output (the control plane) |
| `asset_requirements.schema.json` | Phase 2 output |
| `script_verified.schema.json` | Phase 3 output |
| `asset_manifest.schema.json` | Phase 4 output |
| `blog.schema.json` | Blog source store (paragraph IDs) |
| `ledger_entry.schema.json` | Phase 9 output |

## Templates (`templates/`)

| Template | Purpose |
|----------|---------|
| `edit_plan.template.md` | CapCut assembly instructions |
| `blog.example.json` | Sample blog.json with paragraph IDs |

## Placeholders you must fill

Search for `TODO(V2)` in this folder and replace:
- **Supabase project ref** (for ledger writes)
- **Blog bundle index** (optional: `_indexes/ready.json` for blogs)
- **Paragraph ID persistence policy** (recommended: persist across edits)

Most other decisions have been locked in based on your answers.
