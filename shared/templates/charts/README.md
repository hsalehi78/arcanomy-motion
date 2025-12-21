# Chart Templates

This folder contains JSON templates for rendering charts with Remotion.

## Usage

1. Copy a template to your reel's `inputs/data/` folder
2. Edit the values to match your data
3. Render with: `uv run chart <path-to-json>`

## Available Templates

### `bar_chart_template.json`

Vertical bar chart with animated bars growing from bottom.

```json
{
  "chartType": "bar",
  "title": "Your Chart Title",
  "animationDuration": 45,
  "data": [
    { "label": "Category", "value": 100 },
    { "label": "Another", "value": 150, "color": "#FF3B30" }
  ]
}
```

## Props Reference

### Bar Chart

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `chartType` | `"bar"` | Required | Chart type identifier |
| `title` | `string` | `"Chart"` | Title displayed at top |
| `animationDuration` | `number` | `45` | Animation frames (30 = 1 second) |
| `data` | `array` | Required | Array of data points |

### Data Point

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `label` | `string` | Yes | Category label (shown below bar) |
| `value` | `number` | Yes | Numeric value (determines bar height) |
| `color` | `string` | No | Hex color override (default: `#FFD700` gold) |

## Examples

### Quarterly Revenue
```json
{
  "chartType": "bar",
  "title": "2024 Quarterly Revenue",
  "animationDuration": 60,
  "data": [
    { "label": "Q1", "value": 1200 },
    { "label": "Q2", "value": 1850 },
    { "label": "Q3", "value": 1620 },
    { "label": "Q4", "value": 2100, "color": "#00FF00" }
  ]
}
```

### Comparison (highlight one)
```json
{
  "chartType": "bar",
  "title": "Competitor Analysis",
  "animationDuration": 45,
  "data": [
    { "label": "Us", "value": 95, "color": "#FFD700" },
    { "label": "Competitor A", "value": 72 },
    { "label": "Competitor B", "value": 68 },
    { "label": "Competitor C", "value": 45 }
  ]
}
```

## Output

Charts are rendered as MP4 videos at 1080x1920 (9:16 vertical) at 30fps.

Default output location: Same folder as JSON file, with `.mp4` extension.

