import React from "react";
import { AbsoluteFill, Sequence, Video } from "remotion";
import { Subtitle } from "../components/typography/Subtitle";
import { COLORS } from "../lib/constants";

type SubtitleWord = {
  word: string;
  startFrame: number;
  endFrame: number;
};

type Segment = {
  id: number;
  startFrame: number;
  durationFrames: number;
  text: string;
  subtitleWords: SubtitleWord[];
};

export type CaptionBurnProps = Record<string, unknown> & {
  totalFrames?: number;
  baseVideoPath: string;
  segments: Segment[];
  colors?: typeof COLORS;
};

export const CaptionBurn: React.FC<CaptionBurnProps> = ({
  baseVideoPath,
  segments,
  colors = COLORS,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      <Video
        src={baseVideoPath}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      {segments.map((segment) => (
        <Sequence
          key={`subtitle-${segment.id}`}
          from={segment.startFrame}
          durationInFrames={segment.durationFrames}
        >
          <Subtitle text={segment.text} words={segment.subtitleWords} colors={colors} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};


