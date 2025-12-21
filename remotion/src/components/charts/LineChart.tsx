/**
 * LineChart Component - Animated line chart for Remotion
 * 
 * This component renders a fully customizable line chart with:
 * - Animated line draw (reveals from left to right)
 * - Data points with optional labels
 * - Customizable colors, fonts, grid
 * - Area fill option
 * 
 * Props can be provided in nested format matching the JSON schema.
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

/**
 * Single data point for the line chart
 */
export interface LineDataPoint {
  label?: string;     // X-axis label (e.g., "Jan", "Q1")
  x?: number;         // X value (numeric, for scatter-style)
  y: number;          // Y value
}

/**
 * Font configuration
 */
export interface FontConfig {
  family?: string;
  size?: number;
  weight?: number;
}

/**
 * Margin configuration
 */
export interface MarginConfig {
  top?: number;
  right?: number;
  bottom?: number;
  left?: number;
}

/**
 * Comprehensive props for the LineChart component
 */
export interface LineChartProps {
  /** Required: Array of data points */
  data: LineDataPoint[];
  
  /** Dimensions */
  dimensions?: {
    width?: number;
    height?: number;
    margin?: MarginConfig;
  };
  width?: number;
  height?: number;
  
  /** Background */
  background?: {
    color?: string;
  };
  
  /** Title */
  title?: {
    show?: boolean;
    text?: string;
    y?: number;
    font?: FontConfig;
    color?: string;
  };
  
  /** Subtitle */
  subtitle?: {
    show?: boolean;
    text?: string;
    y?: number;
    font?: FontConfig;
    color?: string;
  };
  
  /** X-Axis */
  xAxis?: {
    show?: boolean;
    label?: {
      font?: FontConfig;
      color?: string;
    };
  };
  
  /** Y-Axis */
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
  
  /** Line styling */
  line?: {
    color?: string;
    width?: number;
    curve?: "linear" | "smooth";  // Line interpolation
  };
  
  /** Area fill under the line */
  area?: {
    show?: boolean;
    color?: string;       // Fill color (with transparency)
    gradient?: boolean;   // Gradient fill from top to bottom
  };
  
  /** Data points */
  points?: {
    show?: boolean;
    radius?: number;
    color?: string;
  };
  
  /** Data labels */
  dataLabels?: {
    show?: boolean;
    position?: "above" | "below";
    font?: FontConfig;
    color?: string;
  };
  
  /** Animation */
  animation?: {
    duration?: number;
  };
  
  /** Legacy props */
  colors?: typeof COLORS;
  animationDuration?: number;
}

// =============================================================================
// COMPONENT
// =============================================================================

