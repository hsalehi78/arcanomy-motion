# Chart Templates for AI Agents

This folder contains JSON templates and documentation for rendering animated charts.

**Usage:** Copy a template, customize the data, and render with:
```bash
uv run chart path/to/your-chart.json
```

---

## Available Chart Types

| Type | JSON File | Component | Best For |
|------|-----------|-----------|----------|
| **Bar Chart** | `bar-chart-*.json` | BarChart.tsx | Comparing categories, rankings, timelines |
| **Horizontal Bar Chart** | `horizontal-bar-chart-*.json` | HorizontalBarChart.tsx | Rankings, leaderboards, long labels |
| **Stacked Bar Chart** | `stacked-bar-chart-*.json` | StackedBarChart.tsx | Composition, multi-series comparison |
| **Pie Chart** | `pie-chart-*.json` | PieChart.tsx | Proportions, market share, composition |
| **Line Chart** | `line-chart-*.json` | LineChart.tsx | Trends over time, growth, progress |
| **Scatter Chart** | `scatter-chart-*.json` | ScatterChart.tsx | Correlation, distribution, relationships |
| **Progress Chart** | `progress-chart-*.json` | ProgressChart.tsx | Single percentage, completion, gauges |
| **Number Counter** | `number-counter-*.json` | NumberCounter.tsx | Big number reveal, animated counting |

---

## Bar Chart Templates

| File | Description | Use Case |
|------|-------------|----------|
| `bar-chart-basic.json` | Fully documented reference template | Start here for customization |
| `bar-chart-comparison.json` | Us vs competitors | Market share, feature comparison |
| `bar-chart-highlight.json` | One bar emphasized | Winner reveal, key insight |
| `bar-chart-minimal.json` | 2-3 bars only | Before/after, dramatic impact |
| `bar-chart-negative.json` | Gains and losses | Profit/loss, performance |
| `bar-chart-ranking.json` | Sorted by value | Top 5, leaderboards |
| `bar-chart-timeline.json` | Data over time | Monthly/quarterly metrics |

## Pie Chart Templates

| File | Description | Use Case |
|------|-------------|----------|
| `pie-chart-basic.json` | Donut chart with legend | Market share, budget breakdown |

## Line Chart Templates

| File | Description | Use Case |
|------|-------------|----------|
| `line-chart-basic.json` | Line with area fill | Growth trends, progress |

## Scatter Chart Templates

| File | Description | Use Case |
|------|-------------|----------|
| `scatter-chart-basic.json` | Scatter with trend line | Correlation, outliers |

## Horizontal Bar Chart Templates

| File | Description | Use Case |
|------|-------------|----------|
| `horizontal-bar-chart-basic.json` | Bars grow left to right | Top 5 lists, rankings, leaderboards |

## Stacked Bar Chart Templates

| File | Description | Use Case |
|------|-------------|----------|
| `stacked-bar-chart-basic.json` | Multi-series stacked bars | Quarterly by region, composition over time |

## Progress Chart Templates

| File | Description | Use Case |
|------|-------------|----------|
| `progress-chart-basic.json` | Circular progress gauge | Satisfaction %, completion rates, single metrics |

## Number Counter Templates

| File | Description | Use Case |
|------|-------------|----------|
| `number-counter-basic.json` | Animated counting number | Revenue reveal, big statistics, milestones |

---

## JSON Schema v2.0

All chart JSONs follow the **v2.0 comprehensive schema** with inline documentation:

```json
{
  "_meta": {
    "description": "What this template is for",
    "version": "2.0",
    "usage": "uv run chart path/to/file.json",
    "IMPORTANT_FOR_AGENTS": "All _*_desc fields are inline documentation"
  },

  "chartType": "bar",
  "_chartType_desc": "OPTIONS: 'bar', 'horizontalBar', 'stackedBar', 'pie', 'line', 'scatter', 'progress', 'number'",

  "dimensions": {
    "width": 1080,
    "height": 1080,
    "margin": { "top": 200, "right": 60, "bottom": 140, "left": 100 }
  },

  "background": {
    "color": "#0A0A0A",
    "_color_desc": "Use '#00FF00' for green screen transparency"
  },

  "title": {
    "show": true,
    "text": "Chart Title",
    "y": 60,
    "font": { "family": "Montserrat", "size": 56, "weight": 700 },
    "color": "#FFFFFF"
  },

  "animation": {
    "duration": 30,
    "style": "staggered",
    "velocityMode": true
  },

  "data": [
    { "label": "A", "value": 100 },
    { "label": "B", "value": 200, "color": "#FFD700" }
  ]
}
```

### Key Features

