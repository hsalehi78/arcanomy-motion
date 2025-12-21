/**
 * ProgressChart Component - Animated circular progress/gauge for Remotion
 * 
 * Perfect for:
 * - Single percentage metrics ("85% of people...")
 * - Completion rates, goals, achievements
 * - Satisfying fill animations
 * 
 * Shows a circular arc that fills to represent a percentage.
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

export interface FontConfig {
  family?: string;
  size?: number;
  weight?: number;
}

export interface ProgressChartProps {
  /** The value to display (0-100 for percentage, or any number) */
  value: number;
  
  /** Maximum value (default 100 for percentage) */
  maxValue?: number;
  
  /** Display format */
  format?: "percent" | "number" | "custom";
  
  /** Custom suffix (e.g., "K", "M", "$") */
  suffix?: string;
  
  /** Custom prefix (e.g., "$", "€") */
  prefix?: string;
  
  dimensions?: {
    width?: number;
    height?: number;
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
    font?: FontConfig;
    color?: string;
  };
  
  /** Circle/arc styling */
  circle?: {
    radius?: number;
    strokeWidth?: number;
    backgroundColor?: string;
    fillColor?: string;
    startAngle?: number;  // -90 = top
  };
  
  /** Center value display */
  centerValue?: {
    show?: boolean;
    font?: FontConfig;
    color?: string;
  };
  
  /** Label below the value */
  label?: {
    show?: boolean;
    text?: string;
    font?: FontConfig;
    color?: string;
  };
  
  animation?: {
    duration?: number;
    easing?: "linear" | "ease-out";
  };
}

// =============================================================================
// COMPONENT
// =============================================================================

export const ProgressChart: React.FC<ProgressChartProps> = (props) => {
  const frame = useCurrentFrame();
  
  const value = props.value ?? 0;
  const maxValue = props.maxValue ?? 100;
  const format = props.format ?? "percent";
  const suffix = props.suffix ?? "";
  const prefix = props.prefix ?? "";

  // ==========================================================================
  // PROP EXTRACTION
  // ==========================================================================
  
  const width = props.dimensions?.width ?? props.width ?? 1080;
  const height = props.dimensions?.height ?? props.height ?? 1080;
  const bgColor = props.background?.color ?? COLORS.bg;
  
  // Title
  const showTitle = props.title?.show ?? true;
  const titleText = props.title?.text ?? "";
  const titleY = props.title?.y ?? 100;
  const titleFont = props.title?.font ?? {};
  const titleColor = props.title?.color ?? "#FFFFFF";
  
  // Subtitle
  const showSubtitle = props.subtitle?.show ?? false;
  const subtitleText = props.subtitle?.text ?? "";
  const subtitleFont = props.subtitle?.font ?? {};
  const subtitleColor = props.subtitle?.color ?? "#888888";
  
  // Circle
  const radius = props.circle?.radius ?? Math.min(width, height) * 0.3;
  const strokeWidth = props.circle?.strokeWidth ?? 30;
  const circleBgColor = props.circle?.backgroundColor ?? "#333333";
  const fillColor = props.circle?.fillColor ?? COLORS.highlight;
  const startAngle = props.circle?.startAngle ?? -90;
  
  // Center value
  const showCenterValue = props.centerValue?.show ?? true;
  const centerValueFont = props.centerValue?.font ?? {};
  const centerValueColor = props.centerValue?.color ?? "#FFFFFF";
  
  // Label
  const showLabel = props.label?.show ?? false;
  const labelText = props.label?.text ?? "";
  const labelFont = props.label?.font ?? {};
  const labelColor = props.label?.color ?? "#888888";
  
  // Animation
  const animationDuration = props.animation?.duration ?? 45;

  // ==========================================================================
  // CALCULATIONS
  // ==========================================================================
  
  const centerX = width / 2;
  const centerY = height / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min(value / maxValue, 1);
  
  // Animation progress
  const progress = interpolate(
    frame,
    [0, animationDuration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );
  
  const animatedPercentage = percentage * progress;
  const strokeDashoffset = circumference * (1 - animatedPercentage);
  
  // Animated value for display
  const displayValue = Math.round(value * progress);
  
  // Format the display value
  let formattedValue = "";
  if (format === "percent") {
    formattedValue = `${displayValue}%`;
  } else if (format === "number") {
    formattedValue = `${prefix}${displayValue.toLocaleString()}${suffix}`;
  } else {
    formattedValue = `${prefix}${displayValue}${suffix}`;
  }

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
          x={centerX}
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

      {/* Background circle */}
      <circle
        cx={centerX}
        cy={centerY}
        r={radius}
        fill="none"
        stroke={circleBgColor}
        strokeWidth={strokeWidth}
      />

      {/* Progress arc */}
      <circle
        cx={centerX}
        cy={centerY}
        r={radius}
        fill="none"
        stroke={fillColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        transform={`rotate(${startAngle} ${centerX} ${centerY})`}
      />

      {/* Center value */}
      {showCenterValue && (
        <text
          x={centerX}
          y={centerY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={centerValueColor}
          fontSize={centerValueFont.size ?? 120}
          fontWeight={centerValueFont.weight ?? 700}
          fontFamily={centerValueFont.family ?? "Montserrat, sans-serif"}
        >
          {formattedValue}
        </text>
      )}

      {/* Label below value */}
      {showLabel && labelText && (
        <text
          x={centerX}
          y={centerY + (centerValueFont.size ?? 120) / 2 + 40}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={labelColor}
          fontSize={labelFont.size ?? 36}
          fontWeight={labelFont.weight ?? 500}
          fontFamily={labelFont.family ?? "Inter, sans-serif"}
        >
          {labelText}
        </text>
      )}

      {/* Subtitle (bottom) */}
      {showSubtitle && subtitleText && (
        <text
          x={centerX}
          y={height - 100}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={subtitleColor}
          fontSize={subtitleFont.size ?? 32}
          fontWeight={subtitleFont.weight ?? 400}
          fontFamily={subtitleFont.family ?? "Inter, sans-serif"}
        >
          {subtitleText}
        </text>
      )}
    </svg>
  );
};

