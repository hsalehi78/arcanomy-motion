import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { MainReel } from "./compositions/MainReel";
import { Shorts } from "./compositions/Shorts";
import { CaptionBurn, CaptionBurnProps } from "./compositions/CaptionBurn";

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

  return {
    durationInFrames: Math.max(1, totalFrames),
    fps: 30,
    width: 1080,
    height: 1920,
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
    </>
  );
};

