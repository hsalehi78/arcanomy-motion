# 08 — Chart Components Plan

## Overview

This document outlines the plan for building reusable, animated chart components for Remotion. These charts will be developed as standalone compositions first, then integrated into the main video pipeline later.

---

## Goals

1. **Standalone Development** — Build and preview charts independently using Remotion Studio
2. **Consistent Design** — Follow the Arcanomy visual identity (black/gold/white palette)
3. **Animated** — All charts have draw-on animations (0.5–1.5s duration)
4. **Reusable** — Components accept props for data, colors, and animation timing
5. **Integration-Ready** — Easy to embed in `MainReel` segments later

---

## Phase 1: Bar Chart (This Sprint)

### Component: `BarChart.tsx`

A vertical bar chart with animated bars that grow from the bottom.

#### Props Interface

```typescript
interface BarData {
  label: string;      // Category name (x-axis)
  value: number;      // Numeric value (y-axis)
  color?: string;     // Optional override color per bar
}

interface BarChartProps {
  data: BarData[];              // Required: array of data points
  width?: number;               // Default: 800
  height?: number;              // Default: 500
  colors?: typeof COLORS;       // Default: Arcanomy palette
  animationDuration?: number;   // Default: 30 frames (1s)
  barGap?: number;              // Default: 20px gap between bars
  showLabels?: boolean;         // Default: true (category labels)
  showValues?: boolean;         // Default: true (value labels on bars)
  title?: string;               // Optional chart title
}
```

#### Animation Behavior

| Element | Animation | Timing |
|---------|-----------|--------|
| Bars | Grow from bottom (0 → full height) | 0 → `animationDuration` frames |
| Value labels | Fade in after bars complete | After `animationDuration` |
| Category labels | Fade in with bars | 0 → `animationDuration` frames |
| Grid lines | Static (no animation) | Visible from frame 0 |

#### Visual Specifications

| Element | Style |
|---------|-------|
| Background | `#000000` (pure black) |
| Bars | `#FFD700` (gold) — can override per bar |
| Grid lines | `#0A0A0A` (near black) @ 50% opacity |
| Value text | `#F5F5F5` (off-white), 16px, bold |
| Label text | `#F5F5F5` (off-white), 14px, regular |
| Bar corners | 4px border radius |

---

## File Structure

```
remotion/src/
├── components/
│   └── charts/
│       ├── LineChart.tsx      # Existing
│       ├── BarChart.tsx       # NEW — Phase 1
│       ├── PieChart.tsx       # Phase 2 (future)
│       ├── AreaChart.tsx      # Phase 3 (future)
│       └── index.ts           # NEW — Barrel export
│
├── compositions/
│   ├── MainReel.tsx           # Existing
│   ├── CaptionBurn.tsx        # Existing
│   ├── Shorts.tsx             # Existing
│   └── BarChartDemo.tsx       # NEW — Standalone demo
│
└── Root.tsx                   # EDIT — Add BarChartDemo composition
```

---

## Demo Composition: `BarChartDemo`

A full-screen composition for previewing the bar chart in Remotion Studio.

#### Props

```typescript
interface BarChartDemoProps {
  data: BarData[];
  title?: string;
  animationDuration?: number;
}
```

#### Default Test Data

```typescript
defaultProps: {
  title: "Monthly Revenue ($K)",
  animationDuration: 45,  // 1.5s
  data: [
    { label: "Jan", value: 120 },
    { label: "Feb", value: 85 },
    { label: "Mar", value: 200 },
    { label: "Apr", value: 150 },
    { label: "May", value: 280, color: "#FFD700" },  // Highlighted
    { label: "Jun", value: 190 },
  ],
}
```

#### Composition Settings

| Setting | Value |
|---------|-------|
| ID | `BarChartDemo` |
| Width | 1080 |
| Height | 1920 |
| FPS | 30 |
| Duration | 90 frames (3 seconds) |

---

## Implementation Checklist

### Files to Create

- [x] `remotion/src/components/charts/BarChart.tsx` ✅
- [x] `remotion/src/components/charts/index.ts` ✅
- [x] `remotion/src/compositions/BarChartDemo.tsx` ✅

### Files to Modify

- [x] `remotion/src/Root.tsx` — Add import and Composition ✅

### Testing

- [ ] Run `pnpm start` in `remotion/` folder
- [ ] Select "BarChartDemo" composition
- [ ] Verify bar animation plays correctly
- [ ] Test with different data sets via props panel
- [ ] Render test: `pnpm exec remotion render BarChartDemo out/bar-chart-test.mp4`

---

## Python Integration (Implemented)

Charts can be rendered from Python using the `ChartRenderer` service.

### Service: `src/services/chart_renderer.py`

```python
from src.services import render_chart_from_json, BarChartProps

# Render from JSON file
render_chart_from_json("path/to/chart.json")

# Render with Python dict
render_bar_chart({
    "title": "Revenue",
    "data": [{"label": "Q1", "value": 100}]
}, output_path="out/chart.mp4")
```

### CLI Command

```bash
# Render a chart from JSON
uv run arcanomy render-chart path/to/chart.json

# With custom output
uv run arcanomy render-chart chart.json -o output/my-chart.mp4

# Shorthand
uv run chart chart.json
```

### JSON Template

Templates and examples available in `docs/charts/`:

```json
{
  "chartType": "bar",
  "title": "Monthly Revenue ($K)",
  "animationDuration": 45,
  "data": [
    { "label": "Jan", "value": 120 },
    { "label": "Feb", "value": 85 },
    { "label": "Mar", "value": 200, "color": "#FFD700" }
  ]
}
```

---

## Future Phases

### Phase 2: Pie Chart

- Animated slice reveal (clockwise draw)
- Optional center label (donut style)
- Legend with color swatches

### Phase 3: Area Chart

- Line chart variant with filled area below
- Gradient fill from line color to transparent
- Same animation as LineChart (draw-on)

### Phase 4: Full Integration

- Add chart segment type to `MainReel`
- Define manifest schema for chart data
- Charts rendered inline during video assembly

---

## Design Decisions

### Why SVG?

- Crisp at any resolution
- Easy to animate with Remotion's `interpolate()`
- No external dependencies

### Why Default to 30-frame Animation?

- 1 second @ 30fps is the standard from `ANIMATION.chartDrawDuration`
- Long enough to be visible, short enough to maintain pacing
- Can be overridden per-chart

### Why No Axis Lines?

- Minimal design matches Arcanomy's clean aesthetic
- Grid lines provide enough reference
- Can be added as optional prop later if needed

---

## Open Questions

1. **Horizontal bars?** — Should we support horizontal orientation as a variant?
2. **Stacked bars?** — Multiple values per category (grouped or stacked)?
3. **Negative values?** — Bars that go below zero?
4. **Data source?** — Accept CSV path or always pre-parsed data?

---

## Approval

- [x] Plan reviewed and approved ✅
- [x] Phase 1 implemented ✅

---

*Last updated: December 20, 2024*

