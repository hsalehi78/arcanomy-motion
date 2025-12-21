/**
 * ScatterChartDemo Composition
 * 
 * This composition wraps the ScatterChart component and passes through
 * all props from the JSON file. It serves as the entry point for
 * Remotion rendering.
 */

import React from "react";
import { AbsoluteFill } from "remotion";
import { ScatterChart, ScatterChartProps } from "../components/charts";

/**
 * Props for ScatterChartDemo - extends ScatterChartProps to accept all chart options
 */
export interface ScatterChartDemoProps extends ScatterChartProps, Record<string, unknown> {}

export const ScatterChartDemo: React.FC<ScatterChartDemoProps> = (props) => {
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
      <ScatterChart {...props} />
    </AbsoluteFill>
  );
};

