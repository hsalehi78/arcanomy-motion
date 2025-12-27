# Remotion Setup Guide

How to install and configure Remotion for chart rendering.

---

## Overview

**Remotion** is a React-based video engine that renders animated charts to MP4. Arcanomy Motion uses Remotion to generate chart videos from `chart.json` configuration files.

### Architecture

```
chart.json → Python CLI → Remotion (Node.js) → MP4 video
                 ↓
         npx remotion render
```

---

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | 18+ | Runs Remotion |
| pnpm | 9+ | Package manager |
| Python | 3.10+ | Orchestration CLI |
| FFmpeg | Latest | Video encoding |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/arcanomy/arcanomy-motion.git
cd arcanomy-motion
```

### 2. Install Python Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Install Remotion Dependencies

```bash
cd remotion
pnpm install
cd ..
```

### 4. Verify Installation

```bash
# Test chart rendering
uv run arcanomy render-chart docs/charts/bar-chart-basic.json

# Should output: docs/charts/bar-chart-basic.mp4
```

---

## Project Structure

```
arcanomy-motion/
├── remotion/                    # Remotion project
│   ├── package.json             # Node dependencies
│   ├── remotion.config.ts       # Remotion configuration
│   ├── src/
│   │   ├── Root.tsx             # Composition registry
│   │   ├── components/
│   │   │   └── charts/          # Chart components
│   │   │       ├── BarChart.tsx
│   │   │       ├── HorizontalBarChart.tsx
│   │   │       ├── LineChart.tsx
│   │   │       ├── PieChart.tsx
│   │   │       ├── ProgressChart.tsx
│   │   │       ├── ScatterChart.tsx
│   │   │       ├── StackedBarChart.tsx
│   │   │       └── NumberCounter.tsx
│   │   └── compositions/        # Composition wrappers
│   │       ├── BarChartDemo.tsx
│   │       ├── NumberCounterDemo.tsx
│   │       └── ...
│   └── out/                     # Rendered outputs
│
├── src/
│   └── services/
│       ├── chart_renderer.py    # Python chart rendering service
│       └── remotion_cli.py      # Remotion CLI wrapper
│
└── docs/
    └── charts/                  # Chart templates and examples
        ├── README.md
        ├── bar-chart-basic.json
        ├── bar-chart-basic.mp4
        └── ...
```

---

## How Rendering Works

### 1. JSON to Props

The Python CLI reads `chart.json` and:
- Strips all `_*` comment fields (like `_desc`, `_options`)
- Extracts `chartType` to determine which Remotion composition to use
- Passes remaining props to Remotion

### 2. Chart Type Mapping

| chartType in JSON | Remotion Composition ID |
|-------------------|------------------------|
| `bar` | `BarChartDemo` |
| `horizontalBar` | `HorizontalBarChartDemo` |
| `stackedBar` | `StackedBarChartDemo` |
| `pie` | `PieChartDemo` |
| `line` | `LineChartDemo` |
| `scatter` | `ScatterChartDemo` |
| `progress` | `ProgressChartDemo` |
| `number` | `NumberCounterDemo` |

### 3. Duration Calculation

Each composition has a `calculateMetadata` function that computes duration based on animation settings:

```typescript
// Example: Bar chart duration calculation
const calcBarChartDemoMetadata = ({ props }) => {
  const animDuration = props.animation?.duration ?? 45;
  const animStyle = props.animation?.style ?? "simultaneous";
  const dataLength = props.data?.length ?? 4;
  
  let totalAnimDuration = animDuration;
  if (animStyle === "staggered") {
    totalAnimDuration = animDuration * dataLength;
  }
  
  // Add 30 frames hold at end
  const durationInFrames = Math.ceil(totalAnimDuration + 30);
  
  return { durationInFrames, fps: 30, width: 1080, height: 1080, props };
};
```

### 4. Render Command

The CLI executes:

```bash
cd remotion && npx remotion render \
  BarChartDemo \
  output.mp4 \
  --props='{"data":[...],"animation":{...}}'
