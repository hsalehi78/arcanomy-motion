# Chart Examples — Copy-Paste Templates

Ready-to-use chart.json templates for common use cases. Copy and customize.

---

## Bar Chart — Comparison (Most Common)

**Use for:** Comparing "us vs them", before/after, age comparisons

```json
{
  "chartType": "bar",
  
  "dimensions": {
    "width": 1080,
    "height": 1080,
    "margin": { "top": 200, "right": 60, "bottom": 140, "left": 100 }
  },
  
  "background": { "color": "#00FF00" },
  
  "title": { "show": false },
  "subtitle": { "show": false },
  
  "xAxis": {
    "show": true,
    "label": {
      "font": { "family": "Inter", "size": 42, "weight": 500 },
      "color": "#FFFFFF"
    }
  },
  
  "yAxis": {
    "show": false,
    "gridLines": { "show": true, "color": "#333333" }
  },
  
  "bars": {
    "gap": 20,
    "cornerRadius": 8,
    "defaultColor": "#FFD700"
  },
  
  "dataLabels": {
    "show": true,
    "position": "above",
    "font": { "family": "Montserrat", "size": 48, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "animation": {
    "duration": 30,
    "style": "wave",
    "velocityMode": true,
    "staggerDelay": 10,
    "direction": "left-to-right"
  },
  
  "data": [
    { "label": "Age 25", "value": 1140000, "color": "#FFD700" },
    { "label": "Age 35", "value": 540000, "color": "#FF3B30" }
  ]
}
```

**Customization:**
- Change `data[].label` to your categories
- Change `data[].value` to your numbers
- Use `#FFD700` (gold) for the "good" option
- Use `#FF3B30` (red) for the "bad" option

---

## Bar Chart — Highlight Winner

**Use for:** Revealing the top performer, emphasizing one data point

```json
{
  "chartType": "bar",
  
  "dimensions": {
    "width": 1080,
    "height": 1080,
    "margin": { "top": 200, "right": 60, "bottom": 140, "left": 100 }
  },
  
  "background": { "color": "#00FF00" },
  
  "title": { "show": false },
  "subtitle": { "show": false },
  
  "xAxis": {
    "show": true,
    "label": {
      "font": { "family": "Inter", "size": 42, "weight": 500 },
      "color": "#FFFFFF"
    }
  },
  
  "yAxis": { "show": false, "gridLines": { "show": true, "color": "#333333" } },
  
  "bars": { "gap": 20, "cornerRadius": 8, "defaultColor": "#555555" },
  
  "dataLabels": {
    "show": true,
    "position": "above",
    "font": { "family": "Montserrat", "size": 42, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "animation": {
    "duration": 30,
    "style": "simultaneous",
    "velocityMode": true,
    "direction": "left-to-right"
  },
  
  "data": [
    { "label": "Option A", "value": 120 },
    { "label": "Option B", "value": 85 },
    { "label": "WINNER", "value": 280, "color": "#FFD700" },
    { "label": "Option D", "value": 150 }
  ]
}
```

**Customization:**
- Set `defaultColor` to gray (`#555555`)
- Only the winner gets a custom `color` in the data array

---

## Number Counter — Big Reveal

**Use for:** Dramatic single-number reveals like "$600,000" or "10 years"

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

