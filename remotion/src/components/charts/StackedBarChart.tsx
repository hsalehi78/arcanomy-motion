/**
 * StackedBarChart Component - Animated stacked bar chart for Remotion
 * 
 * Perfect for:
 * - Showing composition of multiple categories
 * - Comparing parts of a whole across groups
 * - "How spending changed over time" type visualizations
 * 
 * Each bar is divided into segments representing different data series.
 */

import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS, ANIMATION } from "../../lib/constants";

// =============================================================================
// GOOGLE FONTS IMPORT
// =============================================================================

const GOOGLE_FONTS_IMPORT = `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=Montserrat:wght@400;500;700&display=swap');`;

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

export interface StackedBarDataPoint {
  label: string;           // Category (e.g., "Q1", "2023")
  values: number[];        // Values for each series
}

export interface StackedBarSeries {
  name: string;            // Series name (e.g., "Revenue", "Costs")
  color: string;           // Series color
}

export interface FontConfig {
  family?: string;
  size?: number;
  weight?: number;
}

export interface MarginConfig {
  top?: number;
  right?: number;
  bottom?: number;
  left?: number;
}

export interface StackedBarChartProps {
  /** Array of categories, each with values for all series */
  data: StackedBarDataPoint[];
  
  /** Series definitions (names and colors) */
  series: StackedBarSeries[];
  
  /** Stack mode: 'stacked' or 'grouped' */
  mode?: "stacked" | "grouped";
  
  dimensions?: {
    width?: number;
    height?: number;
    margin?: MarginConfig;
  };
  width?: number;
  height?: number;
  
  background?: {
    color?: string;
  };
  
  title?: {
    show?: boolean;
    text?: string;
    y?: number;
    font?: FontConfig;
    color?: string;
  };
  
  subtitle?: {
    show?: boolean;
    text?: string;
    y?: number;
    font?: FontConfig;
    color?: string;
  };
  
  xAxis?: {
    show?: boolean;
    label?: {
      font?: FontConfig;
      color?: string;
    };
  };
  
  yAxis?: {
    show?: boolean;
    label?: {
      font?: FontConfig;
      color?: string;
    };
    gridLines?: {
      show?: boolean;
      color?: string;
    };
  };
  
  bars?: {
    gap?: number;
    cornerRadius?: number;
  };
  
  legend?: {
    show?: boolean;
    position?: "top" | "bottom" | "right";
    font?: FontConfig;
    color?: string;
  };
  
  animation?: {
    duration?: number;
    style?: "simultaneous" | "staggered";
    staggerDelay?: number;
  };
}

// =============================================================================
// COMPONENT
// =============================================================================

