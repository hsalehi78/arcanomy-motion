# Chart JSON Schema Reference

Complete schema documentation for generating `chart.json` files.

---

## Overview

Charts are rendered by **Remotion** (a React-based video engine) and output as 10-second MP4 files with green-screen backgrounds for compositing in CapCut.

### Supported Chart Types

| chartType | Remotion Component | Best For |
|-----------|-------------------|----------|
| `bar` | BarChartDemo | Comparing 2-5 values, rankings |
| `horizontalBar` | HorizontalBarChartDemo | Leaderboards, ranking lists |
| `stackedBar` | StackedBarChartDemo | Multi-series composition |
| `pie` | PieChartDemo | Proportions, market share |
| `line` | LineChartDemo | Trends over time |
| `scatter` | ScatterChartDemo | Correlation, distribution |
| `progress` | ProgressChartDemo | Single percentage/gauge |
| `number` | NumberCounterDemo | Big number reveals, milestones |

---

## Universal Properties

All chart types share these top-level properties:

```json
{
  "chartType": "bar | horizontalBar | stackedBar | pie | line | scatter | progress | number",
  
  "dimensions": {
    "width": 1080,
    "height": 1080,
    "margin": { "top": 200, "right": 60, "bottom": 140, "left": 100 }
  },
  
  "background": {
    "color": "#00FF00"
  },
  
  "title": {
    "show": true,
    "text": "Chart Title",
    "y": 60,
    "font": { "family": "Montserrat", "size": 64, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "subtitle": {
    "show": false,
    "text": "Subtitle text",
    "y": 130,
    "font": { "family": "Inter", "size": 48, "weight": 400 },
    "color": "#888888"
  }
}
```

### Background Color

| Color | Hex | Purpose |
|-------|-----|---------|
| **Green Screen** | `#00FF00` | **RECOMMENDED** - Use chroma key in CapCut to make transparent |
| Black | `#0A0A0A` | Solid dark background |
| Transparent | `transparent` | Only works with ProRes codec (not MP4) |

**Always use `#00FF00`** for green screen unless you have a specific reason not to.

### Fonts

| Font | Use For | Weights |
|------|---------|---------|
| `Montserrat` | Titles, data labels, bold emphasis | 400, 500, 700 |
| `Inter` | Subtitles, axis labels, body text | 400, 500, 700 |

---

## Bar Chart Schema

```json
{
  "chartType": "bar",
  
  "dimensions": {
    "width": 1080,
    "height": 1080,
    "margin": { "top": 280, "right": 60, "bottom": 140, "left": 120 }
  },
  
  "background": { "color": "#00FF00" },
  
  "title": {
    "show": false,
    "text": "Chart Title",
    "y": 60,
    "font": { "family": "Montserrat", "size": 64, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "subtitle": {
    "show": false,
    "text": "Subtitle",
    "y": 130,
    "font": { "family": "Inter", "size": 48, "weight": 400 },
    "color": "#888888"
  },
  
  "xAxis": {
    "show": true,
    "label": {
      "font": { "family": "Inter", "size": 42, "weight": 500 },
      "color": "#FFFFFF"
    }
  },
  
  "yAxis": {
    "show": false,
    "label": {
      "font": { "family": "Inter", "size": 42, "weight": 500 },
      "color": "#888888"
    },
    "gridLines": {
      "show": true,
      "color": "#333333"
    }
  },
  
  "bars": {
    "gap": 20,
    "cornerRadius": 8,
    "defaultColor": "#FFD700"
  },
  
  "dataLabels": {
    "show": true,
    "position": "inside-top",
    "font": { "family": "Montserrat", "size": 48, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "animation": {
    "duration": 30,
    "style": "simultaneous",
    "velocityMode": true,
    "staggerDelay": 15,
    "direction": "left-to-right"
  },
  
  "data": [
    { "label": "Age 25", "value": 1140000, "color": "#FFD700" },
    { "label": "Age 35", "value": 540000, "color": "#FF3B30" }
  ]
}
```

### Bar Chart Data Format