**Customization:**
- `value`: The final number to display
- `prefix`: Text before ($ € £ # etc)
- `suffix`: Text after (K M % + etc)
- `number.color`: Red for loss/cost, Gold for gain/win
- `title.text`: What the number represents
- `subtitle.text`: Context or timeframe

---

## Horizontal Bar Chart — Leaderboard

**Use for:** Top 5 rankings, country comparisons, sorted lists

```json
{
  "chartType": "horizontalBar",
  
  "dimensions": {
    "width": 1080,
    "height": 1080,
    "margin": { "top": 120, "right": 100, "bottom": 60, "left": 200 }
  },
  
  "background": { "color": "#00FF00" },
  
  "title": { "show": false },
  
  "yAxis": {
    "show": true,
    "label": {
      "font": { "family": "Inter", "size": 36, "weight": 500 },
      "color": "#FFFFFF"
    }
  },
  
  "xAxis": { "show": false, "gridLines": { "show": true, "color": "#333333" } },
  
  "bars": { "height": 50, "gap": 15, "cornerRadius": 6 },
  
  "dataLabels": {
    "show": true,
    "position": "right",
    "font": { "family": "Montserrat", "size": 32, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "animation": {
    "duration": 30,
    "style": "staggered",
    "direction": "top-to-bottom"
  },
  
  "data": [
    { "label": "United States", "value": 28.78, "color": "#4ECDC4" },
    { "label": "China", "value": 18.53, "color": "#FF6B6B" },
    { "label": "Germany", "value": 4.59, "color": "#FFE66D" },
    { "label": "Japan", "value": 4.11, "color": "#C44DFF" },
    { "label": "India", "value": 3.94, "color": "#00D4FF" }
  ]
}
```

**Customization:**
- Each item can have a distinct color
- Data should be pre-sorted (highest first)
- Labels can be longer than vertical bars (up to 15 chars)

---

## Pie Chart — Composition

**Use for:** Market share, portfolio allocation, percentage breakdown

```json
{
  "chartType": "pie",
  
  "dimensions": { "width": 1080, "height": 1080 },
  "background": { "color": "#00FF00" },
  
  "title": { "show": false },
  
  "innerRadius": 0.5,
  
  "legend": {
    "show": true,
    "position": "bottom",
    "font": { "family": "Inter", "size": 32, "weight": 500 },
    "color": "#FFFFFF"
  },
  
  "dataLabels": {
    "show": true,
    "format": "percent",
    "font": { "family": "Montserrat", "size": 28, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "animation": {
    "duration": 30,
    "style": "simultaneous"
  },
  
  "data": [
    { "label": "Stocks", "value": 60, "color": "#FFD700" },
    { "label": "Bonds", "value": 25, "color": "#4ECDC4" },
    { "label": "Real Estate", "value": 10, "color": "#FF6B6B" },
    { "label": "Cash", "value": 5, "color": "#888888" }
  ]
}
```

**Customization:**
- `innerRadius`: 0 for full pie, 0.5 for donut
- Values are proportions (will be converted to percentages)
- Limit to 4-5 slices maximum

---

## Line Chart — Trend

**Use for:** Growth over time, progress, historical data

```json
{
  "chartType": "line",
  
  "dimensions": {
    "width": 1080,
    "height": 1080,
    "margin": { "top": 100, "right": 60, "bottom": 120, "left": 100 }
  },
  
  "background": { "color": "#00FF00" },
  
  "title": { "show": false },
  
  "xAxis": {
    "show": true,
    "label": {
      "font": { "family": "Inter", "size": 36, "weight": 500 },
      "color": "#888888"
    }
  },
  
  "yAxis": {
    "show": true,
    "gridLines": { "show": true, "color": "#333333" }
  },
  
  "line": {
    "color": "#FFD700",
    "strokeWidth": 4
  },
  
  "area": {
    "show": true,
    "opacity": 0.2
  },
  
  "dots": {
    "show": true,
    "radius": 6,
    "color": "#FFD700"
  },
  
  "animation": {
    "duration": 45
  },
  
  "data": [
    { "label": "2020", "y": 100 },
    { "label": "2021", "y": 125 },
    { "label": "2022", "y": 148 },
    { "label": "2023", "y": 195 },
    { "label": "2024", "y": 250 }
  ]
}
```

---

## Progress Chart — Single Metric

**Use for:** Completion percentage, satisfaction score, goal progress

```json
{
  "chartType": "progress",
  
  "dimensions": { "width": 1080, "height": 1080 },
  "background": { "color": "#00FF00" },
  
  "title": {
    "show": true,
    "text": "Customer Satisfaction",
    "position": "above",
    "font": { "family": "Inter", "size": 48, "weight": 500 },
    "color": "#FFFFFF"
  },
  
  "subtitle": {
    "show": true,
    "text": "Q4 2024 Survey Results",
    "font": { "family": "Inter", "size": 32, "weight": 400 },
    "color": "#888888"
  },
  
  "value": 87,
  "maxValue": 100,
  "format": "percent",
  
  "arc": {
    "color": "#FFD700",
    "backgroundColor": "#333333",
    "strokeWidth": 40
  },
  
  "valueDisplay": {
    "show": true,
    "font": { "family": "Montserrat", "size": 120, "weight": 700 },
    "color": "#FFFFFF"
  },
  
  "animation": {
    "duration": 45,
    "easing": "ease-out"
  }
}
```

---

## Quick Selection Guide

| Your Data | Use This Template |
|-----------|-------------------|
| Comparing 2-3 values (A vs B vs C) | Bar Chart — Comparison |
| Showing a winner among options | Bar Chart — Highlight Winner |
| Single dramatic number ($600K, 10 years) | Number Counter — Big Reveal |
| Top 5 ranking | Horizontal Bar — Leaderboard |
| Percentage breakdown (portfolio, market share) | Pie Chart — Composition |
| Growth over time | Line Chart — Trend |
| Single percentage (87% satisfaction) | Progress Chart — Single Metric |

---

## Common Customizations

### Changing Colors

```json
// Gold (winner, positive, YOUR option)
"color": "#FFD700"

// Red (loser, negative, danger)
"color": "#FF3B30"

// Gray (neutral, competitors, de-emphasized)
"color": "#888888"

// Green (growth, success)
"color": "#00FF88"
```

### Adjusting Animation Speed

```json
// Fast (dramatic, punchy)
"animation": { "duration": 20 }

// Normal (balanced)
"animation": { "duration": 30 }

// Slow (building tension)
"animation": { "duration": 45 }
```

### Hiding Title/Subtitle

```json
// When voiceover provides context, hide titles
"title": { "show": false },
"subtitle": { "show": false }
```
