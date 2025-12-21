/**
 * ScatterChart Component - Animated scatter plot for Remotion
 * 
 * This component renders a fully customizable scatter chart with:
 * - Animated point appearance (fade in, scale in)
 * - Optional connecting lines
 * - Customizable point sizes, colors
 * - Trend line option
 * 
 * Great for: Correlation data, distribution, comparing two variables
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
 * Single data point for the scatter chart
 */
export interface ScatterDataPoint {
  x: number;          // X value
  y: number;          // Y value
  label?: string;     // Optional label for this point
  size?: number;      // Optional custom size for this point
  color?: string;     // Optional custom color for this point
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
 * Comprehensive props for the ScatterChart component
 */
export interface ScatterChartProps {
  /** Required: Array of data points */
  data: ScatterDataPoint[];
  
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
    title?: string;        // Axis label (e.g., "Price ($)")
    label?: {
      font?: FontConfig;
      color?: string;
    };
  };
  
  /** Y-Axis */
  yAxis?: {
    show?: boolean;
    title?: string;        // Axis label (e.g., "Sales Volume")
    label?: {
      font?: FontConfig;
      color?: string;
    };
    gridLines?: {
      show?: boolean;
      color?: string;
    };
  };
  
  /** Point styling */
  points?: {
    radius?: number;       // Default point size
    color?: string;        // Default point color
    opacity?: number;      // Point opacity (0-1)
    stroke?: {
      color?: string;
      width?: number;
    };
  };
  
  /** Trend line */
  trendLine?: {
    show?: boolean;
    color?: string;
    width?: number;
    style?: "solid" | "dashed";
  };
  
  /** Point labels */
  pointLabels?: {
    show?: boolean;
    font?: FontConfig;
    color?: string;
  };
  
  /** Animation */
  animation?: {
    duration?: number;
    style?: "simultaneous" | "sequential" | "random";  // How points appear
    staggerDelay?: number;
  };
}

// =============================================================================
// COMPONENT
// =============================================================================

