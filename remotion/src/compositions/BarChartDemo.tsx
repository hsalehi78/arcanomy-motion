/**
 * BarChartDemo Composition
 * 
 * This composition wraps the BarChart component and passes through
 * all props from the JSON file. It serves as the entry point for
 * Remotion rendering.
 * 
 * All props from the JSON are passed directly to BarChart, allowing
 * full customization of dimensions, fonts, colors, and styling.
 */

import React from "react";
import { AbsoluteFill } from "remotion";
import { BarChart, BarChartProps } from "../components/charts";

/**
 * Props for BarChartDemo - extends BarChartProps to accept all chart options
 * Record<string, unknown> allows additional props to pass through
 */
export interface BarChartDemoProps extends BarChartProps, Record<string, unknown> {}

export const BarChartDemo: React.FC<BarChartDemoProps> = (props) => {
  // Extract dimensions for the container, with defaults
  const width = props.dimensions?.width ?? props.width ?? 1080;
  const height = props.dimensions?.height ?? props.height ?? 1080;
  const bgColor = props.background?.color ?? "#000000";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bgColor,
        width,
        height,
      }}
    >
      {/* Pass ALL props directly to BarChart */}
      <BarChart {...props} />
    </AbsoluteFill>
  );
};
