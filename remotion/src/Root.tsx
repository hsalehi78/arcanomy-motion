import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { MainReel } from "./compositions/MainReel";
import { Shorts } from "./compositions/Shorts";
import { CaptionBurn, CaptionBurnProps } from "./compositions/CaptionBurn";
import { BarChartDemo, BarChartDemoProps } from "./compositions/BarChartDemo";

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
    </>
  );
};

