# Refactor RFC — V2 CapCut Kit Pipeline (Canonical, Locked)

**Status:** Draft for approval (Phase 0 — no code changes yet)  
**Canonical doctrine source:** `docs/principles/arcanomy-reels-operating-system.md`  
**This RFC purpose:** Convert locked doctrine into unambiguous engineering contracts, flags, artifacts, and a phased migration plan.

---

## 1) Canonical doctrine (decisions, not suggestions)

### 1.1 Final boss doctrine
- **Final boss:** `docs/principles/arcanomy-reels-operating-system.md`
- All other docs and systems must either:
  - be updated to conform, or
  - be moved behind `--legacy`, or
  - be explicitly deprecated/archived.

### 1.2 Output boundary (what the system produces)
- **Canonical output (v2 mainline):** **CapCut-ready assembly kit + guide**
- **Not produced by default:** final assembled MP4
- **Legacy only:** FFmpeg/Remotion final assembly may exist behind `--legacy-final`

### 1.3 Production timing model (10s cap)
- **Subsegment (atomic production unit):** exactly **10.0 seconds**, immutable
- **Segment (story unit):** **1–2 subsegments** (10–20s), conceptual beats
- **Reel length:** **3–6 subsegments** (30–60s), hard cap 60s
- **Micro-reels (10/20s):** not supported in v2 mainline unless explicitly added later

### 1.4 Captions
- **Canonical captions styling:** CapCut preset (yellow text + black stroke + glow + keyword highlighting)
- **Canonical caption data output:** `captions.srt`
  - **Line-level only** (no karaoke/word timing)
  - **Timed via voice alignment** (not heuristics)
  - **Hard rule:** SRT entries **must not cross subsegment boundaries**
- **Deprecated:** Remotion karaoke pill captions; caption burn-in

### 1.5 Remotion scope
- **Canonical:** Remotion renders **charts only**
- Allowed outputs:
  - chart MP4s (10.0s per subsegment usage)
  - optional overlay MP4s (arrows/highlights) if needed later
- Disallowed in v2 mainline:
  - full scene composition
  - narrative templates
  - captions

### 1.6 Charts: duration + compositing background
- **Charts must render to 10.0s** per subsegment where used
  - If a chart “spans 20s” (2 subsegments), render **two** 10.0s files (Part A / Part B)
- **No arbitrary-length charts** in v2 mainline
  - Optional future flag: `--legacy-chart-flex` (explicitly non-canonical)
- **Background strategy:**
  - Default: **alpha (transparent) MP4** if reliably supported end-to-end
  - Fallback: **green screen** `#00FF00` + CapCut chroma key
  - Opaque black cutaway: deprecated/rare exception

Alpha capability detection (canonical):
- The pipeline must perform a **capability check** at runtime (render a tiny 1–2 frame test overlay and inspect for alpha support). If alpha is not reliably preserved through the configured renderer/encoder, it must **auto-select** the green-screen fallback and record the decision in `v2/meta/provenance.json`.

### 1.7 Visual generation (baseline determinism)
- v2 mainline subsegment visuals are:
  - breathing stills / inert motion (Ken Burns-style), OR
  - curated inert loops from a local library
- **No generative background video** (Runway/Kling) in v2 mainline
  - Optional later: `--bg=generative` with full provenance (prompt + seed + model/version hash)

### 1.8 Audio (kit contents)
- **Voice:** required, per subsegment: `voice/subseg-XX.wav`
- **Sound resets:** instructions only using a fixed local SFX library (no API generation)
- **Music:** manual selection in CapCut; guide specifies constraints (low arousal, no vocals, no drops)

### 1.9 Auditability
- `audit_level` is controlled by `claim.json`: `basic` | `strict`
- **Strict** requires:
  - chart provenance: CSV path + columns + transform steps + input file hash + output values hash
  - deterministic reruns (zero diffs)
- **Canonical transform spec:** constrained JSON DSL (no scripts)

### 1.10 Legacy boundary
- **v2 is default**
- v1 remains runnable behind `--legacy`
- **Legacy is frozen** (no new features; bugfixes only)

---

## 2) V2 inputs (contracts)

