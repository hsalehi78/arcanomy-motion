import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../lib/constants";

interface ShortsProps {
  text: string;
  colors?: typeof COLORS;
}

export const Shorts: React.FC<ShortsProps> = ({
  text,
  colors = COLORS,
}) => {
  const frame = useCurrentFrame();

  // Instant appear (snap in)
  const opacity = frame >= 0 ? 1 : 0;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "10%",
      }}
    >
      <h1
        style={{
          color: colors.textPrimary,
          fontSize: "72px",
          fontWeight: "bold",
          textAlign: "center",
          lineHeight: 1.2,
          opacity,
        }}
      >
        {text}
      </h1>
    </AbsoluteFill>
  );
};

