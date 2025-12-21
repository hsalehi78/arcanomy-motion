// =============================================================================
// CHART COMPONENT EXPORTS
// =============================================================================
// Export all chart components and their type definitions for use in compositions.

// Standard vertical bar chart
export { BarChart } from "./BarChart";
export type { BarChartProps, BarData } from "./BarChart";

// Horizontal bar chart (for rankings, leaderboards)
export { HorizontalBarChart } from "./HorizontalBarChart";
export type { HorizontalBarChartProps, HorizontalBarData } from "./HorizontalBarChart";

// Stacked/grouped bar chart (multi-series)
export { StackedBarChart } from "./StackedBarChart";
export type { StackedBarChartProps, StackedBarDataPoint, StackedBarSeries } from "./StackedBarChart";

// Line chart (trends over time)
export { LineChart } from "./LineChart";
export type { LineChartProps, LineDataPoint } from "./LineChart";

// Pie/donut chart (proportions)
export { PieChart } from "./PieChart";
export type { PieChartProps, PieData } from "./PieChart";

// Scatter chart (correlations, distributions)
export { ScatterChart } from "./ScatterChart";
export type { ScatterChartProps, ScatterDataPoint } from "./ScatterChart";

// Progress/gauge chart (single percentage)
export { ProgressChart } from "./ProgressChart";
export type { ProgressChartProps } from "./ProgressChart";

// Number counter (animated counting)
export { NumberCounter } from "./NumberCounter";
export type { NumberCounterProps } from "./NumberCounter";