### 2.1 Canonical v2 inputs
Required:
- `inputs/claim.json`
- `inputs/data.json` (required even if `type: "none"`)

Optional:
- `inputs/seed.md` (non-authoritative notes; never required)

### 2.2 `claim.json` (minimal required fields)
Required:
- `claim_id`: string
- `claim_text`: string (the sacred sentence)
- `supporting_data_ref`: string (points to data.json dataset id or embedded id)
- `audit_level`: `"basic" | "strict"`

Optional:
- `tags`: string[]
- `risk_notes`: string
- `thumbnail_text`: string

Non-goals (v2 input):
- hook/CTA/audience fields are not required here; those belong upstream.

### 2.3 `data.json` (high-level intent)
This is a **bundle of datasets** that can be referenced by charts and claims.
At minimum it must support:
- `type: "none"` (no datasets)
- `datasets[]` with:
  - `dataset_id`
  - `source.csv.path` (local path inside reel folder)
  - optional schema hints (column names, units)

> Note: The *chart specs* carry the strict transform DSL. `data.json` provides dataset catalog + source mapping.

---

## 3) V2 outputs: the CapCut kit layout (canonical)

### 3.1 Kit folder structure (per reel)

```
content/reels/<reel-slug>/
  inputs/
    claim.json
    data.json
    seed.md (optional)

  v2/
    meta/
      provenance.json              # run metadata, hashes, tool versions
      quality_gate.json            # pass/fail + reasons + counters (3–2–1 instructions present)

    subsegments/
      subseg-01.mp4                # exactly 10.0s
      subseg-02.mp4
      ...

    charts/
      chart-subseg-01.mp4          # exactly 10.0s if used
      chart-subseg-02.mp4
      ...

    voice/
      subseg-01.wav                # aligned for 10.0s timeline
      subseg-02.wav
      ...

    captions/
      captions.srt                 # line-level, aligned to voice, bounded per subsegment

    thumbnail/
      thumbnail.png

    guides/
      capcut_assembly_guide.md
      retention_checklist.md
```

### 3.2 Deterministic rerun invariant
Re-running v2 for the same inputs and toolchain must yield:
- **zero diffs** in all `v2/` artifacts, unless inputs changed or `--force` is used.

---

## 4) Pipeline architecture (v2 mainline)

### 4.1 Smart-agent vs dumb scripts (v2)
The original “Smart Agent + Dumb Scripts” architecture remains useful, but v2 narrows scope:
- v2 baseline must be **reliable, deterministic, auditable**
- anything that increases variance moves behind flags or upstream

### 4.2 V2 stage truth table

| Stage | Type | Input | Output |
|------:|------|-------|--------|
| V2-0 Init | Script | `inputs/*` | `v2/meta/provenance.json` (initial), folder creation |
| V2-1 Plan | Agent/Rules | `claim.json`, `data.json` (+optional `seed.md`) | `v2/meta/plan.json` (segments + subsegments + required assets + instructions) |
| V2-2 Visuals | Script | `v2/meta/plan.json` | `v2/subsegments/subseg-*.mp4` (10.0s each) |
| V2-3 Voice | Script | `v2/meta/plan.json` | `v2/voice/subseg-*.wav` |
| V2-4 Captions | Script | plan + aligned voice | `v2/captions/captions.srt` (bounded per subsegment) |
| V2-5 Charts | Script (Remotion) | chart specs from plan + data DSL | `v2/charts/chart-subseg-*.mp4` (10.0s each, alpha/green bg) |
| V2-6 Kit + Guides | Script | all prior outputs | `v2/guides/*.md`, `v2/thumbnail/thumbnail.png` |
| V2-7 Quality Gate | Script | all outputs | `v2/meta/quality_gate.json` |

> Ordering note: charts can render before/after voice; captions requires voice. In practice, V2-5 charts can run in parallel with V2-3 voice.

### 4.3 Where 3–2–1 is enforced in v2
Because CapCut assembly is manual, v2 enforces:
- The **presence of explicit instructions** (zooms, overlays, sound resets)
- Not the presence of keyframes in a final export

Quality Gate validates:
- 3 zoom instructions per segment
- 2 overlay instructions per subsegment (1 informational max, 1 emotional)
- 1 sound reset instruction at segment boundaries

