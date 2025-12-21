/**
 * NumberCounter Component - Animated counting number for Remotion
 * 
 * Perfect for:
 * - Big number reveals ("Revenue hit $1.2M")
 * - Counting up animations
 * - Key statistics and metrics
 * 
 * Shows a number that counts up from 0 (or startValue) to the target value.
 */

import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../../lib/constants";

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

export interface NumberCounterProps {
  /** The target value to count to */
  value: number;
  
  /** Starting value (default 0) */
  startValue?: number;
  
  /** Prefix (e.g., "$", "€", "#") */
  prefix?: string;
  
  /** Suffix (e.g., "K", "M", "%", "+") */
  suffix?: string;
  
  /** Decimal places to show */
  decimals?: number;
  
  /** Use locale formatting (commas for thousands) */
  useLocale?: boolean;
  
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
    position?: "above" | "below";
    font?: FontConfig;
    color?: string;
  };
  
  subtitle?: {
    show?: boolean;
    text?: string;
    font?: FontConfig;
    color?: string;
  };
  
  /** Main number styling */
  number?: {
    font?: FontConfig;
    color?: string;
  };
  
  animation?: {
    duration?: number;
    easing?: "linear" | "ease-out" | "ease-in-out";
    delay?: number;  // Frames to wait before starting
  };
}

// =============================================================================
// COMPONENT
// =============================================================================

export const NumberCounter: React.FC<NumberCounterProps> = (props) => {
  const frame = useCurrentFrame();
  
  const targetValue = props.value ?? 0;
  const startValue = props.startValue ?? 0;
  const prefix = props.prefix ?? "";
  const suffix = props.suffix ?? "";
  const decimals = props.decimals ?? 0;
  const useLocale = props.useLocale ?? true;

  // ==========================================================================
  // PROP EXTRACTION
  // ==========================================================================
  
  const width = props.dimensions?.width ?? props.width ?? 1080;
  const height = props.dimensions?.height ?? props.height ?? 1080;
  const bgColor = props.background?.color ?? COLORS.bg;
  
  // Title
  const showTitle = props.title?.show ?? true;
  const titleText = props.title?.text ?? "";
  const titlePosition = props.title?.position ?? "above";
  const titleFont = props.title?.font ?? {};
  const titleColor = props.title?.color ?? "#888888";
  
  // Subtitle
  const showSubtitle = props.subtitle?.show ?? false;
  const subtitleText = props.subtitle?.text ?? "";
  const subtitleFont = props.subtitle?.font ?? {};
  const subtitleColor = props.subtitle?.color ?? "#666666";
  
  // Number
  const numberFont = props.number?.font ?? {};
  const numberColor = props.number?.color ?? COLORS.highlight;
  
  // Animation
  const animationDuration = props.animation?.duration ?? 60;
  const delay = props.animation?.delay ?? 0;
  const easing = props.animation?.easing ?? "ease-out";

  // ==========================================================================
  // CALCULATIONS
  // ==========================================================================
  
  const centerX = width / 2;
  const centerY = height / 2;
  
  // Apply easing
  let progress: number;
  if (easing === "ease-out") {
    const t = interpolate(frame, [delay, delay + animationDuration], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    progress = 1 - Math.pow(1 - t, 3);  // Cubic ease-out
  } else if (easing === "ease-in-out") {
    const t = interpolate(frame, [delay, delay + animationDuration], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    progress = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;  // Cubic ease-in-out
  } else {
    progress = interpolate(frame, [delay, delay + animationDuration], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }
  
  // Calculate current value
  const currentValue = startValue + (targetValue - startValue) * progress;
  
  // Format the number
  let formattedNumber: string;
  if (decimals > 0) {
    formattedNumber = currentValue.toFixed(decimals);
    if (useLocale) {
      const parts = formattedNumber.split(".");
      parts[0] = parseInt(parts[0]).toLocaleString();
      formattedNumber = parts.join(".");
    }
  } else {
    const rounded = Math.round(currentValue);
    formattedNumber = useLocale ? rounded.toLocaleString() : rounded.toString();
  }
  
  const displayText = `${prefix}${formattedNumber}${suffix}`;
  
  // Calculate positions
  const numberSize = numberFont.size ?? 160;
  const titleSize = titleFont.size ?? 42;
  const numberY = titlePosition === "above" && showTitle && titleText
    ? centerY + 30
    : centerY;
  const titleY = titlePosition === "above"
    ? numberY - numberSize / 2 - 50
    : numberY + numberSize / 2 + 60;

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
          fontSize={titleSize}
          fontWeight={titleFont.weight ?? 500}
          fontFamily={titleFont.family ?? "Inter, sans-serif"}
        >
          {titleText}
        </text>
      )}

      {/* Main Number */}
      <text
        x={centerX}
        y={numberY}
        textAnchor="middle"
        dominantBaseline="middle"
        fill={numberColor}
        fontSize={numberSize}
        fontWeight={numberFont.weight ?? 700}
        fontFamily={numberFont.family ?? "Montserrat, sans-serif"}
      >
        {displayText}
      </text>

      {/* Subtitle */}
      {showSubtitle && subtitleText && (
        <text
          x={centerX}
          y={height - 150}
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

