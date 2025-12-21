/**
 * PieChart Component - Animated pie/donut chart for Remotion
 * 
 * This component renders a fully customizable pie chart with:
 * - Animated slice entrance (grows from 0 to full angle)
 * - Optional donut hole
 * - Customizable colors, fonts, labels
 * - Legend support
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
 * Single data point for the pie chart
 */
export interface PieData {
  label: string;      // Category name
  value: number;      // Numeric value (will be converted to percentage)
  color?: string;     // Optional hex color for this slice
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
 * Comprehensive props for the PieChart component
 */
export interface PieChartProps {
  /** Required: Array of data points */
  data: PieData[];
  
  /** Dimensions */
  dimensions?: {
    width?: number;
    height?: number;
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
  
  /** Pie styling */
  pie?: {
    innerRadius?: number;    // 0 = full pie, > 0 = donut
    outerRadius?: number;    // Radius of the pie
    startAngle?: number;     // Starting angle in degrees (0 = top)
    padAngle?: number;       // Gap between slices in degrees
    cornerRadius?: number;   // Rounded corners on slices
  };
  
  /** Slice labels */
  sliceLabels?: {
    show?: boolean;
    position?: "inside" | "outside";  // Where to show labels
    showValue?: boolean;     // Show the value
    showPercent?: boolean;   // Show percentage
    font?: FontConfig;
    color?: string;
  };
  
  /** Legend */
  legend?: {
    show?: boolean;
    position?: "right" | "bottom";
    font?: FontConfig;
    color?: string;
  };
  
  /** Animation */
  animation?: {
    duration?: number;       // Frames for full animation
    style?: "simultaneous" | "sequential";  // All at once or one by one
    staggerDelay?: number;   // Delay between slices for sequential
  };
  
  /** Default slice colors (used if not specified per-slice) */
  colors?: string[];
}

// =============================================================================
// DEFAULT COLORS
// =============================================================================

const DEFAULT_SLICE_COLORS = [
  "#FFD700",  // Gold
  "#FF3B30",  // Red
  "#00FF88",  // Green
  "#007AFF",  // Blue
  "#FF9500",  // Orange
  "#AF52DE",  // Purple
  "#5AC8FA",  // Cyan
  "#FF2D55",  // Pink
];

// =============================================================================
// COMPONENT
// =============================================================================

export const PieChart: React.FC<PieChartProps> = (props) => {
  const frame = useCurrentFrame();
  const { data } = props;

  if (!data || data.length === 0) return null;

  // ==========================================================================
  // PROP EXTRACTION
  // ==========================================================================
  
  const width = props.dimensions?.width ?? props.width ?? 1080;
  const height = props.dimensions?.height ?? props.height ?? 1080;
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
  
  // Pie styling
  const innerRadius = props.pie?.innerRadius ?? 0;  // 0 = full pie
  const outerRadius = props.pie?.outerRadius ?? Math.min(width, height) * 0.35;
  const startAngle = props.pie?.startAngle ?? -90;  // Start from top
  const padAngle = props.pie?.padAngle ?? 1;
  
  // Slice labels
  const showSliceLabels = props.sliceLabels?.show ?? true;
  const labelPosition = props.sliceLabels?.position ?? "outside";
  const showValue = props.sliceLabels?.showValue ?? false;
  const showPercent = props.sliceLabels?.showPercent ?? true;
  const sliceLabelFont = props.sliceLabels?.font ?? {};
  const sliceLabelColor = props.sliceLabels?.color ?? "#FFFFFF";
  
  // Legend
  const showLegend = props.legend?.show ?? true;
  const legendPosition = props.legend?.position ?? "right";
  const legendFont = props.legend?.font ?? {};
  const legendColor = props.legend?.color ?? "#FFFFFF";
  
  // Animation
  const animationDuration = props.animation?.duration ?? ANIMATION.chartDrawDuration;
  const animationStyle = props.animation?.style ?? "simultaneous";
  const staggerDelay = props.animation?.staggerDelay ?? 5;
  
  // Default colors
  const defaultColors = props.colors ?? DEFAULT_SLICE_COLORS;

  // ==========================================================================
  // CALCULATIONS
  // ==========================================================================
  
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const centerX = legendPosition === "right" ? width * 0.4 : width / 2;
  const centerY = legendPosition === "bottom" ? height * 0.4 : height / 2;
  
  // Calculate slice angles
  let currentAngle = startAngle;
  const slices = data.map((d, i) => {
    const percentage = d.value / total;
    const angle = percentage * 360 - padAngle;
    const slice = {
      ...d,
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
      percentage,
      color: d.color ?? defaultColors[i % defaultColors.length],
    };
    currentAngle += angle + padAngle;
    return slice;
  });

  // ==========================================================================
  // ANIMATION
  // ==========================================================================
  
  const getSliceProgress = (index: number): number => {
    if (animationStyle === "simultaneous") {
      return interpolate(
        frame,
        [0, animationDuration],
        [0, 1],
        { extrapolateRight: "clamp" }
      );
    } else {
      const startFrame = index * staggerDelay;
      return interpolate(
        frame,
        [startFrame, startFrame + animationDuration],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
    }
  };

  // ==========================================================================
  // PATH HELPERS
  // ==========================================================================
  
  const polarToCartesian = (cx: number, cy: number, r: number, angleDeg: number) => {
    const angleRad = (angleDeg * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(angleRad),
      y: cy + r * Math.sin(angleRad),
    };
  };

  const describeArc = (
    cx: number, cy: number,
    outerR: number, innerR: number,
    startAng: number, endAng: number
  ): string => {
    const start = polarToCartesian(cx, cy, outerR, endAng);
    const end = polarToCartesian(cx, cy, outerR, startAng);
    const largeArc = endAng - startAng <= 180 ? 0 : 1;
    
    if (innerR === 0) {
      // Full pie slice
      return [
        `M ${cx} ${cy}`,
        `L ${end.x} ${end.y}`,
        `A ${outerR} ${outerR} 0 ${largeArc} 1 ${start.x} ${start.y}`,
        `Z`
      ].join(" ");
    } else {
      // Donut slice
      const innerStart = polarToCartesian(cx, cy, innerR, endAng);
      const innerEnd = polarToCartesian(cx, cy, innerR, startAng);
      return [
        `M ${end.x} ${end.y}`,
        `A ${outerR} ${outerR} 0 ${largeArc} 1 ${start.x} ${start.y}`,
        `L ${innerStart.x} ${innerStart.y}`,
        `A ${innerR} ${innerR} 0 ${largeArc} 0 ${innerEnd.x} ${innerEnd.y}`,
        `Z`
      ].join(" ");
    }
  };

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

      {/* Pie slices */}
      {slices.map((slice, index) => {
        const progress = getSliceProgress(index);
        const animatedEndAngle = slice.startAngle + (slice.endAngle - slice.startAngle) * progress;
        
        if (progress === 0) return null;
        
        const path = describeArc(
          centerX, centerY,
          outerRadius, innerRadius,
          slice.startAngle, animatedEndAngle
        );
        
        // Label position
        const midAngle = (slice.startAngle + slice.endAngle) / 2;
        const labelRadius = labelPosition === "inside" 
          ? (outerRadius + innerRadius) / 2 
          : outerRadius + 30;
        const labelPos = polarToCartesian(centerX, centerY, labelRadius, midAngle);
        
        return (
          <g key={index}>
            {/* Slice */}
            <path
              d={path}
              fill={slice.color}
            />
            
            {/* Label */}
            {showSliceLabels && progress >= 0.8 && (
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill={sliceLabelColor}
                fontSize={sliceLabelFont.size ?? 32}
                fontWeight={sliceLabelFont.weight ?? 700}
                fontFamily={sliceLabelFont.family ?? "Montserrat, sans-serif"}
              >
                {showPercent && `${Math.round(slice.percentage * 100)}%`}
                {showValue && !showPercent && slice.value}
              </text>
            )}
          </g>
        );
      })}

      {/* Legend */}
      {showLegend && (
        <g>
          {slices.map((slice, index) => {
            const legendX = legendPosition === "right" ? width * 0.75 : width * 0.1 + index * 150;
            const legendY = legendPosition === "right" ? 200 + index * 50 : height * 0.85;
            
            return (
              <g key={`legend-${index}`}>
                {/* Color box */}
                <rect
                  x={legendX}
                  y={legendY - 12}
                  width={24}
                  height={24}
                  fill={slice.color}
                  rx={4}
                />
                {/* Label */}
                <text
                  x={legendX + 35}
                  y={legendY}
                  dominantBaseline="middle"
                  fill={legendColor}
                  fontSize={legendFont.size ?? 28}
                  fontWeight={legendFont.weight ?? 500}
                  fontFamily={legendFont.family ?? "Inter, sans-serif"}
                >
                  {slice.label}
                </text>
              </g>
            );
          })}
        </g>
      )}
    </svg>
  );
};