```json
{
  "data": [
    { "label": "Label1", "value": 100 },
    { "label": "Label2", "value": 200, "color": "#FF3B30" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | ✅ | Text below bar (max 10 chars) |
| `value` | number | ✅ | Bar height value |
| `color` | string | ❌ | Override bar color (hex) |

### Data Label Positions

| Position | Description |
|----------|-------------|
| `above` | Outside, above the bar |
| `inside-top` | Inside bar, near top |
| `inside-middle` | Center of bar |
| `inside-bottom` | Inside bar, near bottom |

---

## Animation Options

### Bar Chart Animation

| Property | Options | Description |
|----------|---------|-------------|
| `style` | `simultaneous` | All bars animate together |
| | `staggered` | Each bar waits for previous to finish |
| | `wave` | Bars overlap with flowing effect |
| `velocityMode` | `true` | Taller bars take longer (dramatic) |
| | `false` | All bars same duration |
| `direction` | `left-to-right` | First to last |
| | `right-to-left` | Last to first |
| | `center-out` | Center bars first |
| | `random` | Random order |
| `staggerDelay` | number | Frames between bar starts |
| `duration` | number | Base duration in frames (30 = 1 sec) |

### Recommended Animation Settings

For maximum drama:
```json
{
  "animation": {
    "duration": 30,
    "style": "simultaneous",
    "velocityMode": true
  }
}
```

For staggered reveal:
```json
{
  "animation": {
    "duration": 30,
    "style": "wave",
    "staggerDelay": 10,
    "direction": "left-to-right"
  }
}
```

---

## Number Counter Schema

For big number reveals (e.g., "$600,000"):

```json
{
  "chartType": "number",
  
  "value": 600000,
  "startValue": 0,
  "prefix": "$",
  "suffix": "",
  "decimals": 0,
  "useLocale": true,
  
  "dimensions": { "width": 1080, "height": 1080 },
  "background": { "color": "#00FF00" },
  
  "title": {
    "show": true,
    "text": "Cost of Waiting",
    "position": "above",
    "font": { "family": "Inter, sans-serif", "size": 48, "weight": 500 },
    "color": "#FFFFFF"
  },
  
  "subtitle": {
    "show": true,
    "text": "10 years of delay",
    "font": { "family": "Inter, sans-serif", "size": 36, "weight": 400 },
    "color": "#888888"
  },
  
  "number": {
    "font": { "family": "Montserrat, sans-serif", "size": 160, "weight": 700 },
    "color": "#FF3B30"
  },
  
  "animation": {
    "duration": 60,
    "easing": "ease-out",
    "delay": 15
  }
}
```

### Number Counter Fields

| Field | Type | Description |
|-------|------|-------------|
| `value` | number | Target value to count to |
| `startValue` | number | Starting value (usually 0) |
| `prefix` | string | Text before number ($, €, #) |
| `suffix` | string | Text after number (K, M, %) |
| `decimals` | number | Decimal places to show |
| `useLocale` | boolean | Format with commas (1,250,000) |

### Easing Options

| Easing | Description |
|--------|-------------|
| `linear` | Constant speed |
| `ease-out` | Fast start, slow finish (most satisfying) |
| `ease-in-out` | Slow start and end, fast middle |

---

## Color Palette (Arcanomy Brand)

| Color | Hex | Use Case |
|-------|-----|----------|
| **Gold** | `#FFD700` | Primary, highlights, winners, YOUR data |
| **Chart Line** | `#FFB800` | Lines, secondary emphasis |
| **Signal Red** | `#FF3B30` | Danger, losses, negative, problems |
| **Bright Green** | `#00FF88` | Growth, positive, success |
| **Blue** | `#007AFF` | Trust, neutral highlight |
| **Muted Gray** | `#888888` | De-emphasized, competitors |
| **Dark Gray** | `#555555` | Very de-emphasized |
| **Pure White** | `#FFFFFF` | Maximum contrast, labels |
| **Near Black** | `#0A0A0A` | Backgrounds |
| **Green Screen** | `#00FF00` | Transparency for compositing |

### Color Strategy by Use Case

| Scenario | Highlighted Color | Other Color |
|----------|-------------------|-------------|
| Us vs Competitors | Gold for "Us" | Gray for others |
| Winner reveal | Gold for winner | Muted for losers |
| Good vs Bad | Gold/Green for good | Red for bad |
| Timeline | Same color throughout | — |
| Cost/Loss emphasis | Red for loss | — |

---

## Other Chart Types

### Pie Chart

```json
{
  "chartType": "pie",
  "innerRadius": 0.5,
  "data": [
    { "label": "Stocks", "value": 60, "color": "#FFD700" },
    { "label": "Bonds", "value": 30, "color": "#888888" },
    { "label": "Cash", "value": 10, "color": "#555555" }
  ],
  "animation": { "duration": 30, "style": "simultaneous" }
}
```

### Line Chart

```json
{
  "chartType": "line",
  "data": [
    { "label": "2020", "y": 100 },
    { "label": "2021", "y": 120 },
    { "label": "2022", "y": 145 },
    { "label": "2023", "y": 180 }
  ],
  "line": { "color": "#FFD700", "strokeWidth": 4 },
  "area": { "show": true, "opacity": 0.2 },
  "animation": { "duration": 45 }
}
```

### Horizontal Bar Chart

```json
{
  "chartType": "horizontalBar",
  "data": [
    { "label": "United States", "value": 28.78, "color": "#4ECDC4" },
    { "label": "China", "value": 18.53, "color": "#FF6B6B" },
    { "label": "Germany", "value": 4.59, "color": "#FFE66D" }
  ],
  "animation": { "duration": 30, "style": "staggered", "direction": "top-to-bottom" }
}
```

### Progress Chart

```json
{
  "chartType": "progress",
  "value": 85,
  "maxValue": 100,
  "format": "percent",
  "arc": { "color": "#FFD700", "backgroundColor": "#333333" },
  "animation": { "duration": 45, "easing": "ease-out" }
}
```

---

## Output Specifications

All rendered charts will have:

| Property | Value |
|----------|-------|
| Resolution | 1080 × 1080 (1:1 square) |
| Frame Rate | 30 fps |
| Duration | 10.0 seconds (300 frames) |
| Format | MP4 (H.264) |
| Background | Green (#00FF00) for chroma key |

---

## Validation Checklist

Before generating chart.json:

- [ ] `chartType` is one of the valid types
- [ ] `data` array has 2-6 items (mobile readability)
- [ ] Labels are SHORT (max 10 characters)
- [ ] Values are round numbers where possible (120, not 119.7)
- [ ] Colors use brand palette
- [ ] Only 1-2 items have highlight colors
- [ ] Background is `#00FF00` for green screen
- [ ] Animation duration is 30 frames (1 second base)
