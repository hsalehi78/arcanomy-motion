# Domain Model (v2)

## Core concepts

- **BlogSource**
  - Immutable blog content split into stable paragraphs (`p_001`, `p_002`, …)
  - Optional extracted tables/charts as structured objects

- **ClaimCandidate**
  - Candidate claim with tags + proof anchors + optional chart intent

- **ClaimLocked**
  - The selected claim for the run, with dedupe decision justification

- **Script**
  - The final voiceover text (120–160 words target)
  - Every stat/casual claim references `proof_anchor_ids`

- **Beat**
  - A timed unit of the reel. Each beat includes:
    - `t_start`, `t_end`
    - `vo_text`, `caption_text`
    - `visual_slot` (B-roll, chart, math card, AI fallback)
    - `events[]` (zoom, overlay in/out, sound reset)

- **AssetManifest**
  - Resolved assets for the beat sheet:
    - b-roll clip selection + windows (source in/out)
    - music selection
    - overlays generated

- **ConceptLedgerEntry**
  - Permanent record of what shipped
  - Used for dedupe gates and reproducibility

## Determinism boundaries

- Beat sheet generation is creative (LLM), but constrained by schemas.
- Asset resolution is deterministic, scored, and ledger-aware.
- Verification is deterministic (string/anchor matching + max rewrite cycles).

