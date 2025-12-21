/**
 * StackedBarChartDemo Composition
 * 
 * Wrapper for the StackedBarChart component that accepts all props
 * and passes them through for Remotion rendering.
 */

import { StackedBarChart, StackedBarChartProps } from "../components/charts/StackedBarChart";

export const StackedBarChartDemo: React.FC<StackedBarChartProps> = (props) => {
  return <StackedBarChart {...props} />;
};

