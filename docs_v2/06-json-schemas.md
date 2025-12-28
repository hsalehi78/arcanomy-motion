# JSON Schemas (v2)

This app should treat schemas as **gates**, not suggestions.

Schemas live in `docs_v2/schemas/` and are intended to be used in code (Pydantic / Zod / Ajv).

## Required schemas (MVP)

- `blog.schema.json`
- `broll_index.schema.json`
- `music_index.schema.json`
- `run_context.schema.json`
- `claim_candidates.schema.json`
- `dedupe_report.schema.json`
- `claim_locked.schema.json`
- `script.schema.json`
- `script_verified.schema.json`
- `beat_sheet.schema.json`
- `asset_requirements.schema.json`
- `asset_manifest.schema.json`
- `kit_manifest.schema.json`
- `ledger_entry.schema.json`
- `provenance.schema.json`

## Schema philosophy

- Prefer “explicit enums” over free text for machine-critical fields.
- Allow a `_notes` field for humans, but never rely on it.
- Always include `schema_version`.

