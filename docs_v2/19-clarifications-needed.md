# Clarifications Needed (fill these once) — TODO(V2)

Answering these lets the v2 docs become fully “drop-in” for your new repo.

## R2 / CDN

- **CDN base URL**: keep `https://cdn.arcanomydata.com` ✅ (confirmed)
- **R2 layout**: bucket `arcanomy`, prefix `content/` ✅ (confirmed from your console screenshot)
- **Reel seed index**: keep `content/reels/_indexes/ready.json` ✅ (recommended default; confirm if you want a different name)
- **Blog bundle index (v2)**: `TODO(V2)` do you want:
  - no index (always fetch by identifier), or
  - `content/blogs/_indexes/ready.json` (recommended)

## Blog source store

- **Source of truth**:
  - keep using existing blog MDX at `/content/posts/{id}/content.mdx`, or ingest from elsewhere?
- **Versioning strategy**:
  - one folder per blog version, or a `version` field inside `blog.json`?
- **Paragraph ID policy**:
  - do you require IDs to persist even if the blog is edited later (recommended), or is “latest only” acceptable?

## Supabase

- **Project**: `TODO(V2)` paste your Supabase project URL (or project ref) so we can lock the integration docs.
- **Auth model**:
  - user-auth ✅ (confirmed)
- **Tables**:
  - confirm the ledger table name (e.g., `public.concept_ledger`)
  - keep it simple (ledger only for MVP) ✅ (confirmed)
- **RLS**:
  - with user-auth: **enable RLS** ✅ (recommended default; see `14-supabase-concept-ledger.md`)

## B-roll library

- **Clip IDs**: generate deterministically ✅ (confirmed)
- **Hard constraints**:
  - `TODO(V2)` default recommendation: disallow `has_faces=true` and `has_logos=true` unless the beat explicitly requires it.
- **Transitions pack**:
  - none yet ✅ (confirmed) → recommended to create a small pack (10–30 clips)

## Music library

- **Allowed**: vocals allowed ✅ (confirmed)
- **Ducking targets**: `TODO(V2)` if you don’t have a preference, start with:
  - music at ~15–25% volume under VO
  - fade in/out 0.3–0.6s
  - after SOUND_RESET: +10–20% for 0.5–1.0s

## Charts

- Keep current Remotion chart schema as-is (recommended), or do you want a simplified v2-only overlay schema? keep it

