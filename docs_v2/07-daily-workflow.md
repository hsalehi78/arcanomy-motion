# Daily Workflow (v2) — End-to-End

This is the operational runbook that should map 1:1 to CLI commands.

## Phase 0 — Initialization

**Goal:** create run folder + load context.

- Create: `runs/YYYY-MM-DD_blogslug_dayN/`
- Load blog source (`blog.json`) + compute hash
- Query Concept Ledger for this blog + recent history
- Compute `dayN = count(ledger entries for blog_slug) + 1`

**Output:** `run_context.json`

## Phase 1 — Claim selection + dedupe

**Goal:** select a provable, non-repetitive claim.

- Generate 8 candidates with:
  - `claim_text` (one sentence)
  - `primary_tag`
  - `core_stat` (or null)
  - `proof_anchor_ids[]`
  - `needs_chart` + `chart_template` (or null)
  - `format`

**Dedupe gates**

- Block if `primary_tag` used in last 7 reels (same blog)
- Block if `core_stat_hash` used in last 14 reels
- Block if semantic similarity to last 7 takeaways > threshold

If fewer than 2 pass:
- regenerate with an explicit avoid list (max 3 attempts)
- otherwise force a micro-claim from unused blog section

**Output:** `01_claim/claim_locked.json` + `dedupe_report.json`

## Phase 2 — Script + Beat Sheet + Asset Requirements

**Goal:** produce a production spec.

- Generate script structure: HOOK / TRUTH / PROBLEM / FIX / CLOSE
- 120–160 words target
- Every stat references `proof_anchor_ids`

Generate `beat_sheet.json`:
- beats with `t_start`, `t_end`
- caption + emphasis tokens
- visual slots:
  - `BROLL_SLOT` (required tags + composition)
  - `CHART_SLOT` (template + props + duration)
  - `MATH_CARD_SLOT`
  - `AI_SLOT` (fallback only)
- events: ZOOM, SOUND_RESET, OVERLAY_IN, OVERLAY_OUT

Generate `asset_requirements.json`:
- min clips (6–10 default)
- cadence target (2–3s)
- chart window (max 10s, optional)
- music mood tag

**Output:**
- `02_script/script_v1.json`
- `02_script/beat_sheet_v1.json`
- `02_script/asset_requirements.json`

## Phase 3 — Deterministic verification gate

**Goal:** remove hallucinations before asset work.

- Parse script for:
  - numbers
  - “research shows” / “studies”
  - causal claims
- Each must match a proof anchor snippet
- If not: weaken/remove/replace line
- Max 2 rewrite cycles; then drop the stat

**Output:** `02_script/script_verified.json`

## Phase 4 — Resolve visuals from local libraries (no browsing)

### 4A — Resolve b-roll per beat

For each `BROLL_SLOT`:
- Query `content/libraries/broll/index.json`
- Exclude clips used in last 14 days (ledger)
- Score: composition match > novelty > motion smoothness
- Assign `source_in`, `source_out` matching beat duration

If insufficient unique clips:
- fill with abstract transitions pack (recommended to create a small pack if you don’t have one yet)
- if still short: `AI_SLOT` fallback (image→motion)

**Output:** `03_assets/clips/` + `asset_manifest.json`

### 4B — Resolve music

- Pick track matching mood tag
- Exclude last 7 days

**Output:** `03_assets/music/selected.mp3`

## Phase 5 — Audio + captions

- Generate VO from verified script → `vo.wav`
- Generate SRT with constraints:
  - ≤42 chars per line
  - ≤6 words per line
  - break at pauses
  - never split numbers
- Generate `emphasis.json` from beat sheet

**Output:** `04_audio/vo.wav`, `captions.srt`, `emphasis.json`

## Phase 6 — Charts (only if beat sheet demands)

- Render chart overlay
- If render fails: generate fallback math card PNG

**Output:** `06_overlays/chart.mp4` OR `fallback_math_card.png`

## Phase 7 — Assemble CapCut Kit

Create `07_capcut_kit/` with `imports/` and `edit_plan.md`.

`edit_plan.md` must include:
- total duration
- time mapping table `t_start–t_end → clip file → source_in/out`
- chart placement + scale
- zoom timestamps
- sound reset timestamp
- caption emphasis words + timestamps
- music ducking + fade in/out

## Phase 8 — CapCut finishing (manual)

Follow mechanical steps:
- import kit
- VO on A1, lock
- clips on V1
- chart on V2 (if any)
- SRT captions + preset
- emphasis per plan
- music on A2 (duck under VO)
- zoom + sound reset per timestamps
- export `final.mp4`

## Phase 9 — Update ledger

Append what shipped:
- claim + tags + stat hash
- clips IDs + windows
- music
- chart template/data
- takeaway + hook premise

