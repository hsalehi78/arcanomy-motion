/**
 * BarChart Component - Comprehensive animated bar chart for Remotion
 * 
 * This component renders a fully customizable vertical bar chart with:
 * - Animated bar entrance (grows from bottom)
 * - Customizable colors, fonts, margins
 * - Title and subtitle support
 * - Grid lines and axis labels
 * - Data labels above bars
 * 
 * Props can be provided in two formats:
 * 1. Flat format: { title: "...", width: 1080, ... }
 * 2. Nested format: { title: { text: "...", font: {...} }, dimensions: {...} }
 * 
 * The component handles both for backwards compatibility.
 */

import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS, ANIMATION } from "../../lib/constants";

// =============================================================================
// GOOGLE FONTS IMPORT URL
// =============================================================================

/**
 * Google Fonts CSS import URL for Arcanomy brand fonts
 * Montserrat: Bold headlines, data labels
 * Inter: Clean body text, axis labels
 */
const GOOGLE_FONTS_IMPORT = `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=Montserrat:wght@400;500;700&display=swap');`;

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * Single data point for the bar chart
 * @property label - Category name shown on x-axis (e.g., "North", "Q1")
 * @property value - Numeric value determining bar height
 * @property color - Optional hex color override for this specific bar
 */
export interface BarData {
  label: string;
  value: number;
  color?: string;
}

/**
 * Font configuration for text elements
 * @property family - Font family name (e.g., "Inter", "Arial")
 * @property size - Font size in pixels
 * @property weight - Font weight (400 = normal, 700 = bold)
 */
export interface FontConfig {
  family?: string;
  size?: number;
  weight?: number;
}

/**
 * Margin/padding configuration
 * @property top - Space above the chart area (for title)
 * @property right - Space to the right of the chart
 * @property bottom - Space below the chart (for x-axis labels)
 * @property left - Space to the left of the chart (for y-axis labels)
 */
export interface MarginConfig {
  top?: number;
  right?: number;
  bottom?: number;
  left?: number;
}

/**
 * Comprehensive props for the BarChart component
 * Supports both flat props and nested configuration objects
 */
export interface BarChartProps {
  /** Required: Array of data points to render as bars */
  data: BarData[];
  
  // -------------------------------------------------------------------------
  // Dimensions - Chart size and spacing
  // -------------------------------------------------------------------------
  
  /** Nested dimensions config (preferred for v2.0 schema) */
  dimensions?: {
    width?: number;
    height?: number;
    margin?: MarginConfig;
  };
  
  /** Flat width prop (legacy, for backwards compatibility) */
  width?: number;
  /** Flat height prop (legacy, for backwards compatibility) */
  height?: number;
  
  // -------------------------------------------------------------------------
  // Background
  // -------------------------------------------------------------------------
  
  /** Background configuration */
  background?: {
    color?: string;  // Hex color for background (e.g., "#000000")
  };
  
  // -------------------------------------------------------------------------
  // Title - Main heading at top of chart
  // -------------------------------------------------------------------------
  
  /** 
   * Title can be a simple string or object with styling options
   * String: "My Chart Title"
   * Object: { text: "My Chart", font: { size: 48 }, color: "#FFF", show: true, y: 60 }
   */
  title?: string | {
    show?: boolean;   // Toggle title visibility on/off (default: true)
    text?: string;
    y?: number;       // Explicit Y position from top in pixels
    font?: FontConfig;
    color?: string;
  };
  
  // -------------------------------------------------------------------------
  // Subtitle - Secondary heading below title
  // -------------------------------------------------------------------------
  
  /** Subtitle configuration (typically units or context) */
  subtitle?: {
    show?: boolean;     // Toggle subtitle visibility on/off (default: true)
    text?: string;      // Subtitle text (e.g., "Revenue in $K")
    y?: number;         // Explicit Y position from top in pixels
    font?: FontConfig;  // Font styling
    color?: string;     // Text color
  };
  
  // -------------------------------------------------------------------------
  // X-Axis - Category labels below bars
  // -------------------------------------------------------------------------
  
  /** X-axis configuration */
  xAxis?: {
    show?: boolean;       // Toggle x-axis labels visibility (default: true)
    label?: {
      font?: FontConfig;  // Font for category labels
      color?: string;     // Label color
    };
  };
  
  // -------------------------------------------------------------------------
  // Y-Axis - Value scale on left side
  // -------------------------------------------------------------------------
  
  /** Y-axis configuration */
  yAxis?: {
    show?: boolean;       // Toggle y-axis labels visibility (default: true)
    label?: {
      font?: FontConfig;  // Font for value labels
      color?: string;     // Label color
    };
    gridLines?: {
      show?: boolean;   // Whether to show horizontal grid lines
      color?: string;   // Grid line color
    };
  };
  
