# Chart Overlays (Remotion) — v2 Contract

## Rule

Charts are **overlays only**, not full-video compositions.

## Recommended templates (max 5)

- single-stat (number)
- comparison-bar
- range-bar
- timeline
- pie-simple

## Output spec (keep stable)

- 1080×1080
- 30 fps
- max 10 seconds window
- background green `#00FF00` (CapCut chroma key)
- file: `chart.mp4` (or `overlays/chart.mp4`)

## Reuse from existing system

If you keep the same Remotion project structure, you can reuse your existing `chart.json` contract and templates.

Current (existing) conventions worth keeping:
- CDN chart seed file: `chart.json` inside reel seed folder
- Remotion chart schema supports: bar, horizontalBar, stackedBar, pie, line, scatter, progress, number

## v2 change

Charts are created only if the beat sheet contains a `CHART_SLOT`.

