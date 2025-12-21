/**
 * LineChartDemo Composition
 * 
 * This composition wraps the LineChart component and passes through
 * all props from the JSON file. It serves as the entry point for
 * Remotion rendering.
 */

import React from "react";
import { AbsoluteFill } from "remotion";
import { LineChart, LineChartProps } from "../components/charts";

/**
 * Props for LineChartDemo - extends LineChartProps to accept all chart options
 */
export interface LineChartDemoProps extends LineChartProps, Record<string, unknown> {}

export const LineChartDemo: React.FC<LineChartDemoProps> = (props) => {
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
      <LineChart {...props} />
    </AbsoluteFill>
  );
};

