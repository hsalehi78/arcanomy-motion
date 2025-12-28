# Observability + Provenance (v2)

This app must be debuggable on day 3, not just day 1.

## Required provenance file

Write `99_provenance/provenance.json` with:

- `run_id`
- timestamps per phase
- hashes of immutable inputs:
  - blog.json hash
  - ledger snapshot query params (not full data)
  - b-roll index hash
  - music index hash
- model/provider versions (if LLM used)
- render tool versions (ffmpeg, remotion)

## Logs

Write `99_provenance/logs.txt` (append-only) with:

- gate failures (dedupe, verification, resolver exhaustion)
- selected clip IDs + scores
- any fallback usage

## Why this matters

When the system “fails,” you want to know:
- was it a schema violation?
- a library shortage?
- a dedupe gate too strict?
- an ingestion/anchor mismatch?