export const ScatterChart: React.FC<ScatterChartProps> = (props) => {
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
    right: props.dimensions?.margin?.right ?? 80,
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
  
  // Axes
  const showXAxis = props.xAxis?.show ?? true;
  const xAxisTitle = props.xAxis?.title ?? "";
  const xLabelFont = props.xAxis?.label?.font ?? {};
  const xLabelColor = props.xAxis?.label?.color ?? "#FFFFFF";
  
  const showYAxis = props.yAxis?.show ?? true;
  const yAxisTitle = props.yAxis?.title ?? "";
  const yLabelFont = props.yAxis?.label?.font ?? {};
  const yLabelColor = props.yAxis?.label?.color ?? "#888888";
  const showGridLines = props.yAxis?.gridLines?.show ?? true;
  const gridLineColor = props.yAxis?.gridLines?.color ?? "#333333";
  
  // Points
  const defaultRadius = props.points?.radius ?? 12;
  const defaultColor = props.points?.color ?? COLORS.highlight;
  const pointOpacity = props.points?.opacity ?? 0.9;
  const strokeColor = props.points?.stroke?.color ?? "#FFFFFF";
  const strokeWidth = props.points?.stroke?.width ?? 2;
  
  // Trend line
  const showTrendLine = props.trendLine?.show ?? false;
  const trendLineColor = props.trendLine?.color ?? "#FFFFFF";
  const trendLineWidth = props.trendLine?.width ?? 2;
  const trendLineStyle = props.trendLine?.style ?? "dashed";
  
  // Point labels
  const showPointLabels = props.pointLabels?.show ?? false;
  const pointLabelFont = props.pointLabels?.font ?? {};
  const pointLabelColor = props.pointLabels?.color ?? "#FFFFFF";
  
  // Animation
  const animationDuration = props.animation?.duration ?? ANIMATION.chartDrawDuration;
  const animationStyle = props.animation?.style ?? "simultaneous";
  const staggerDelay = props.animation?.staggerDelay ?? 3;

  // ==========================================================================
  // LAYOUT CALCULATIONS
  // ==========================================================================
  
  const chartWidth = width - (margin.left ?? 0) - (margin.right ?? 0);
  const chartHeight = height - (margin.top ?? 0) - (margin.bottom ?? 0);
  
  // Calculate value ranges
  const xValues = data.map(d => d.x);
  const yValues = data.map(d => d.y);
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const xRange = xMax - xMin || 1;
  const yRange = yMax - yMin || 1;
  
  // Add 10% padding to ranges
  const xPadding = xRange * 0.1;
  const yPadding = yRange * 0.1;
  
  // Scale functions
  const scaleX = (value: number) => {
    const normalized = (value - xMin + xPadding) / (xRange + xPadding * 2);
    return (margin.left ?? 0) + normalized * chartWidth;
  };
  
  const scaleY = (value: number) => {
    const normalized = (value - yMin + yPadding) / (yRange + yPadding * 2);
    return (margin.top ?? 0) + chartHeight * (1 - normalized);
  };
  
  // Prepare points
  const points = data.map((d, i) => ({
    x: scaleX(d.x),
    y: scaleY(d.y),
    rawX: d.x,
    rawY: d.y,
    label: d.label ?? "",
    size: d.size ?? defaultRadius,
    color: d.color ?? defaultColor,
    index: i,
  }));

  // ==========================================================================
  // ANIMATION
  // ==========================================================================
  
  const getPointProgress = (index: number): number => {
    if (animationStyle === "simultaneous") {
      return interpolate(
        frame,
        [0, animationDuration],
        [0, 1],
        { extrapolateRight: "clamp" }
      );
    } else if (animationStyle === "sequential") {
      const startFrame = index * staggerDelay;
      return interpolate(
        frame,
        [startFrame, startFrame + animationDuration / 2],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
    } else {
      // Random order
      const randomOrder = [3, 7, 1, 5, 0, 8, 2, 6, 4, 9][index % 10];
      const startFrame = randomOrder * staggerDelay;
      return interpolate(
        frame,
        [startFrame, startFrame + animationDuration / 2],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
    }
  };

  // ==========================================================================
  // TREND LINE CALCULATION (simple linear regression)
  // ==========================================================================
  
  let trendLine = { x1: 0, y1: 0, x2: 0, y2: 0 };
  if (showTrendLine && data.length >= 2) {
    const n = data.length;
    const sumX = data.reduce((s, d) => s + d.x, 0);
    const sumY = data.reduce((s, d) => s + d.y, 0);
    const sumXY = data.reduce((s, d) => s + d.x * d.y, 0);
    const sumX2 = data.reduce((s, d) => s + d.x * d.x, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    const y1 = slope * xMin + intercept;
    const y2 = slope * xMax + intercept;
    
    trendLine = {
      x1: scaleX(xMin),
      y1: scaleY(y1),
      x2: scaleX(xMax),
      y2: scaleY(y2),
    };
  }

  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <svg width={width} height={height}>
      {/* Google Fonts import */}
      <defs>
        <style>{GOOGLE_FONTS_IMPORT}</style>
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
          {/* Horizontal */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={`h-grid-${ratio}`}
              x1={margin.left}
              y1={(margin.top ?? 0) + chartHeight * ratio}
              x2={width - (margin.right ?? 0)}
              y2={(margin.top ?? 0) + chartHeight * ratio}
            />
          ))}
          {/* Vertical */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={`v-grid-${ratio}`}
              x1={(margin.left ?? 0) + chartWidth * ratio}
              y1={margin.top}
              x2={(margin.left ?? 0) + chartWidth * ratio}
              y2={(margin.top ?? 0) + chartHeight}
            />
          ))}
        </g>
      )}

      {/* Y-Axis labels */}
      {showYAxis && (
        <g>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = yMin + yRange * ratio;
            return (
              <text
                key={`y-label-${ratio}`}
                x={(margin.left ?? 0) - 15}
                y={(margin.top ?? 0) + chartHeight * (1 - ratio)}
                textAnchor="end"
                dominantBaseline="middle"
                fill={yLabelColor}
                fontSize={yLabelFont.size ?? 24}
                fontWeight={yLabelFont.weight ?? 400}
                fontFamily={yLabelFont.family ?? "Inter, sans-serif"}
              >
                {Math.round(value)}
              </text>
            );
          })}
          {/* Y-Axis title */}
          {yAxisTitle && (
            <text
              x={30}
              y={(margin.top ?? 0) + chartHeight / 2}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={yLabelColor}
              fontSize={28}
              fontWeight={500}
              fontFamily="Inter, sans-serif"
              transform={`rotate(-90, 30, ${(margin.top ?? 0) + chartHeight / 2})`}
            >
              {yAxisTitle}
            </text>
          )}
        </g>
      )}

      {/* X-Axis labels */}
      {showXAxis && (
        <g>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = xMin + xRange * ratio;
            return (
              <text
                key={`x-label-${ratio}`}
                x={(margin.left ?? 0) + chartWidth * ratio}
                y={height - (margin.bottom ?? 0) + 40}
                textAnchor="middle"
                fill={xLabelColor}
                fontSize={xLabelFont.size ?? 24}
                fontWeight={xLabelFont.weight ?? 400}
                fontFamily={xLabelFont.family ?? "Inter, sans-serif"}
              >
                {Math.round(value)}
              </text>
            );
          })}
          {/* X-Axis title */}
          {xAxisTitle && (
            <text
              x={(margin.left ?? 0) + chartWidth / 2}
              y={height - 30}
              textAnchor="middle"
              fill={xLabelColor}
              fontSize={28}
              fontWeight={500}
              fontFamily="Inter, sans-serif"
            >
              {xAxisTitle}
            </text>
          )}
        </g>
      )}

      {/* Trend line */}
      {showTrendLine && frame > animationDuration * 0.5 && (
        <line
          x1={trendLine.x1}
          y1={trendLine.y1}
          x2={trendLine.x2}
          y2={trendLine.y2}
          stroke={trendLineColor}
          strokeWidth={trendLineWidth}
          strokeDasharray={trendLineStyle === "dashed" ? "10,5" : undefined}
          opacity={interpolate(
            frame,
            [animationDuration * 0.5, animationDuration],
            [0, 0.7],
            { extrapolateRight: "clamp" }
          )}
        />
      )}

      {/* Data points */}
      {points.map((point, index) => {
        const progress = getPointProgress(index);
        if (progress === 0) return null;
        
        const scale = interpolate(progress, [0, 1], [0, 1]);
        const opacity = interpolate(progress, [0, 0.5, 1], [0, 0.5, pointOpacity]);
        
        return (
          <g key={index}>
            {/* Point */}
            <circle
              cx={point.x}
              cy={point.y}
              r={point.size * scale}
              fill={point.color}
              opacity={opacity}
              stroke={strokeColor}
              strokeWidth={strokeWidth}
            />
            
            {/* Point label */}
            {showPointLabels && point.label && progress >= 0.8 && (
              <text
                x={point.x}
                y={point.y - point.size - 10}
                textAnchor="middle"
                fill={pointLabelColor}
                fontSize={pointLabelFont.size ?? 20}
                fontWeight={pointLabelFont.weight ?? 500}
                fontFamily={pointLabelFont.family ?? "Inter, sans-serif"}
              >
                {point.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

