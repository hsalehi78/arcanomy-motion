/**
 * PieChartDemo Composition
 * 
 * This composition wraps the PieChart component and passes through
 * all props from the JSON file. It serves as the entry point for
 * Remotion rendering.
 */

import React from "react";
import { AbsoluteFill } from "remotion";
import { PieChart, PieChartProps } from "../components/charts";

/**
 * Props for PieChartDemo - extends PieChartProps to accept all chart options
 */
export interface PieChartDemoProps extends PieChartProps, Record<string, unknown> {}

export const PieChartDemo: React.FC<PieChartDemoProps> = (props) => {
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
      <PieChart {...props} />
    </AbsoluteFill>
  );
};

