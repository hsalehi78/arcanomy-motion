import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { MainReel } from "./compositions/MainReel";
import { Shorts } from "./compositions/Shorts";
import { CaptionBurn, CaptionBurnProps } from "./compositions/CaptionBurn";
import { BarChartDemo, BarChartDemoProps } from "./compositions/BarChartDemo";
import { PieChartDemo, PieChartDemoProps } from "./compositions/PieChartDemo";
import { LineChartDemo, LineChartDemoProps } from "./compositions/LineChartDemo";
import { ScatterChartDemo, ScatterChartDemoProps } from "./compositions/ScatterChartDemo";
import { HorizontalBarChartDemo } from "./compositions/HorizontalBarChartDemo";
import { ProgressChartDemo } from "./compositions/ProgressChartDemo";
import { NumberCounterDemo } from "./compositions/NumberCounterDemo";
import { StackedBarChartDemo } from "./compositions/StackedBarChartDemo";
import { HorizontalBarChartProps } from "./components/charts/HorizontalBarChart";
import { ProgressChartProps } from "./components/charts/ProgressChart";
import { NumberCounterProps } from "./components/charts/NumberCounter";
import { StackedBarChartProps } from "./components/charts/StackedBarChart";

type MainReelProps = React.ComponentProps<typeof MainReel>;

const calcMainReelMetadata: CalculateMetadataFunction<MainReelProps> = ({ props }) => {
  const totalFrames =
    typeof (props as any)?.totalFrames === "number"
      ? (props as any).totalFrames
      : Array.isArray((props as any)?.segments)
        ? (props as any).segments.reduce(
            (acc: number, s: any) => acc + (typeof s?.durationFrames === "number" ? s.durationFrames : 0),
            0,
          )
        : 1;

  return {
    durationInFrames: Math.max(1, totalFrames),
    fps: 30,
    width: 1080,
    height: 1920,
    props,
  };
};

const calcCaptionBurnMetadata: CalculateMetadataFunction<CaptionBurnProps> = ({ props }) => {
  const totalFrames =
    typeof (props as any)?.totalFrames === "number"
      ? (props as any).totalFrames
      : Array.isArray((props as any)?.segments)
        ? (props as any).segments.reduce(
            (acc: number, s: any) => acc + (typeof s?.durationFrames === "number" ? s.durationFrames : 0),
            0,
          )
        : 1;

  // Use FPS from props if provided, otherwise default to 30
  const fps = typeof (props as any)?.fps === "number" ? (props as any).fps : 30;

  return {
    durationInFrames: Math.max(1, totalFrames),
    fps,
    width: 1080,
    height: 1920,
    props,
  };
};

// Calculate metadata for BarChartDemo - reads dimensions from props
const calcBarChartDemoMetadata: CalculateMetadataFunction<BarChartDemoProps> = ({ props }) => {
  // Extract dimensions from nested or flat props
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  // Animation settings
  const animDuration = (props as any)?.animation?.duration ?? (props as any)?.animationDuration ?? 45;
  const animStyle = (props as any)?.animation?.style ?? "simultaneous";
  const velocityMode = (props as any)?.animation?.velocityMode ?? false;
  const staggerDelay = (props as any)?.animation?.staggerDelay ?? 8;
  const dataArray = Array.isArray((props as any)?.data) ? (props as any).data : [];
  const dataLength = dataArray.length || 4;
  
  // Calculate max duration (for velocityMode, tallest bar takes longest)
  let maxBarDuration = animDuration;
  if (velocityMode && dataArray.length > 0) {
    const values = dataArray.map((d: any) => d.value || 0);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    // Tallest bar duration = animDuration * (maxValue / minValue)
    maxBarDuration = minValue > 0 ? animDuration * (maxValue / minValue) : animDuration;
  }
  
  // Calculate total duration based on animation style
  let totalAnimDuration = maxBarDuration;
  if (animStyle === "staggered") {
    // For staggered: each bar waits for previous to FINISH
    totalAnimDuration = (dataLength - 1) * (animDuration + staggerDelay) + maxBarDuration;
  } else if (animStyle === "wave") {
    // For wave: bars overlap, each starts staggerDelay after previous
    totalAnimDuration = maxBarDuration + (dataLength - 1) * staggerDelay;
  }
  
  // Add 30 frames after animation for final state display
  // Round to integer (Remotion requires integer duration)
  const durationInFrames = Math.ceil(totalAnimDuration + 30);

  return {
    durationInFrames,
    fps: 30,
    width,
    height,
    props,
  };
};