  // -------------------------------------------------------------------------
  // Bars - Bar styling
  // -------------------------------------------------------------------------
  
  /** Bar styling configuration */
  bars?: {
    gap?: number;          // Space between bars in pixels
    cornerRadius?: number; // Rounded corner radius (0 for square)
    defaultColor?: string; // Default bar color if not set per-item
  };
  
  // -------------------------------------------------------------------------
  // Data Labels - Values shown above bars
  // -------------------------------------------------------------------------
  
  /** Data label configuration (values on/near bars) */
  dataLabels?: {
    show?: boolean;       // Whether to show value labels
    position?: "above" | "inside-top" | "inside-middle" | "inside-bottom";  // Label position
    font?: FontConfig;    // Font for value labels
    color?: string;       // Label color
  };
  
  // -------------------------------------------------------------------------
  // Animation
  // -------------------------------------------------------------------------
  
  /** Animation configuration */
  animation?: {
    duration?: number;  // Duration per bar in frames (30 = 1 sec at 30fps)
    style?: "simultaneous" | "staggered" | "wave";  // Animation style
    velocityMode?: boolean;  // true = taller bars take longer (proportional), false = all finish together
    staggerDelay?: number;  // Frames between each bar start (for staggered/wave)
    direction?: "left-to-right" | "right-to-left" | "center-out" | "random";
  };
  
  // -------------------------------------------------------------------------
  // Legacy flat props (for backwards compatibility)
  // -------------------------------------------------------------------------
  
  animationDuration?: number;  // Legacy: use animation.duration instead
  barGap?: number;             // Legacy: use bars.gap instead
  showLabels?: boolean;        // Whether to show x-axis labels
  showValues?: boolean;        // Legacy: use dataLabels.show instead
  colors?: typeof COLORS;      // Legacy color palette
}

// =============================================================================
// COMPONENT
// =============================================================================