---

## 5) Core schemas (v2 contracts)

### 5.1 `plan.json` (two-level model)
`v2/meta/plan.json` is the central contract.
It must encode:
- segments (story units)
- subsegments (10.0s production units)
- per-subsegment assets (visuals, charts, overlays)
- per-segment constraints and retention instructions
- chart specs referencing dataset + transform DSL

Minimal shape (illustrative):

```json
{
  "version": "2.0",
  "reel": {
    "reel_id": "2025-12-21-example",
    "subsegment_count": 5,
    "duration_seconds": 50
  },
  "segments": [
    {
      "segment_id": "seg-01",
      "subsegments": ["subseg-01"],
      "beat": "hook_claim",
      "zoom_plan": [{ "at_seconds": 1.5 }, { "at_seconds": 4.5 }, { "at_seconds": 7.5 }],
      "sound_reset": { "sfx_id": "tap_01", "at_seconds": 0.0 }
    }
  ],
  "subsegments": [
    {
      "subsegment_id": "subseg-01",
      "duration_seconds": 10.0,
      "voice": { "text": "..." },
      "visual": { "type": "still", "source": "generated|library", "prompt_ref": "..." },
      "overlays": [
        { "type": "informational", "ref": "chart-subseg-01" },
        { "type": "emotional", "ref": "emoji:money_mouth" }
      ],
      "charts": [
        { "chart_id": "chart-subseg-01", "dataset_id": "ds-01", "spec": { } }
      ]
    }
  ]
}
```

### 5.2 Chart spec (10s render contract)
Each chart usage in `plan.json` must resolve to exactly one 10.0s output file.
If a story beat needs 20s chart presence, it must have:
- `chart-subseg-02a` and `chart-subseg-02b` (two 10s outputs)

### 5.3 Strict audit transform DSL (canonical)
**Purpose:** deterministic derivation of chart values from CSV.

Allowed ops:
- `select_columns`
- `filter` (simple predicates)
- `groupby` + `aggregate` (`sum|mean|count`)
- `compute` (basic arithmetic expressions)
- `sort`
- `limit`

Example:

```json
{
  "dataset_id": "ds-01",
  "csv": {
    "path": "inputs/data/extracted_data.csv",
    "sha256": "…computed at runtime…"
  },
  "transform": [
    { "op": "select_columns", "columns": ["month", "revenue"] },
    { "op": "filter", "where": [{ "col": "month", "op": "!=", "value": "" }] },
    { "op": "groupby", "by": ["month"], "agg": [{ "col": "revenue", "fn": "sum", "as": "revenue_sum" }] },
    { "op": "sort", "by": [{ "col": "month", "dir": "asc" }] },
    { "op": "limit", "n": 6 }
  ],
  "output_hash": "…hash of derived table…"
}
```

Constraints:
- No arbitrary code execution
- No network I/O
- Expression support in `compute` is intentionally limited (basic arithmetic only)

---

## 6) Determinism & immutability rules (must-haves)

### 6.1 Deterministic reruns
Given the same:
- `inputs/claim.json`
- `inputs/data.json` (+ referenced CSVs)
- toolchain versions
- config flags

…the pipeline produces the same bytes (or at minimum, identical hashes) for all `v2/` outputs.

### 6.2 Immutability by default
- If an output exists, the stage must **not** overwrite it unless:
  - `--force` (stage-local override), or
  - `--fresh` (wipe v2 outputs and rerun)

### 6.3 Provenance always-on
`v2/meta/provenance.json` must include:
- input hashes (claim.json, data.json, referenced CSVs)
- tool versions (python package versions, node/remotion versions)
- flags used
- timestamps

---

## 7) CLI + flags (canonical interface)

### 7.1 Commands (proposal)
- `uv run arcanomy run <reel-path>` → v2 default
- `uv run arcanomy run <reel-path> --legacy` → v1 pipeline (frozen)

### 7.2 v2 flags (proposal)
- `--fresh`: remove `v2/` and regenerate
- `--force`: overwrite stage outputs (use sparingly)
- `--audit-level basic|strict`:
  - default from `claim.json.audit_level`
  - flag may override for debugging, but provenance must record override
