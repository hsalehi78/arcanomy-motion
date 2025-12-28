# Migration Notes: v1 → v2

## What to reuse

- **R2/CDN conventions** for seeds and indexes (if still valid)
- **Remotion charts-only approach** + existing chart schema/templates
- **CapCut doctrine** (track layout, 3–2–1 rule, preset-driven captions)

## What to stop doing

- Generating assets before the beat sheet is asset-complete
- Any pipeline stage that produces videos that are not actually used in assembly

## Recommended migration path

1. Build v2 as a separate repo (or `/apps/v2/` if you insist on mono-repo).
2. Implement only MVP outputs from `docs_v2/README.md`.
3. Run v2 for 10 straight reels.
4. Only then consider deleting v1.

## Reality check

If your existing codebase is tightly coupled to the old stage chain, v2 will ship faster as a rebuild.

