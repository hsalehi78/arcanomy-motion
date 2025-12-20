import { AbsoluteFill, Sequence, Audio, Video, useCurrentFrame } from "remotion";
import { Subtitle } from "../components/typography/Subtitle";
import { COLORS, SIZES } from "../lib/constants";

interface Segment {
  id: number;
  startFrame: number;
  durationFrames: number;
  videoPath: string;
  audioPath: string | null;
  text: string;
  subtitleWords: Array<{
    word: string;
    startFrame: number;
    endFrame: number;
  }>;
}

interface MainReelProps extends Record<string, unknown> {
  totalFrames?: number;
  segments: Segment[];
  musicPath?: string;
  musicVolume?: number;
  colors?: typeof COLORS;
}

export const MainReel: React.FC<MainReelProps> = ({
  segments,
  musicPath,
  musicVolume = 0.3,
  colors = COLORS,
}) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      {/* Background videos for each segment */}
      {segments.map((segment) => (
        <Sequence
          key={`video-${segment.id}`}
          from={segment.startFrame}
          durationInFrames={segment.durationFrames}
        >
          {segment.videoPath && (
            <Video
              src={segment.videoPath}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          )}
        </Sequence>
      ))}

      {/* Voice audio for each segment */}
      {segments.map((segment) => (
        <Sequence
          key={`audio-${segment.id}`}
          from={segment.startFrame}
          durationInFrames={segment.durationFrames}
        >
          {segment.audioPath && <Audio src={segment.audioPath} volume={1} />}
        </Sequence>
      ))}

      {/* Background music */}
      {musicPath && (
        <Audio src={musicPath} volume={musicVolume} />
      )}

      {/* Subtitles */}
      {segments.map((segment) => (
        <Sequence
          key={`subtitle-${segment.id}`}
          from={segment.startFrame}
          durationInFrames={segment.durationFrames}
        >
          <Subtitle
            text={segment.text}
            words={segment.subtitleWords}
            colors={colors}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

