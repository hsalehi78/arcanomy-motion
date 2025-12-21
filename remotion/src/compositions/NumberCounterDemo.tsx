/**
 * NumberCounterDemo Composition
 * 
 * Wrapper for the NumberCounter component that accepts all props
 * and passes them through for Remotion rendering.
 */

import { NumberCounter, NumberCounterProps } from "../components/charts/NumberCounter";

export const NumberCounterDemo: React.FC<NumberCounterProps> = (props) => {
  return <NumberCounter {...props} />;
};

