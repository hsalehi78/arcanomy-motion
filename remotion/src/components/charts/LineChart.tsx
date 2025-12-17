import { useCurrentFrame, interpolate } from "remotion";
import { COLORS, ANIMATION } from "../../lib/constants";

interface DataPoint {
  x: number;
  y: number;
}

interface LineChartProps {
  data: DataPoint[];
  width?: number;
  height?: number;
  colors?: typeof COLORS;
  animationDuration?: number;
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  width = 800,
  height = 400,
  colors = COLORS,
  animationDuration = ANIMATION.chartDrawDuration,
}) => {
  const frame = useCurrentFrame();

  if (data.length === 0) return null;

  // Normalize data to SVG coordinates
  const padding = 40;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const xMin = Math.min(...data.map((d) => d.x));
  const xMax = Math.max(...data.map((d) => d.x));
  const yMin = Math.min(...data.map((d) => d.y));
  const yMax = Math.max(...data.map((d) => d.y));

  const scaleX = (x: number) =>
    padding + ((x - xMin) / (xMax - xMin)) * chartWidth;
  const scaleY = (y: number) =>
    height - padding - ((y - yMin) / (yMax - yMin)) * chartHeight;

  // Create path
  const pathData = data
    .map((point, i) => {
      const x = scaleX(point.x);
      const y = scaleY(point.y);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  // Calculate path length for draw animation
  const pathLength = 1000; // Approximate, will be overridden by CSS
  const drawProgress = interpolate(
    frame,
    [0, animationDuration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  return (
    <svg width={width} height={height}>
      {/* Grid lines */}
      <g stroke={colors.bgSecondary} strokeWidth={1}>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
          <line
            key={`h-${ratio}`}
            x1={padding}
            y1={padding + chartHeight * ratio}
            x2={width - padding}
            y2={padding + chartHeight * ratio}
          />
        ))}
      </g>

      {/* Main line */}
      <path
        d={pathData}
        fill="none"
        stroke={colors.chartLine}
        strokeWidth={3}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={pathLength}
        strokeDashoffset={pathLength * (1 - drawProgress)}
      />

      {/* Data points (appear after line is drawn) */}
      {drawProgress >= 1 &&
        data.map((point, i) => (
          <circle
            key={i}
            cx={scaleX(point.x)}
            cy={scaleY(point.y)}
            r={4}
            fill={colors.highlight}
          />
        ))}
    </svg>
  );
};