export const LineChart: React.FC<LineChartProps> = (props) => {
  const frame = useCurrentFrame();
  const { data } = props;

  if (!data || data.length === 0) return null;

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
  
  // Line
  const lineColor = props.line?.color ?? COLORS.chartLine;
  const lineWidth = props.line?.width ?? 4;
  
  // Area
  const showArea = props.area?.show ?? false;
  const areaColor = props.area?.color ?? `${lineColor}40`;  // 25% opacity
  
  // Points
  const showPoints = props.points?.show ?? true;
  const pointRadius = props.points?.radius ?? 8;
  const pointColor = props.points?.color ?? lineColor;
  
  // Data labels
  const showDataLabels = props.dataLabels?.show ?? false;
  const dataLabelPosition = props.dataLabels?.position ?? "above";
  const dataLabelFont = props.dataLabels?.font ?? {};
  const dataLabelColor = props.dataLabels?.color ?? "#FFFFFF";
  
  // Animation
  const animationDuration = props.animation?.duration ?? props.animationDuration ?? ANIMATION.chartDrawDuration;

  // ==========================================================================
  // LAYOUT CALCULATIONS
  // ==========================================================================
  
  const chartWidth = width - (margin.left ?? 0) - (margin.right ?? 0);
  const chartHeight = height - (margin.top ?? 0) - (margin.bottom ?? 0);
  
  // Calculate value ranges
  const yValues = data.map(d => d.y);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const yRange = yMax - yMin || 1;
  
  // Scale functions
  const scaleX = (index: number) => {
    return (margin.left ?? 0) + (index / (data.length - 1)) * chartWidth;
  };
  
  const scaleY = (value: number) => {
    const normalized = (value - yMin) / yRange;
    return (margin.top ?? 0) + chartHeight * (1 - normalized);
  };
  
  // Create points array
  const points = data.map((d, i) => ({
    x: scaleX(i),
    y: scaleY(d.y),
    label: d.label ?? `${i + 1}`,
    value: d.y,
  }));

  // ==========================================================================
  // ANIMATION
  // ==========================================================================
  
  const drawProgress = interpolate(
    frame,
    [0, animationDuration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );
  
  // Calculate visible points based on progress
  const visiblePointCount = Math.floor(points.length * drawProgress);
  const partialProgress = (points.length * drawProgress) - visiblePointCount;

  // ==========================================================================
  // PATH GENERATION
  // ==========================================================================
  
  // Generate line path
  let linePath = "";
  for (let i = 0; i <= visiblePointCount && i < points.length; i++) {
    const point = points[i];
    let x = point.x;
    let y = point.y;
    
    // For the partial point, interpolate position
    if (i === visiblePointCount && i < points.length - 1) {
      const nextPoint = points[i + 1];
      x = point.x + (nextPoint.x - point.x) * partialProgress;
      y = point.y + (nextPoint.y - point.y) * partialProgress;
    }
    
    linePath += `${i === 0 ? "M" : "L"} ${x} ${y} `;
  }
  
  // Generate area path
  let areaPath = linePath;
  if (linePath && showArea) {
    const lastX = visiblePointCount < points.length - 1
      ? points[visiblePointCount].x + (points[visiblePointCount + 1]?.x - points[visiblePointCount].x) * partialProgress
      : points[points.length - 1].x;
    const baseY = (margin.top ?? 0) + chartHeight;
    areaPath += `L ${lastX} ${baseY} L ${margin.left} ${baseY} Z`;
  }

  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <svg width={width} height={height}>
      {/* Google Fonts import */}
      <defs>
        <style>{GOOGLE_FONTS_IMPORT}</style>
        {/* Gradient for area fill */}
        <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={lineColor} stopOpacity={0.4} />
          <stop offset="100%" stopColor={lineColor} stopOpacity={0.05} />
        </linearGradient>
      </defs>
      
      {/* Background */}
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

      {/* Grid lines */}
      {showGridLines && (
        <g stroke={gridLineColor} strokeWidth={1} opacity={0.5}>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={`grid-${ratio}`}
              x1={margin.left}
              y1={(margin.top ?? 0) + chartHeight * ratio}
              x2={width - (margin.right ?? 0)}
              y2={(margin.top ?? 0) + chartHeight * ratio}
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
              x={(margin.left ?? 0) - 15}
              y={(margin.top ?? 0) + chartHeight * (1 - ratio)}
              textAnchor="end"
              dominantBaseline="middle"
              fill={yLabelColor}
              fontSize={yLabelFont.size ?? 28}
              fontWeight={yLabelFont.weight ?? 400}
              fontFamily={yLabelFont.family ?? "Inter, sans-serif"}
              opacity={drawProgress}
            >
              {Math.round(yMin + yRange * ratio)}
            </text>
          ))}
        </g>
      )}

      {/* Area fill */}
      {showArea && areaPath && (
        <path
          d={areaPath}
          fill="url(#areaGradient)"
        />
      )}

      {/* Line */}
      {linePath && (
        <path
          d={linePath}
          fill="none"
          stroke={lineColor}
          strokeWidth={lineWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}

      {/* Data points */}
      {showPoints && points.slice(0, visiblePointCount + 1).map((point, index) => {
        // Only show point if fully visible
        if (index > visiblePointCount) return null;
        
        return (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r={pointRadius}
            fill={pointColor}
          />
        );
      })}

      {/* X-Axis labels */}
      {showXAxis && (
        <g>
          {points.map((point, index) => {
            if (index > visiblePointCount) return null;
            return (
              <text
                key={`x-label-${index}`}
                x={point.x}
                y={height - (margin.bottom ?? 0) + 40}
                textAnchor="middle"
                fill={xLabelColor}
                fontSize={xLabelFont.size ?? 32}
                fontWeight={xLabelFont.weight ?? 500}
                fontFamily={xLabelFont.family ?? "Inter, sans-serif"}
              >
                {point.label}
              </text>
            );
          })}
        </g>
      )}

      {/* Data labels */}
      {showDataLabels && drawProgress >= 1 && points.map((point, index) => (
        <text
          key={`data-label-${index}`}
          x={point.x}
          y={dataLabelPosition === "above" ? point.y - 20 : point.y + 30}
          textAnchor="middle"
          fill={dataLabelColor}
          fontSize={dataLabelFont.size ?? 28}
          fontWeight={dataLabelFont.weight ?? 700}
          fontFamily={dataLabelFont.family ?? "Montserrat, sans-serif"}
        >
          {point.value}
        </text>
      ))}
    </svg>
  );
};
