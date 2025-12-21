/**
 * ProgressChartDemo Composition
 * 
 * Wrapper for the ProgressChart component that accepts all props
 * and passes them through for Remotion rendering.
 */

import { ProgressChart, ProgressChartProps } from "../components/charts/ProgressChart";

export const ProgressChartDemo: React.FC<ProgressChartProps> = (props) => {
  return <ProgressChart {...props} />;
};

