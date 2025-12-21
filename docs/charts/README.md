# Chart Templates for AI Agents

This folder contains JSON templates and documentation for rendering animated charts.

**Usage:** Copy a template, customize the data, and render with:
```bash
uv run chart path/to/your-chart.json
```

---

## Quick Reference

| File | Description | Use Case |
|------|-------------|----------|
| `bar-chart-basic.json` | Simple bar chart | Single metric comparison |
| `bar-chart-highlight.json` | Bar chart with one highlighted bar | Emphasize a winner/outlier |
| `bar-chart-comparison.json` | Side-by-side comparison | Before/after, us vs them |
| `bar-chart-timeline.json` | Time-based data | Monthly/quarterly trends |
| `bar-chart-negative.json` | Positive and negative values | Profit/loss, gains/drops |

---

## Template Structure

Every chart JSON follows this structure:

```json
{
  "chartType": "bar",
  "title": "Your Title Here",
  "animationDuration": 45,
  "data": [
    { "label": "Category", "value": 100 },
    { "label": "Another", "value": 150, "color": "#FF3B30" }
  ]
}
```

---

## Property Reference

### Root Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `chartType` | `"bar"` | Yes | — | Chart type (only "bar" supported currently) |
| `title` | string | No | `"Chart"` | Title displayed at top of chart |
| `animationDuration` | number | No | `45` | Frames for bar animation (30 frames = 1 second) |
| `data` | array | Yes | — | Array of data points to visualize |

### Data Point Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `label` | string | Yes | — | Category name shown below bar |
| `value` | number | Yes | — | Numeric value (determines bar height) |
| `color` | string | No | `#FFD700` | Hex color code for this bar |

---

## Animation Timing Guide

| Frames | Duration | Use Case |
|--------|----------|----------|
| `15` | 0.5 sec | Quick, punchy reveal |
| `30` | 1.0 sec | Standard pace |
| `45` | 1.5 sec | Default, good for 3-6 bars |
| `60` | 2.0 sec | Dramatic, slow build |
| `90` | 3.0 sec | Maximum impact, few bars |

**Rule of thumb:** More bars = shorter animation per bar feels better.

---

## Color Palette (Arcanomy Brand)

| Color | Hex | Use Case |
|-------|-----|----------|
| Gold (default) | `#FFD700` | Primary bars, highlights, winners |
| Bright Gold | `#FFB800` | Chart lines, secondary emphasis |
| Signal Red | `#FF3B30` | Danger, losses, negative values |
| Off-White | `#F5F5F5` | Neutral, baseline, "others" |
| Pure White | `#FFFFFF` | Maximum contrast accent |
| Muted Gray | `#888888` | De-emphasized, background data |

### Color Strategy

- **One highlight:** Make all bars gold, highlight one with red or white
- **Comparison:** Use gold for "us", muted gray for competitors
- **Positive/Negative:** Gold for gains, red for losses
- **Timeline:** All same color (gold) for consistency

---

## Output Specifications

All charts render to:
- **Resolution:** 1080 × 1920 (9:16 vertical/portrait)
- **Frame Rate:** 30 fps
- **Duration:** 3 seconds (90 frames)
- **Format:** MP4 (H.264)
- **Background:** Pure black (#000000)

---

## Agent Instructions

When generating chart JSON for a reel:

1. **Match the narrative:** Chart title should reinforce the voiceover point
2. **Limit data points:** 3-6 bars is ideal for mobile viewing
3. **Use round numbers:** 120, not 119.7 (easier to read)
4. **Highlight strategically:** Only 1 bar should be a different color
5. **Keep labels short:** 3-8 characters per label is ideal
6. **Consider reading order:** Bars are shown left-to-right

### Example Generation Flow

```
Voiceover: "May saw a 40% spike in revenue"
     ↓
Chart JSON:
{
  "title": "Monthly Revenue ($K)",
  "data": [
    { "label": "Apr", "value": 200 },
    { "label": "May", "value": 280, "color": "#FFD700" },  ← Highlighted
    { "label": "Jun", "value": 220 }
  ]
}
```

---

## File Naming Convention

When saving chart JSON in a reel folder:

```
content/reels/my-reel/inputs/data/
├── chart_revenue_monthly.json
├── chart_users_growth.json
└── chart_comparison_competitors.json
```

Pattern: `chart_[metric]_[dimension].json`

---

## See Also

- `docs/08-chart-components-plan.md` — Technical implementation details
- `remotion/src/components/charts/BarChart.tsx` — React component source
- `src/services/chart_renderer.py` — Python rendering service

