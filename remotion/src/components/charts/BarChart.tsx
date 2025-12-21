import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS, ANIMATION } from "../../lib/constants";

export interface BarData {
  label: string;
  value: number;
  color?: string;
}

export interface BarChartProps {
  data: BarData[];
  width?: number;
  height?: number;
  colors?: typeof COLORS;
  animationDuration?: number;
  barGap?: number;
  showLabels?: boolean;
  showValues?: boolean;
  title?: string;
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  width = 800,
  height = 500,
  colors = COLORS,
  animationDuration = ANIMATION.chartDrawDuration,
  barGap = 20,
  showLabels = true,
  showValues = true,
  title,
}) => {
  const frame = useCurrentFrame();

  if (data.length === 0) return null;

  // Layout calculations
  const padding = { top: title ? 80 : 40, right: 40, bottom: 80, left: 40 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maxValue = Math.max(...data.map((d) => d.value));
  const barWidth = (chartWidth - barGap * (data.length - 1)) / data.length;

  // Animation progress (0 to 1)
  const progress = interpolate(
    frame,
    [0, animationDuration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  return (
    <svg width={width} height={height}>
      {/* Background */}
      <rect width={width} height={height} fill={colors.bg} />

      {/* Title */}
      {title && (
        <text
          x={width / 2}
          y={40}
          textAnchor="middle"
          fill={colors.textPrimary}
          fontSize={24}
          fontWeight="bold"
          fontFamily="system-ui, -apple-system, sans-serif"
        >
          {title}
        </text>
      )}

      {/* Horizontal grid lines */}
      <g stroke={colors.bgSecondary} strokeWidth={1} opacity={0.5}>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
          <line
            key={`grid-${ratio}`}
            x1={padding.left}
            y1={padding.top + chartHeight * (1 - ratio)}
            x2={width - padding.right}
            y2={padding.top + chartHeight * (1 - ratio)}
          />
        ))}
      </g>

      {/* Bars */}
      {data.map((item, index) => {
        const barHeight = (item.value / maxValue) * chartHeight * progress;
        const x = padding.left + index * (barWidth + barGap);
        const y = padding.top + chartHeight - barHeight;

        return (
          <g key={index}>
            {/* Bar */}
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={Math.max(0, barHeight)}
              fill={item.color || colors.highlight}
              rx={4}
              ry={4}
            />

            {/* Value label (appears after animation) */}
            {showValues && progress >= 1 && (
              <text
                x={x + barWidth / 2}
                y={y - 10}
                textAnchor="middle"
                fill={colors.textPrimary}
                fontSize={16}
                fontWeight="bold"
                fontFamily="system-ui, -apple-system, sans-serif"
              >
                {item.value}
              </text>
            )}

            {/* Category label */}
            {showLabels && (
              <text
                x={x + barWidth / 2}
                y={height - padding.bottom + 30}
                textAnchor="middle"
                fill={colors.textPrimary}
                fontSize={14}
                fontFamily="system-ui, -apple-system, sans-serif"
                opacity={progress}
              >
                {item.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