- **`_*_desc` fields**: Inline documentation explaining each setting
- **`show` toggles**: Enable/disable any element (title, subtitle, labels, etc.)
- **`font` objects**: Full control over family, size, weight
- **`color` properties**: Hex colors everywhere, supports transparency (#RRGGBBAA)
- **`animation` options**: Style, duration, velocityMode, staggerDelay, direction

---

## Animation Options

### Bar Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `style` | `"simultaneous"` | All bars animate together |
|         | `"staggered"` | Each bar waits for previous to finish |
|         | `"wave"` | Bars overlap, flowing effect |
| `velocityMode` | `true` | Taller bars take proportionally longer (dramatic!) |
|                | `false` | All bars same duration |
| `direction` | `"left-to-right"` | First to last |
|             | `"right-to-left"` | Last to first (reveal winner last) |
|             | `"center-out"` | Center bars first |
|             | `"random"` | Random order |
| `staggerDelay` | frames | Extra delay between bars |
| `duration` | frames | Base duration (30 = 1 sec at 30fps) |

### Pie Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `style` | `"simultaneous"` | All slices grow together |
|         | `"sequential"` | One slice at a time |
| `staggerDelay` | frames | Delay between slices |

### Line Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `duration` | frames | Time to draw the complete line |

### Scatter Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `style` | `"simultaneous"` | All points appear together |
|         | `"sequential"` | Points appear left to right |
|         | `"random"` | Points appear randomly |
| `staggerDelay` | frames | Delay between points |

### Horizontal Bar Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `style` | `"simultaneous"` | All bars grow together |
|         | `"staggered"` | Each bar waits for previous to finish |
|         | `"wave"` | Bars overlap, flowing effect |
| `velocityMode` | `true` | Longer bars take proportionally longer |
| `direction` | `"top-to-bottom"` | First bar animates first |
|             | `"bottom-to-top"` | Last bar animates first |
| `staggerDelay` | frames | Extra delay between bars |

### Stacked Bar Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `style` | `"simultaneous"` | All categories animate together |
|         | `"staggered"` | Categories animate one by one |
| `staggerDelay` | frames | Delay between categories |

### Progress Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `duration` | frames | Time to fill the arc |
| `easing` | `"linear"` | Constant speed |
|          | `"ease-out"` | Fast start, slow finish (satisfying!) |

### Number Counter Animation

| Property | Options | Description |
|----------|---------|-------------|
| `duration` | frames | Time to count from start to target |
| `delay` | frames | Wait before starting (dramatic pause) |
| `easing` | `"linear"` | Constant counting speed |
|          | `"ease-out"` | Fast start, slows at end (most satisfying) |
|          | `"ease-in-out"` | Slow start and end, fast middle |

---

## Color Palette (Arcanomy Brand)

| Color | Hex | Use Case |
|-------|-----|----------|
| **Gold** | `#FFD700` | Primary, highlights, winners, YOUR data |
| **Chart Line** | `#FFB800` | Lines, secondary emphasis |
| **Signal Red** | `#FF3B30` | Danger, losses, negative, problems |
| **Bright Green** | `#00FF88` | Growth, positive, success |
| **Blue** | `#007AFF` | Trust, neutral highlight |
| **Muted Gray** | `#888888` | De-emphasized, competitors, "others" |
| **Dark Gray** | `#555555` | Very de-emphasized |
| **Pure White** | `#FFFFFF` | Maximum contrast, labels |
| **Near Black** | `#0A0A0A` | Background |

### Color Strategy by Chart Type

- **Comparison:** Gold for "Us", gray for competitors
- **Highlight:** Gold for winner, muted for others
- **Positive/Negative:** Gold/green for gains, red for losses
- **Timeline:** All same color for visual continuity

---

## Green Screen for Transparency

MP4 doesn't support true transparency. For overlay effects in CapCut/editors:

1. Set `background.color` to `"#00FF00"` (bright green)
2. Render the chart
3. In CapCut: Apply **Chroma Key** effect
4. Tap the green area to remove it

```json
"background": {
  "color": "#00FF00",
  "_color_desc": "Green screen - use Chroma Key in editor to remove"
}
```

---

## Fonts

Charts use **Google Fonts** (loaded automatically):

| Font | Use | Weights |
|------|-----|---------|
| **Montserrat** | Titles, data labels, bold text | 400, 500, 700 |
| **Inter** | Subtitles, axis labels, body text | 400, 500, 700 |

All font settings are customizable per-element:

```json
"font": {
  "family": "Montserrat",
  "size": 56,
  "weight": 700
}
```

---

## Output Specifications

| Property | Value |
|----------|-------|
| **Default Resolution** | 1080 × 1080 (1:1 square) |
| **Frame Rate** | 30 fps |
| **Format** | MP4 (H.264) |
| **Duration** | Calculated from animation settings |

All dimensions are customizable via `dimensions.width` and `dimensions.height`.

---

## Agent Instructions

When generating chart JSON for a reel:

1. **Start from a template:** Copy the closest template and modify
2. **Read `_*_desc` fields:** They explain what each setting does
3. **Match the narrative:** Chart title should reinforce the voiceover
4. **Limit data points:** 3-6 items ideal for mobile viewing
5. **Use round numbers:** 120, not 119.7 (easier to read)
6. **Highlight strategically:** Only 1-2 items should have distinct colors
7. **Keep labels short:** 3-8 characters per label is ideal
8. **Test animation:** `velocityMode: true` with `style: "simultaneous"` creates drama

### Example: Creating a Chart for Voice-over

```
Voiceover: "Our product dominates with 35% market share"
     ↓
Template: bar-chart-comparison.json
     ↓
Customize:
- title.text = "Market Share 2024"
- data[0] = { label: "Us", value: 35, color: "#FFD700" }  ← Gold = winner
- data[1-4] = competitors with default gray
```

---

## File Reference

| File | Purpose |
|------|---------|
| **JSON Templates** | `docs/charts/*.json` - Copy and customize |
| **Components** | `remotion/src/components/charts/*.tsx` - React source |
| **Renderer** | `src/services/chart_renderer.py` - Python CLI |
| **Constants** | `remotion/src/lib/constants.ts` - Brand colors |

---

## See Also

- `remotion/src/components/charts/` — All chart component source code
- `docs/_archive/08-chart-components-plan.md` — Technical implementation details (legacy)
- `docs/_archive/05-visual-style-and-subtitles.md` — Brand visual guidelines (legacy)