- `--timing voice|heuristic`:
  - default `voice`
  - `heuristic` is non-canonical and should fail Quality Gate unless explicitly allowed

### 7.3 Deprecated / legacy flags
- `--legacy-final`: legacy-only automated assembly path
- `--legacy-chart-flex`: allow arbitrary chart duration (non-canonical)
- `--bg=generative`: (future) non-baseline mode with full provenance

---

## 8) Quality Gate (v2 acceptance criteria)

### 8.1 Gate output
`v2/meta/quality_gate.json`:
- `pass: true|false`
- `reasons[]`: failures and warnings
- `counters`: subsegments count, segments count, chart count, etc.

### 8.2 Gate rules (minimum)
Must pass:
- outputs present (all required files exist)
- every `subseg-*.mp4` is exactly 10.0s (validation tolerance: **± 1 frame** at the target FPS to avoid encoder edge-case false failures)
- every `voice/subseg-*.wav` exists and is aligned to 10.0s timeline
- captions.srt exists and does not cross subsegment boundaries
- retention instruction presence:
  - 3 zoom instructions per segment
  - overlays specified per subsegment (max 1 informational chart/image, 1 emotional)
  - sound reset instruction at each segment boundary
- strict audit mode requirements satisfied (when enabled)

---

## 9) Deprecations (explicit)

### 9.1 Deprecated in v2 mainline
- FFmpeg auto final assembly
- Remotion caption burn-in / karaoke pill subtitles
- Generative background video as baseline
- Unstructured “seed + yaml is the only input” as canonical

### 9.2 Legacy systems
- Kept runnable behind `--legacy`
- Frozen except critical bug fixes

---

## 10) Phased migration plan (how we refactor safely)

### Phase 0 — Sign-off (this RFC)
Deliverables:
- This RFC approved
- A small “truth table” doc update plan for `docs/00–08` to remove conflicts (tracked separately)

Exit criteria:
- engineering has explicit contracts to implement

### Phase 1 — Introduce v2 artifact model (no behavior change to v1)
Goals:
- Add v2 folder layout under reel
- Add provenance + immutability primitives
- Keep v1 untouched and runnable

Exit criteria:
- v2 runner can initialize a reel and produce `v2/meta/provenance.json` deterministically

### Phase 2 — Implement v2 planning contract (`plan.json`)
Goals:
- Build `plan.json` generator from `claim.json` + `data.json`
- Introduce segment/subsegment model + retention instruction encoding

Exit criteria:
- `plan.json` validates and is deterministic (hash stable)

### Phase 3 — Implement deterministic subsegment visuals (baseline)
Goals:
- Generate `subsegments/subseg-*.mp4` (10.0s) via deterministic methods:
  - still + Ken Burns (Remotion is NOT used; use a reliable compositor), OR
  - curated loops (local library) with deterministic selection rules

Exit criteria:
- 10.0s exact duration validation passes

### Phase 4 — Voice + alignment + captions
Goals:
- Generate `voice/subseg-*.wav`
- Align line-level captions to voice
- Produce boundary-safe `captions.srt`

Exit criteria:
- captions do not cross boundaries; timings derived from voice (not heuristics)

### Phase 5 — Charts-only Remotion integration (10.0s outputs)
Goals:
- Render chart MP4s per subsegment usage (10.0s each)
- Support alpha output; fallback to green screen
- Enforce strict audit DSL derivation

Exit criteria:
- chart outputs render deterministically from CSV + DSL

### Phase 6 — Kit + guides + quality gate
Goals:
- Generate CapCut guide and retention checklist from `plan.json`
- Run Quality Gate and emit `quality_gate.json`

Exit criteria:
- a reel produces the full kit with zero diffs on rerun

### Phase 7 — Legacy isolation
Goals:
- Ensure `--legacy` path remains runnable
- Freeze legacy features; document limitations

Exit criteria:
- v2 default is stable; v1 remains available

---

## 11) Open items (explicitly out-of-scope for v2 baseline)
- Automated CapCut project generation/macros
- Generative background video (Runway/Kling) in baseline
- Karaoke/word-level captions
- Multi-style caption variants


