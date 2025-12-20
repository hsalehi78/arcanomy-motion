import { useCurrentFrame } from "remotion";
import { COLORS } from "../../lib/constants";

interface SubtitleWord {
  word: string;
  startFrame: number;
  endFrame: number;
}

interface SubtitleProps {
  text: string;
  words?: SubtitleWord[];
  colors?: typeof COLORS;
}

export const Subtitle: React.FC<SubtitleProps> = ({
  text,
  words = [],
  colors = COLORS,
}) => {
  const frame = useCurrentFrame();

  // Shorts-optimized subtitle styling (TikTok/IG/Shorts):
  // - High contrast pill
  // - Large, bold-enough text
  // - Explicit font stack (consistent cross-platform)
  const fontFamily =
    '"Inter", "SF Pro Display", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif';

  // Responsive sizing for 1080x1920. (42px was too small on mobile.)
  // Keep it large but not absurdly huge; karaoke pill can be ~8% height overall.
  const fontSizePx = 86;
  const lineHeight = 1.12;

  const outerStyle: React.CSSProperties = {
    position: "absolute",
    // Keep above platform UI / captions area (bottom ~15% reserved).
    bottom: "20%",
    left: "10%",
    right: "10%",
    display: "flex",
    justifyContent: "center",
    pointerEvents: "none",
  };

  const pillStyle: React.CSSProperties = {
    backgroundColor: "rgba(0, 0, 0, 0.78)",
    padding: "18px 28px",
    borderRadius: "14px",
    boxShadow: "0 14px 40px rgba(0, 0, 0, 0.55)",
    backdropFilter: "blur(6px)",
    maxWidth: "80%",
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: "10px",
  };

  const baseTextStyle: React.CSSProperties = {
    fontFamily,
    fontSize: `${fontSizePx}px`,
    lineHeight,
    letterSpacing: "-0.02em",
    textAlign: "center",
    color: colors.textPrimary,
    fontWeight: 600,
    textShadow:
      "0 3px 10px rgba(0,0,0,0.85), 0 1px 0 rgba(0,0,0,0.7), 0 0 20px rgba(0,0,0,0.35)",
    WebkitTextStroke: "1px rgba(0,0,0,0.35)",
  };

  // If no word-level timing, just show the full text
  if (words.length === 0) {
    return (
      <div style={outerStyle}>
        <div style={pillStyle}>
          <span style={baseTextStyle}>{text}</span>
        </div>
      </div>
    );
  }

  // Karaoke-style highlighting
  return (
    <div style={outerStyle}>
      <div style={pillStyle}>
        {words.map((word, index) => {
          const isActive = frame >= word.startFrame && frame < word.endFrame;

          return (
            <span
              key={index}
              style={{
                ...baseTextStyle,
                color: isActive ? colors.highlight : colors.textPrimary,
                fontWeight: isActive ? 800 : baseTextStyle.fontWeight,
                transform: isActive ? "scale(1.12)" : "scale(1)",
                transition: "transform 0.08s linear, color 0.08s linear",
              }}
            >
              {word.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};