export const StackedBarChart: React.FC<StackedBarChartProps> = (props) => {
  const frame = useCurrentFrame();
  const { data, series } = props;

  if (!data || data.length === 0 || !series || series.length === 0) return null;

  const mode = props.mode ?? "stacked";

  // ==========================================================================
  // PROP EXTRACTION
  // ==========================================================================
  
  const width = props.dimensions?.width ?? props.width ?? 1080;
  const height = props.dimensions?.height ?? props.height ?? 1080;
  const margin: MarginConfig = {
    top: props.dimensions?.margin?.top ?? 200,
    right: props.dimensions?.margin?.right ?? 60,
    bottom: props.dimensions?.margin?.bottom ?? 140,
    left: props.dimensions?.margin?.left ?? 100,
  };
  
  const bgColor = props.background?.color ?? COLORS.bg;
  
  // Title
  const showTitle = props.title?.show ?? true;
  const titleText = props.title?.text ?? "";
  const titleY = props.title?.y ?? 60;
  const titleFont = props.title?.font ?? {};
  const titleColor = props.title?.color ?? "#FFFFFF";
  
  // Subtitle
  const showSubtitle = props.subtitle?.show ?? false;
  const subtitleText = props.subtitle?.text ?? "";
  const subtitleY = props.subtitle?.y ?? 120;
  const subtitleFont = props.subtitle?.font ?? {};
  const subtitleColor = props.subtitle?.color ?? "#888888";
  
  // X-Axis
  const showXAxis = props.xAxis?.show ?? true;
  const xLabelFont = props.xAxis?.label?.font ?? {};
  const xLabelColor = props.xAxis?.label?.color ?? "#FFFFFF";
  
  // Y-Axis
  const showYAxis = props.yAxis?.show ?? true;
  const yLabelFont = props.yAxis?.label?.font ?? {};
  const yLabelColor = props.yAxis?.label?.color ?? "#888888";
  const showGridLines = props.yAxis?.gridLines?.show ?? true;
  const gridLineColor = props.yAxis?.gridLines?.color ?? "#333333";
  
  // Bars
  const barGap = props.bars?.gap ?? 24;
  const cornerRadius = props.bars?.cornerRadius ?? 4;
  
  // Legend
  const showLegend = props.legend?.show ?? true;
  const legendPosition = props.legend?.position ?? "top";
  const legendFont = props.legend?.font ?? {};
  const legendColor = props.legend?.color ?? "#FFFFFF";
  
  // Animation
  const animationDuration = props.animation?.duration ?? ANIMATION.chartDrawDuration;
  const animationStyle = props.animation?.style ?? "simultaneous";
  const staggerDelay = props.animation?.staggerDelay ?? 5;

  // ==========================================================================
  // LAYOUT CALCULATIONS
  // ==========================================================================
  
  const chartWidth = width - (margin.left ?? 0) - (margin.right ?? 0);
  const chartHeight = height - (margin.top ?? 0) - (margin.bottom ?? 0);
  
  // Calculate max value for scaling
  let maxValue = 0;
  if (mode === "stacked") {
    // Max is sum of all series for each category
    data.forEach(d => {
      const sum = d.values.reduce((a, b) => a + b, 0);
      maxValue = Math.max(maxValue, sum);
    });
  } else {
    // Max is highest individual value
    data.forEach(d => {
      d.values.forEach(v => {
        maxValue = Math.max(maxValue, v);
      });
    });
  }
  
  const barWidth = (chartWidth - barGap * (data.length - 1)) / data.length;

  // ==========================================================================
  // ANIMATION
  // ==========================================================================
  
  const getProgress = (categoryIndex: number): number => {
    if (animationStyle === "simultaneous") {
      return interpolate(frame, [0, animationDuration], [0, 1], { extrapolateRight: "clamp" });
    } else {
      const startFrame = categoryIndex * staggerDelay;
      return interpolate(frame, [startFrame, startFrame + animationDuration], [0, 1], 
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    }
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <svg width={width} height={height}>
      <defs>
        <style>{GOOGLE_FONTS_IMPORT}</style>
      </defs>
      
      <rect width={width} height={height} fill={bgColor} />

      {/* Title */}
      {showTitle && titleText && (
        <text
          x={width / 2}
          y={titleY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={titleColor}
          fontSize={titleFont.size ?? 56}
          fontWeight={titleFont.weight ?? 700}
          fontFamily={titleFont.family ?? "Montserrat, Inter, sans-serif"}
        >
          {titleText}
        </text>
      )}

      {/* Subtitle */}
      {showSubtitle && subtitleText && (
        <text
          x={width / 2}
          y={subtitleY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={subtitleColor}
          fontSize={subtitleFont.size ?? 36}
          fontWeight={subtitleFont.weight ?? 400}
          fontFamily={subtitleFont.family ?? "Inter, sans-serif"}
        >
          {subtitleText}
        </text>
      )}

      {/* Legend */}
      {showLegend && legendPosition === "top" && (
        <g>
          {series.map((s, i) => {
            const legendX = width / 2 - (series.length * 100) / 2 + i * 120;
            return (
              <g key={`legend-${i}`}>
                <rect
                  x={legendX}
                  y={subtitleY + 40}
                  width={20}
                  height={20}
                  fill={s.color}
                  rx={3}
                />
                <text
                  x={legendX + 28}
                  y={subtitleY + 50}
                  dominantBaseline="middle"
                  fill={legendColor}
                  fontSize={legendFont.size ?? 24}
                  fontWeight={legendFont.weight ?? 500}
                  fontFamily={legendFont.family ?? "Inter, sans-serif"}
                >
                  {s.name}
                </text>
              </g>
            );
          })}
        </g>
      )}

      {/* Grid lines */}
      {showGridLines && (
        <g stroke={gridLineColor} strokeWidth={1} opacity={0.5}>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={`grid-${ratio}`}
              x1={margin.left}
              y1={(margin.top ?? 0) + chartHeight * (1 - ratio)}
              x2={width - (margin.right ?? 0)}
              y2={(margin.top ?? 0) + chartHeight * (1 - ratio)}
            />
          ))}
        </g>
      )}

      {/* Y-Axis labels */}
      {showYAxis && (
        <g>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <text
              key={`y-label-${ratio}`}
              x={(margin.left ?? 0) - 10}
              y={(margin.top ?? 0) + chartHeight * (1 - ratio)}
              textAnchor="end"
              dominantBaseline="middle"
              fill={yLabelColor}
              fontSize={yLabelFont.size ?? 24}
              fontWeight={yLabelFont.weight ?? 400}
              fontFamily={yLabelFont.family ?? "Inter, sans-serif"}
            >
              {Math.round(maxValue * ratio)}
            </text>
          ))}
        </g>
      )}

      {/* Stacked Bars */}
      {data.map((category, catIndex) => {
        const progress = getProgress(catIndex);
        const x = (margin.left ?? 0) + catIndex * (barWidth + barGap);
        
        // Calculate cumulative heights for stacking
        let cumulativeHeight = 0;
        
        return (
          <g key={catIndex}>
            {mode === "stacked" ? (
              // Stacked mode: bars on top of each other
              category.values.map((value, seriesIndex) => {
                const segmentHeight = (value / maxValue) * chartHeight * progress;
                const y = (margin.top ?? 0) + chartHeight - cumulativeHeight - segmentHeight;
                cumulativeHeight += segmentHeight;
                
                return (
                  <rect
                    key={seriesIndex}
                    x={x}
                    y={y}
                    width={barWidth}
                    height={Math.max(0, segmentHeight)}
                    fill={series[seriesIndex]?.color ?? COLORS.highlight}
                    rx={seriesIndex === category.values.length - 1 ? cornerRadius : 0}
                    ry={seriesIndex === category.values.length - 1 ? cornerRadius : 0}
                  />
                );
              })
            ) : (
              // Grouped mode: bars side by side
              category.values.map((value, seriesIndex) => {
                const groupedBarWidth = barWidth / series.length - 4;
                const groupedX = x + seriesIndex * (groupedBarWidth + 4);
                const barHeight = (value / maxValue) * chartHeight * progress;
                const y = (margin.top ?? 0) + chartHeight - barHeight;
                
                return (
                  <rect
                    key={seriesIndex}
                    x={groupedX}
                    y={y}
                    width={groupedBarWidth}
                    height={Math.max(0, barHeight)}
                    fill={series[seriesIndex]?.color ?? COLORS.highlight}
                    rx={cornerRadius}
                    ry={cornerRadius}
                  />
                );
              })
            )}

            {/* X-Axis label */}
            {showXAxis && (
              <text
                x={x + barWidth / 2}
                y={height - (margin.bottom ?? 0) + 40}
                textAnchor="middle"
                fill={xLabelColor}
                fontSize={xLabelFont.size ?? 28}
                fontWeight={xLabelFont.weight ?? 500}
                fontFamily={xLabelFont.family ?? "Inter, sans-serif"}
                opacity={progress}
              >
                {category.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