```

---

## Development Commands

### Preview Mode (Interactive)

```bash
cd remotion
pnpm start
# Opens Remotion Studio at http://localhost:3000
```

### Render Single Chart

```bash
# From project root
uv run arcanomy render-chart path/to/chart.json

# Or with custom output path
uv run arcanomy render-chart chart.json -o output/my-chart.mp4
```

### Render with Frame Range

```bash
# Render only frames 0-299 (exactly 10 seconds)
uv run arcanomy render-chart chart.json --frames 0-299
```

---

## Adding a New Chart Type

To add a new chart type to Remotion:

### 1. Create the Component

```typescript
// remotion/src/components/charts/MyNewChart.tsx
import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

export interface MyNewChartProps {
  data: Array<{ label: string; value: number }>;
  animation?: { duration?: number };
}

export const MyNewChart: React.FC<MyNewChartProps> = ({ data, animation }) => {
  const frame = useCurrentFrame();
  const duration = animation?.duration ?? 30;
  
  const progress = interpolate(frame, [0, duration], [0, 1], {
    extrapolateRight: "clamp",
  });
  
  return (
    <div style={{ background: "#00FF00", width: "100%", height: "100%" }}>
      {/* Your chart rendering logic */}
    </div>
  );
};
```

### 2. Create the Composition Wrapper

```typescript
// remotion/src/compositions/MyNewChartDemo.tsx
import React from "react";
import { MyNewChart, MyNewChartProps } from "../components/charts/MyNewChart";

export type MyNewChartDemoProps = MyNewChartProps;

export const MyNewChartDemo: React.FC<MyNewChartDemoProps> = (props) => {
  return <MyNewChart {...props} />;
};
```

### 3. Add calculateMetadata Function

```typescript
// In remotion/src/Root.tsx
const calcMyNewChartDemoMetadata: CalculateMetadataFunction<MyNewChartDemoProps> = ({ props }) => {
  const width = props.dimensions?.width ?? 1080;
  const height = props.dimensions?.height ?? 1080;
  const animDuration = props.animation?.duration ?? 30;
  const durationInFrames = Math.ceil(animDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};
```

### 4. Register the Composition

```typescript
// In remotion/src/Root.tsx, inside RemotionRoot
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* ... existing compositions ... */}
      <Composition<MyNewChartDemoProps, any>
        id="MyNewChartDemo"
        component={MyNewChartDemo}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          data: [{ label: "A", value: 100 }],
        }}
        calculateMetadata={calcMyNewChartDemoMetadata}
      />
    </>
  );
};
```

### 5. Add to Python Renderer

```python
# In src/services/chart_renderer.py
chart_type_to_composition = {
    "bar": "BarChartDemo",
    # ... existing types ...
    "myNew": "MyNewChartDemo",  # Add this
}
```

### 6. Create JSON Template

```json
// docs/charts/my-new-chart-basic.json
{
  "_schema_desc": "My New Chart Template",
  "chartType": "myNew",
  "data": [
    { "label": "A", "value": 100 },
    { "label": "B", "value": 200 }
  ],
  "animation": { "duration": 30 }
}
```

---

## Troubleshooting

### "Remotion not found"

```bash
cd remotion
pnpm install
```

### "FFmpeg not found"

Install FFmpeg:
- Windows: `choco install ffmpeg` or download from ffmpeg.org
- Mac: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

### "Chart renders but is wrong duration"

Check that the `calculateMetadata` function in Root.tsx correctly calculates `durationInFrames` based on your animation props.

### "Green screen looks wrong"

Ensure `background.color` is exactly `#00FF00`. Any other green shade may not chroma key correctly.

---

## Environment Variables

None required for chart rendering. The Remotion project is self-contained.

---

## Output Specifications

All rendered charts will have:

| Property | Value |
|----------|-------|
| Resolution | 1080 × 1080 (1:1 square) |
| Frame Rate | 30 fps |
| Format | MP4 (H.264) |
| Background | Green (#00FF00) for chroma key |
| Duration | Calculated from animation props |
