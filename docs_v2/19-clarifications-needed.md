# Clarifications — Resolved & Still Open

## ✅ Resolved (locked into docs)

| Topic | Decision | Doc updated |
|-------|----------|-------------|
| CDN base URL | Keep `https://cdn.arcanomydata.com` | `12-r2-storage.md` |
| R2 bucket | `arcanomy` bucket, `content/` prefix | `12-r2-storage.md` |
| Reel seed index | Keep `_indexes/ready.json` | `12-r2-storage.md` |
| Supabase auth model | User-auth + RLS | `14-supabase-concept-ledger.md` |
| Ledger table | `public.concept_ledger` (solo/simple) | `14-supabase-concept-ledger.md` |
| Clip ID generation | Hash from filename + file content | `09-broll-library.md` |
| Vocals in music | Allowed (but default to instrumental) | `10-music-library.md` |
| Chart schema | Keep current Remotion schema | `11-chart-overlays.md` |
| Semantic similarity threshold | 0.85 cosine | `07-daily-workflow.md` |
| Ducking default | 70% CapCut / −6 dB | `07-daily-workflow.md`, `00-glossary.md` |
| Transitions pack | None yet; recommend creating 10–30 clips | `09-broll-library.md` |
| Folder numbering gap | Reserved `05_qc/` for QA artifacts | `04-run-folder-spec.md` |
| Blog store versioning | One folder per version (`v1/`, `v2/`, …) | `13-blog-source-store.md` |
| Paragraph ID policy | Stable within a blog version; new version on blog edits | `13-blog-source-store.md` |

---

## 🔴 Still Open — TODO(V2)

Fill these before implementation begins:

### 1. Supabase project ref

Which Supabase project is v2 writing to? (e.g., `https://xyzabc.supabase.co`)

→ Update `14-supabase-concept-ledger.md` once known.

### 2. Blog bundle index (optional)

Do you want a v2-specific index file for parsed blog bundles?

- Option A: Yes, at `content/blogs/_indexes/ready.json`
- Option B: No, fetch by identifier only

→ If yes, update `13-blog-source-store.md`.

### 3. Paragraph IDs (already decided)

Resolved via per-version folders (see above). Proof anchors are stable because old runs reference `content/blogs/{id}/vN/blog.json`.

---

## Not Blocking MVP

These can be deferred:

- **Faces/logos policy** in b-roll — decide per-tag if needed
- **Exact ducking dB** — 70% CapCut default works; tune later
- **Transitions pack** — ship MVP without; add later