export const BarChart: React.FC<BarChartProps> = (props) => {
  // Get current animation frame from Remotion
  const frame = useCurrentFrame();
  const { data } = props;

  // Early return if no data provided
  if (!data || data.length === 0) return null;

  // ==========================================================================
  // PROP EXTRACTION
  // Extract values from nested or flat props with sensible defaults
  // This allows the component to accept both v1 (flat) and v2 (nested) schemas
  // ==========================================================================
  
  // --- Dimensions ---
  // Priority: nested dimensions > flat props > defaults
  const width = props.dimensions?.width ?? props.width ?? 1080;
  const height = props.dimensions?.height ?? props.height ?? 1920;
  const margin: MarginConfig = {
    top: props.dimensions?.margin?.top ?? 120,      // Space for title
    right: props.dimensions?.margin?.right ?? 60,   // Right padding
    bottom: props.dimensions?.margin?.bottom ?? 200, // Space for x-axis labels
    left: props.dimensions?.margin?.left ?? 80,      // Space for y-axis labels
  };

  // --- Background ---
  const bgColor = props.background?.color ?? props.colors?.bg ?? COLORS.bg;

  // --- Title ---
  // Handle both string and object formats
  const showTitle = typeof props.title === "object" 
    ? props.title?.show ?? true 
    : true;
  const titleText = typeof props.title === "string" 
    ? props.title 
    : props.title?.text ?? "";
  const titleExplicitY = typeof props.title === "object" 
    ? props.title?.y 
    : undefined;
  const titleFont: FontConfig = typeof props.title === "object" 
    ? props.title?.font ?? {} 
    : {};
  const titleColor = typeof props.title === "object" 
    ? props.title?.color 
    : props.colors?.textPrimary ?? COLORS.textPrimary;

  // --- Subtitle ---
  const showSubtitle = props.subtitle?.show ?? true;
  const subtitleText = props.subtitle?.text ?? "";
  const subtitleExplicitY = props.subtitle?.y;
  const subtitleFont = props.subtitle?.font ?? {};
  const subtitleColor = props.subtitle?.color ?? "#888888";

  // --- X-Axis Labels Visibility ---
  const showXAxisLabels = props.xAxis?.show ?? props.showLabels ?? true;

  // --- Y-Axis Visibility ---
  const showYAxisLabels = props.yAxis?.show ?? true;

  // --- X-Axis Labels ---
  const xLabelFont = props.xAxis?.label?.font ?? {};
  const xLabelColor = props.xAxis?.label?.color ?? props.colors?.textPrimary ?? COLORS.textPrimary;

  // --- Y-Axis ---
  const yLabelFont = props.yAxis?.label?.font ?? {};
  const yLabelColor = props.yAxis?.label?.color ?? "#888888";
  const showGridLines = props.yAxis?.gridLines?.show ?? true;
  const gridLineColor = props.yAxis?.gridLines?.color ?? "#222222";

  // --- Bars ---
  const barGap = props.bars?.gap ?? props.barGap ?? 24;
  const cornerRadius = props.bars?.cornerRadius ?? 6;
  const defaultBarColor = props.bars?.defaultColor ?? props.colors?.highlight ?? COLORS.highlight;

  // --- Data Labels ---
  const showDataLabels = props.dataLabels?.show ?? props.showValues ?? true;
  const dataLabelPosition = props.dataLabels?.position ?? "above";  // above, inside-top, inside-middle, inside-bottom
  const dataLabelFont = props.dataLabels?.font ?? {};
  const dataLabelColor = props.dataLabels?.color ?? props.colors?.textPrimary ?? COLORS.textPrimary;

  // --- Animation ---
  const animationDuration = props.animation?.duration ?? props.animationDuration ?? ANIMATION.chartDrawDuration;
  const animationStyle = props.animation?.style ?? "simultaneous";
  const velocityMode = props.animation?.velocityMode ?? false;
  const staggerDelay = props.animation?.staggerDelay ?? 8;
  const animationDirection = props.animation?.direction ?? "left-to-right";

  // ==========================================================================
  // LAYOUT CALCULATIONS
  // ==========================================================================
  
  // Calculate the drawable chart area (inside margins)
  const chartWidth = width - (margin.left ?? 0) - (margin.right ?? 0);
  const chartHeight = height - (margin.top ?? 0) - (margin.bottom ?? 0);
  
  // Find the maximum value to scale bars proportionally
  const maxValue = Math.max(...data.map((d) => d.value));
  
  // Calculate individual bar width based on chart width and gaps
  const barWidth = (chartWidth - barGap * (data.length - 1)) / data.length;

  // ==========================================================================
  // ANIMATION - Per-bar progress calculation
  // ==========================================================================
  
  /**
   * Calculate animation progress for each bar based on style
   * @param barIndex - Index of the bar (0 to data.length-1)
   * @returns Progress value from 0 to 1
   */
  const getBarProgress = (barIndex: number): number => {
    // Calculate the animation order based on direction
    let orderIndex = barIndex;
    if (animationDirection === "right-to-left") {
      orderIndex = data.length - 1 - barIndex;
    } else if (animationDirection === "center-out") {
      const center = (data.length - 1) / 2;
      orderIndex = Math.abs(barIndex - center);
    } else if (animationDirection === "random") {
      // Use a deterministic "random" based on index
      orderIndex = [2, 0, 3, 1, 4, 5, 6, 7][barIndex % 8];
    }

    // Calculate this bar's duration based on velocityMode
    // velocityMode: true = taller bars take longer (same speed, more distance)
    // velocityMode: false = all bars take the same time
    const barValue = data[barIndex].value;
    const minValue = Math.min(...data.map(d => d.value));
    const barDuration = velocityMode 
      ? animationDuration * (barValue / minValue)  // Taller bars take longer (30 frames = shortest bar)
      : animationDuration;                          // Fixed duration for all

    if (animationStyle === "simultaneous") {
      // All bars animate together at the same time
      return interpolate(
        frame,
        [0, barDuration],
        [0, 1],
        { extrapolateRight: "clamp" }
      );
    } else if (animationStyle === "staggered") {
      // Each bar starts AFTER the previous one FINISHES
      // startFrame = (bar index) * (duration + extra delay)
      const startFrame = orderIndex * (animationDuration + staggerDelay);
      return interpolate(
        frame,
        [startFrame, startFrame + barDuration],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
    } else if (animationStyle === "wave") {
      // Bars overlap - each starts slightly after previous (only staggerDelay apart)
      const startFrame = orderIndex * staggerDelay;
      return interpolate(
        frame,
        [startFrame, startFrame + barDuration],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
    }
    return 1;
  };

  // For non-bar elements, use overall progress
  const overallProgress = interpolate(
    frame,
    [0, animationDuration + (data.length - 1) * staggerDelay],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  // Calculate title and subtitle positions
  // Use explicit Y if provided, otherwise center in top margin
  const titleY = titleExplicitY ?? (margin.top ?? 120) / 2;
  const subtitleY = subtitleExplicitY ?? titleY + (titleFont.size ?? 48) + 20;

  // #region agent log
  if (frame === 0) {
    fetch('http://127.0.0.1:7246/ingest/f8eaf619-5d68-4d81-81c1-828880c224eb',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'BarChart.tsx:ANIMATION',message:'Animation settings',data:{animationStyle,animationDuration,velocityMode,staggerDelay,animationDirection,barCount:data.length,maxValue,barValues:data.map(d=>d.value)},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'H4-velocity'})}).catch(()=>{});
  }
  // #endregion

  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <svg width={width} height={height}>
      {/* Google Fonts import for Montserrat and Inter */}
      <defs>
        <style>{GOOGLE_FONTS_IMPORT}</style>
      </defs>
      
      {/* Background rectangle - fills entire canvas */}
      <rect width={width} height={height} fill={bgColor} />

      {/* Title - centered at top (only if show=true and has text) */}
      {showTitle && titleText && (
        <text
          x={width / 2}
          y={titleY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={titleColor}
          fontSize={titleFont.size ?? 48}
          fontWeight={titleFont.weight ?? 700}
          fontFamily={titleFont.family ?? "Montserrat, Inter, system-ui, sans-serif"}
        >
          {titleText}
        </text>
      )}

      {/* Subtitle - centered below title (only if show=true and has text) */}
      {showSubtitle && subtitleText && (
        <text
          x={width / 2}
          y={subtitleY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={subtitleColor}
          fontSize={subtitleFont.size ?? 24}
          fontWeight={subtitleFont.weight ?? 400}
          fontFamily={subtitleFont.family ?? "Inter, system-ui, sans-serif"}
        >
          {subtitleText}
        </text>
      )}

      {/* Horizontal grid lines - help read bar values */}
      {showGridLines && (
        <g stroke={gridLineColor} strokeWidth={1} opacity={0.5}>
          {/* Draw 5 grid lines at 0%, 25%, 50%, 75%, 100% of max value */}
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

      {/* Y-Axis labels - value scale on left side (only if show=true) */}
      {showYAxisLabels && (
        <g>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <text
              key={`y-label-${ratio}`}
              x={(margin.left ?? 0) - 10}
              y={(margin.top ?? 0) + chartHeight * (1 - ratio)}
              textAnchor="end"
              dominantBaseline="middle"
              fill={yLabelColor}
              fontSize={yLabelFont.size ?? 16}
              fontWeight={yLabelFont.weight ?? 400}
              fontFamily={yLabelFont.family ?? "Inter, system-ui, sans-serif"}
              opacity={overallProgress}  // Fade in with animation
            >
              {Math.round(maxValue * ratio)}
            </text>
          ))}
        </g>
      )}

      {/* Bars and their labels */}
      {data.map((item, index) => {
        // Get per-bar animation progress (supports staggered animation)
        const barProgress = getBarProgress(index);
        
        // Calculate bar dimensions - height animated based on per-bar progress
        const barHeight = (item.value / maxValue) * chartHeight * barProgress;
        const x = (margin.left ?? 0) + index * (barWidth + barGap);
        const y = (margin.top ?? 0) + chartHeight - barHeight;

        return (
          <g key={index}>
            {/* The bar itself */}
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={Math.max(0, barHeight)}  // Prevent negative height
              fill={item.color || defaultBarColor}  // Use item color or default
              rx={cornerRadius}  // Rounded corners
              ry={cornerRadius}
            />

            {/* Value label - position based on dataLabelPosition setting */}
            {showDataLabels && barProgress >= 1 && (() => {
              // Calculate Y position based on dataLabelPosition
              // above: outside bar, above it
              // inside-top: inside bar, near top
              // inside-middle: inside bar, vertically centered
              // inside-bottom: inside bar, near bottom
              let labelY = y - 15;  // default: above
              if (dataLabelPosition === "inside-top") {
                labelY = y + 30;
              } else if (dataLabelPosition === "inside-middle") {
                labelY = y + barHeight / 2;
              } else if (dataLabelPosition === "inside-bottom") {
                labelY = y + barHeight - 15;
              }
              
              return (
                <text
                  x={x + barWidth / 2}
                  y={labelY}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill={dataLabelColor}
                  fontSize={dataLabelFont.size ?? 20}
                  fontWeight={dataLabelFont.weight ?? 700}
                  fontFamily={dataLabelFont.family ?? "Montserrat, Inter, system-ui, sans-serif"}
                >
                  {item.value}
                </text>
              );
            })()}

            {/* X-Axis category label below bar (only if show=true) */}
            {showXAxisLabels && (
              <text
                x={x + barWidth / 2}
                y={height - (margin.bottom ?? 0) + 40}
                textAnchor="middle"
                fill={xLabelColor}
                fontSize={xLabelFont.size ?? 18}
                fontWeight={xLabelFont.weight ?? 500}
                fontFamily={xLabelFont.family ?? "Inter, system-ui, sans-serif"}
                opacity={barProgress}  // Fade in with this bar's animation
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
