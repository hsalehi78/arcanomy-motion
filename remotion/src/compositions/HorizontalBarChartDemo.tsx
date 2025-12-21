/**
 * HorizontalBarChartDemo Composition
 * 
 * Wrapper for the HorizontalBarChart component that accepts all props
 * and passes them through for Remotion rendering.
 */

import { HorizontalBarChart, HorizontalBarChartProps } from "../components/charts/HorizontalBarChart";

export const HorizontalBarChartDemo: React.FC<HorizontalBarChartProps> = (props) => {
  return <HorizontalBarChart {...props} />;
};

