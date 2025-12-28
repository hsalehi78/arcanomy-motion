# Glossary (v2)

Standard terms used throughout the v2 documentation.

---

## Core Concepts

| Term | Definition |
|------|------------|
| **Beat** | A timed segment of the reel (typically 2–4 seconds) containing one visual slot, one VO line, and zero or more events. The beat sheet is an array of beats. |
| **Beat Sheet** | The central production spec: an ordered list of beats that fully describes what happens at each moment of the reel. Drives asset resolution and CapCut assembly. |
| **Proof Anchor** | A stable paragraph ID (`p_001`, `p_002`, etc.) in the blog source that a claim or statistic references. Used for deterministic verification. |
| **Visual Slot** | A placeholder in a beat specifying what visual should appear. Types: `BROLL_SLOT`, `CHART_SLOT`, `MATH_CARD_SLOT`, `AI_SLOT`. |
| **Dedupe Gate** | A blocking check that prevents repetitive content (same tag, same stat, similar takeaway) from being selected. |
| **Concept Ledger** | The Supabase table that stores every shipped reel's metadata. Used for dedupe queries and reproducibility. |
| **Run** | A single daily execution of the pipeline for one blog. Produces a run folder with all artifacts. |
| **CapCut Kit** | The final deliverable: a folder of imports + `edit_plan.md` that an editor can mechanically assemble in CapCut. |

---

## File Types

| File | Purpose |
|------|---------|
| `run_context.json` | Immutable snapshot of inputs at run start (blog hash, ledger state, library hashes). |
| `claim_locked.json` | The selected claim after dedupe passes. |
| `beat_sheet_v1.json` | The production spec with all beats, visual slots, and events. |
| `asset_manifest.json` | Resolved clips and music, with source windows. |
| `script_verified.json` | Script after deterministic verification (no hallucinated stats). |
| `edit_plan.md` | Human-readable assembly instructions for CapCut. |

---

## Events

| Event | Description |
|-------|-------------|
| `ZOOM` | Camera zoom in/out at a specific timestamp. Payload includes `scale` and `direction`. |
| `SOUND_RESET` | Audio transition marker (typically a whoosh + music micro-rise). |
| `OVERLAY_IN` / `OVERLAY_OUT` | Chart or overlay appears/disappears. |

---

## Path Conventions

- All `path` fields in JSON should be **POSIX-style** (forward slashes) and **relative** to a known root (e.g., `content/libraries/broll/`), even if running on Windows.
- This keeps manifests stable across OSes and avoids accidental absolute-path leakage.

---

## Thresholds & Defaults

| Name | Value | Notes |
|------|-------|-------|
| Semantic similarity threshold | 0.85 (cosine) | Block claim if similarity to recent takeaways exceeds this. |
| Clip reuse window | 14 days | Exclude clips used in ledger within this window. |
| Music reuse window | 7 days | Exclude tracks used in ledger within this window. |
| Tag reuse window | 7 reels (same blog) | Block `primary_tag` if used recently for the same blog. |
| VO max retry | 3 | Retry TTS API failures before aborting. |
| Chart render timeout | 120 seconds | Fallback to math card PNG if exceeded. |
| Default ducking | 70% (CapCut) / −6 dB | Music level under VO. |

