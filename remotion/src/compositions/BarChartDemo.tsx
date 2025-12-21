import React from "react";
import { AbsoluteFill } from "remotion";
import { BarChart, BarData } from "../components/charts";
import { COLORS } from "../lib/constants";

export interface BarChartDemoProps extends Record<string, unknown> {
  data: BarData[];
  title?: string;
  animationDuration?: number;
}

export const BarChartDemo: React.FC<BarChartDemoProps> = ({
  data,
  title = "Sample Chart",
  animationDuration = 45,
}) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Chart */}
      <BarChart
        data={data}
        width={900}
        height={600}
        animationDuration={animationDuration}
        title={title}
      />
    </AbsoluteFill>
  );
};