// Calculate metadata for PieChartDemo
const calcPieChartDemoMetadata: CalculateMetadataFunction<PieChartDemoProps> = ({ props }) => {
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  const animDuration = (props as any)?.animation?.duration ?? 30;
  const animStyle = (props as any)?.animation?.style ?? "simultaneous";
  const staggerDelay = (props as any)?.animation?.staggerDelay ?? 5;
  const dataLength = Array.isArray((props as any)?.data) ? (props as any).data.length : 5;
  
  let totalAnimDuration = animDuration;
  if (animStyle === "sequential") {
    totalAnimDuration = animDuration + (dataLength - 1) * staggerDelay;
  }
  
  const durationInFrames = Math.ceil(totalAnimDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};

// Calculate metadata for LineChartDemo
const calcLineChartDemoMetadata: CalculateMetadataFunction<LineChartDemoProps> = ({ props }) => {
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  const animDuration = (props as any)?.animation?.duration ?? 45;
  const durationInFrames = Math.ceil(animDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};

// Calculate metadata for ScatterChartDemo
const calcScatterChartDemoMetadata: CalculateMetadataFunction<ScatterChartDemoProps> = ({ props }) => {
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  const animDuration = (props as any)?.animation?.duration ?? 30;
  const animStyle = (props as any)?.animation?.style ?? "simultaneous";
  const staggerDelay = (props as any)?.animation?.staggerDelay ?? 3;
  const dataLength = Array.isArray((props as any)?.data) ? (props as any).data.length : 10;
  
  let totalAnimDuration = animDuration;
  if (animStyle === "sequential" || animStyle === "random") {
    totalAnimDuration = animDuration / 2 + (dataLength - 1) * staggerDelay;
  }
  
  const durationInFrames = Math.ceil(totalAnimDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};

// Calculate metadata for HorizontalBarChartDemo
const calcHorizontalBarChartDemoMetadata: CalculateMetadataFunction<HorizontalBarChartProps> = ({ props }) => {
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  const animDuration = (props as any)?.animation?.duration ?? 30;
  const animStyle = (props as any)?.animation?.style ?? "staggered";
  const velocityMode = (props as any)?.animation?.velocityMode ?? false;
  const staggerDelay = (props as any)?.animation?.staggerDelay ?? 0;
  const dataArray = Array.isArray((props as any)?.data) ? (props as any).data : [];
  const dataLength = dataArray.length || 5;
  
  let maxBarDuration = animDuration;
  if (velocityMode && dataArray.length > 0) {
    const values = dataArray.map((d: any) => d.value || 0);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    maxBarDuration = minValue > 0 ? animDuration * (maxValue / minValue) : animDuration;
  }
  
  let totalAnimDuration = maxBarDuration;
  if (animStyle === "staggered") {
    totalAnimDuration = (dataLength - 1) * (animDuration + staggerDelay) + maxBarDuration;
  } else if (animStyle === "wave") {
    totalAnimDuration = maxBarDuration + (dataLength - 1) * staggerDelay;
  }
  
  const durationInFrames = Math.ceil(totalAnimDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};

// Calculate metadata for ProgressChartDemo
const calcProgressChartDemoMetadata: CalculateMetadataFunction<ProgressChartProps> = ({ props }) => {
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  const animDuration = (props as any)?.animation?.duration ?? 45;
  const durationInFrames = Math.ceil(animDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};

// Calculate metadata for NumberCounterDemo
const calcNumberCounterDemoMetadata: CalculateMetadataFunction<NumberCounterProps> = ({ props }) => {
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  const animDuration = (props as any)?.animation?.duration ?? 60;
  const delay = (props as any)?.animation?.delay ?? 0;
  const durationInFrames = Math.ceil(delay + animDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};

// Calculate metadata for StackedBarChartDemo
const calcStackedBarChartDemoMetadata: CalculateMetadataFunction<StackedBarChartProps> = ({ props }) => {
  const width = (props as any)?.dimensions?.width ?? (props as any)?.width ?? 1080;
  const height = (props as any)?.dimensions?.height ?? (props as any)?.height ?? 1080;
  
  const animDuration = (props as any)?.animation?.duration ?? 30;
  const animStyle = (props as any)?.animation?.style ?? "simultaneous";
  const staggerDelay = (props as any)?.animation?.staggerDelay ?? 8;
  const dataLength = Array.isArray((props as any)?.data) ? (props as any).data.length : 4;
  
  let totalAnimDuration = animDuration;
  if (animStyle === "staggered") {
    totalAnimDuration = animDuration + (dataLength - 1) * staggerDelay;
  }
  
  const durationInFrames = Math.ceil(totalAnimDuration + 30);

  return { durationInFrames, fps: 30, width, height, props };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition<MainReelProps, any>
        id="MainReel"
        component={MainReel}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          totalFrames: 1,
          segments: [],
          colors: {
            bg: "#000000",
            bgSecondary: "#0A0A0A",
            textPrimary: "#F5F5F5",
            highlight: "#FFD700",
            chartLine: "#FFB800",
            danger: "#FF3B30",
          },
        }}
        durationInFrames={900}
        calculateMetadata={calcMainReelMetadata}
      />
      <Composition<CaptionBurnProps, any>
        id="CaptionBurn"
        component={CaptionBurn}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          totalFrames: 1,
          baseVideoPath: "",
          segments: [],
        }}
        durationInFrames={300}
        calculateMetadata={calcCaptionBurnMetadata}
      />
      <Composition<React.ComponentProps<typeof Shorts>, any>
        id="Shorts"
        component={Shorts}
        durationInFrames={300} // 10 seconds
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          text: "Your text here",
        }}
      />
      <Composition<BarChartDemoProps, any>
        id="BarChartDemo"
        component={BarChartDemo}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          title: "Monthly Revenue ($K)",
          animationDuration: 45,
          data: [
            { label: "Jan", value: 120 },
            { label: "Feb", value: 85 },
            { label: "Mar", value: 200 },
            { label: "Apr", value: 150 },
            { label: "May", value: 280, color: "#FFD700" },
            { label: "Jun", value: 190 },
          ],
        }}
        calculateMetadata={calcBarChartDemoMetadata}
      />
      <Composition<PieChartDemoProps, any>
        id="PieChartDemo"
        component={PieChartDemo}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          data: [
            { label: "Category A", value: 35 },
            { label: "Category B", value: 25 },
            { label: "Category C", value: 20 },
            { label: "Category D", value: 12 },
            { label: "Others", value: 8 },
          ],
        }}
        calculateMetadata={calcPieChartDemoMetadata}
      />
      <Composition<LineChartDemoProps, any>
        id="LineChartDemo"
        component={LineChartDemo}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          data: [
            { label: "Jan", y: 45 },
            { label: "Feb", y: 52 },
            { label: "Mar", y: 48 },
            { label: "Apr", y: 61 },
            { label: "May", y: 78 },
            { label: "Jun", y: 95 },
          ],
        }}
        calculateMetadata={calcLineChartDemoMetadata}
      />
      <Composition<ScatterChartDemoProps, any>
        id="ScatterChartDemo"
        component={ScatterChartDemo}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          data: [
            { x: 10, y: 150 },
            { x: 20, y: 130 },
            { x: 30, y: 95 },
            { x: 40, y: 70 },
            { x: 50, y: 55 },
          ],
        }}
        calculateMetadata={calcScatterChartDemoMetadata}
      />
      <Composition<HorizontalBarChartProps, any>
        id="HorizontalBarChartDemo"
        component={HorizontalBarChartDemo}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          data: [
            { label: "United States", value: 28.78, color: "#4ECDC4" },
            { label: "China", value: 18.53, color: "#FF6B6B" },
            { label: "Germany", value: 4.59, color: "#FFE66D" },
            { label: "Japan", value: 4.11, color: "#C44DFF" },
            { label: "India", value: 3.94, color: "#00D4FF" },
          ],
        }}
        calculateMetadata={calcHorizontalBarChartDemoMetadata}
      />
      <Composition<ProgressChartProps, any>
        id="ProgressChartDemo"
        component={ProgressChartDemo}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          value: 85,
          maxValue: 100,
          format: "percent",
        }}
        calculateMetadata={calcProgressChartDemoMetadata}
      />
      <Composition<NumberCounterProps, any>
        id="NumberCounterDemo"
        component={NumberCounterDemo}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          value: 1250000,
          prefix: "$",
          useLocale: true,
        }}
        calculateMetadata={calcNumberCounterDemoMetadata}
      />
      <Composition<StackedBarChartProps, any>
        id="StackedBarChartDemo"
        component={StackedBarChartDemo}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          mode: "stacked",
          series: [
            { name: "North America", color: "#4ECDC4" },
            { name: "Europe", color: "#FF6B6B" },
            { name: "Asia Pacific", color: "#FFE66D" },
          ],
          data: [
            { label: "Q1", values: [45, 32, 28] },
            { label: "Q2", values: [52, 38, 35] },
            { label: "Q3", values: [48, 42, 40] },
            { label: "Q4", values: [62, 48, 52] },
          ],
        }}
        calculateMetadata={calcStackedBarChartDemoMetadata}
      />
    </>
  );
};

