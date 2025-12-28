# Beat Sheet Timing Invariants (Sanity Check)

JSON Schema can validate *shapes*, but it cannot reliably enforce all timing invariants (ordering, non-overlap, cross-field comparisons).

Therefore v2 requires a deterministic sanity-check step before asset resolution.

## When it runs

Immediately after Phase 2 outputs `beat_sheet_v1.json`, before Phase 4 resolves assets.

## What it checks (must-pass)

- **Beat timing**
  - every beat has `t_end > t_start`
  - beats are ordered by `t_start`
  - beats do not overlap: `beat[i].t_end <= beat[i+1].t_start`
  - last `t_end` approximately matches `duration_seconds` (allow small epsilon, e.g., ±0.05s)

- **Event timing**
  - every event timestamp `t` is within `[0, duration_seconds]`
  - recommended: event timestamps are within their beat bounds (if you can attribute events to beats)

- **Slot sufficiency**
  - every beat has exactly one `visual_slot.type`
  - `CHART_SLOT` duration <= 12 seconds

## Output artifact (optional but recommended)

Write a machine-readable QC file:

- `05_qc/beat_sheet_qc.json`
  - `{ pass: boolean, errors: string[], warnings: string[] }`

If `pass=false`, abort the run and point to the first failing invariant.

