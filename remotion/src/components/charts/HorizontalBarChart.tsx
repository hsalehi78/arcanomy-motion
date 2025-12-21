/**
 * HorizontalBarChart Component - Animated horizontal bar chart for Remotion
 * 
 * Perfect for:
 * - Rankings and leaderboards ("Top 10...")
 * - Long category names that won't fit under vertical bars
 * - Reading order matches natural left-to-right scanning
 * 
 * Bars grow from left to right with customizable animation.
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

export interface HorizontalBarData {
  label: string;
  value: number;
  color?: string;
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

export interface HorizontalBarChartProps {
  data: HorizontalBarData[];
  
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
  
  labels?: {
    show?: boolean;
    position?: "left" | "inside" | "right";
    font?: FontConfig;
    color?: string;
  };
  
  values?: {
    show?: boolean;
    position?: "end" | "inside";
    font?: FontConfig;
    color?: string;
  };
  
  bars?: {
    height?: number;
    gap?: number;
    cornerRadius?: number;
    defaultColor?: string;
  };
  
  xAxis?: {
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
  
  animation?: {
    duration?: number;
    style?: "simultaneous" | "staggered" | "wave";
    velocityMode?: boolean;
    staggerDelay?: number;
    direction?: "top-to-bottom" | "bottom-to-top";
  };
}

// =============================================================================
// COMPONENT
// =============================================================================

export const HorizontalBarChart: React.FC<HorizontalBarChartProps> = (props) => {
  const frame = useCurrentFrame();
  const { data } = props;

  if (!data || data.length === 0) return null;

  // ==========================================================================
  // PROP EXTRACTION
  // ==========================================================================
  
  const width = props.dimensions?.width ?? props.width ?? 1080;
  const height = props.dimensions?.height ?? props.height ?? 1080;
  const margin: MarginConfig = {
    top: props.dimensions?.margin?.top ?? 180,
    right: props.dimensions?.margin?.right ?? 120,
    bottom: props.dimensions?.margin?.bottom ?? 80,
    left: props.dimensions?.margin?.left ?? 250,
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
  
  // Labels
  const showLabels = props.labels?.show ?? true;
  const labelPosition = props.labels?.position ?? "left";
  const labelFont = props.labels?.font ?? {};
  const labelColor = props.labels?.color ?? "#FFFFFF";
  
  // Values
  const showValues = props.values?.show ?? true;
  const valuePosition = props.values?.position ?? "end";
  const valueFont = props.values?.font ?? {};
  const valueColor = props.values?.color ?? "#FFFFFF";
  
  // Bars
  const barHeight = props.bars?.height ?? 50;
  const barGap = props.bars?.gap ?? 20;
  const cornerRadius = props.bars?.cornerRadius ?? 6;
  const defaultBarColor = props.bars?.defaultColor ?? COLORS.highlight;
  
  // X-Axis
  const showXAxis = props.xAxis?.show ?? false;
  const showGridLines = props.xAxis?.gridLines?.show ?? true;
  const gridLineColor = props.xAxis?.gridLines?.color ?? "#333333";
  
  // Animation
  const animationDuration = props.animation?.duration ?? ANIMATION.chartDrawDuration;
  const animationStyle = props.animation?.style ?? "staggered";
  const velocityMode = props.animation?.velocityMode ?? false;
  const staggerDelay = props.animation?.staggerDelay ?? 0;
  const animationDirection = props.animation?.direction ?? "top-to-bottom";

  // ==========================================================================
  // LAYOUT CALCULATIONS
  // ==========================================================================
  
  const chartWidth = width - (margin.left ?? 0) - (margin.right ?? 0);
  const chartHeight = height - (margin.top ?? 0) - (margin.bottom ?? 0);
  const maxValue = Math.max(...data.map((d) => d.value));
  const minValue = Math.min(...data.map((d) => d.value));

  // ==========================================================================
  // ANIMATION
  // ==========================================================================
  
  const getBarProgress = (barIndex: number): number => {
    let orderIndex = barIndex;
    if (animationDirection === "bottom-to-top") {
      orderIndex = data.length - 1 - barIndex;
    }

    const barValue = data[barIndex].value;
    const barDuration = velocityMode 
      ? animationDuration * (barValue / minValue)
      : animationDuration;

    if (animationStyle === "simultaneous") {
      return interpolate(frame, [0, barDuration], [0, 1], { extrapolateRight: "clamp" });
    } else if (animationStyle === "staggered") {
      const startFrame = orderIndex * (animationDuration + staggerDelay);
      return interpolate(frame, [startFrame, startFrame + barDuration], [0, 1], 
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    } else {
      const startFrame = orderIndex * staggerDelay;
      return interpolate(frame, [startFrame, startFrame + barDuration], [0, 1], 
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

      {/* Vertical grid lines */}
      {showGridLines && (
        <g stroke={gridLineColor} strokeWidth={1} opacity={0.5}>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={`grid-${ratio}`}
              x1={(margin.left ?? 0) + chartWidth * ratio}
              y1={margin.top}
              x2={(margin.left ?? 0) + chartWidth * ratio}
              y2={(margin.top ?? 0) + chartHeight}
            />
          ))}
        </g>
      )}

      {/* Bars */}
      {data.map((item, index) => {
        const progress = getBarProgress(index);
        const barW = (item.value / maxValue) * chartWidth * progress;
        const y = (margin.top ?? 0) + index * (barHeight + barGap);
        const x = margin.left ?? 0;

        return (
          <g key={index}>
            {/* Bar */}
            <rect
              x={x}
              y={y}
              width={Math.max(0, barW)}
              height={barHeight}
              fill={item.color || defaultBarColor}
              rx={cornerRadius}
              ry={cornerRadius}
            />

            {/* Label (left of bar) */}
            {showLabels && labelPosition === "left" && (
              <text
                x={x - 15}
                y={y + barHeight / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fill={labelColor}
                fontSize={labelFont.size ?? 32}
                fontWeight={labelFont.weight ?? 500}
                fontFamily={labelFont.family ?? "Inter, sans-serif"}
                opacity={progress > 0 ? 1 : 0}
              >
                {item.label}
              </text>
            )}

            {/* Value (at end of bar) */}
            {showValues && progress >= 1 && (
              <text
                x={valuePosition === "end" ? x + barW + 15 : x + barW - 15}
                y={y + barHeight / 2}
                textAnchor={valuePosition === "end" ? "start" : "end"}
                dominantBaseline="middle"
                fill={valueColor}
                fontSize={valueFont.size ?? 36}
                fontWeight={valueFont.weight ?? 700}
                fontFamily={valueFont.family ?? "Montserrat, sans-serif"}
              >
                {item.value}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

