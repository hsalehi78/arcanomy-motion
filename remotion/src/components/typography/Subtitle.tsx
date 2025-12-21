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

// Number of words to show in the sliding window (on each side of active word)
const WINDOW_SIZE = 2; // Shows ~5 words total: 2 before + active + 2 after

export const Subtitle: React.FC<SubtitleProps> = ({
  text,
  words = [],
  colors = COLORS,
}) => {
  const frame = useCurrentFrame();

  // Find the currently active word index
  const activeIndex = words.findIndex(
    (w) => frame >= w.startFrame && frame < w.endFrame
  );

  // If no word is active yet, find the next upcoming word
  const effectiveIndex =
    activeIndex >= 0
      ? activeIndex
      : words.findIndex((w) => frame < w.startFrame);

  // Calculate sliding window bounds
  const windowStart = Math.max(0, (effectiveIndex >= 0 ? effectiveIndex : 0) - WINDOW_SIZE);
  const windowEnd = Math.min(
    words.length,
    (effectiveIndex >= 0 ? effectiveIndex : 0) + WINDOW_SIZE + 1
  );

  // Get visible words for this frame
  const visibleWords = words.slice(windowStart, windowEnd);

  // Shorts-optimized subtitle styling (TikTok/IG/Shorts):
  const fontFamily =
    '"Inter", "SF Pro Display", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif';

  const fontSizePx = 72; // Slightly smaller for better readability
  const lineHeight = 1.15;

  const outerStyle: React.CSSProperties = {
    position: "absolute",
    // Position at ~25% from bottom (like TikTok)
    bottom: "12%",
    left: "5%",
    right: "5%",
    display: "flex",
    justifyContent: "center",
    pointerEvents: "none",
  };

  const pillStyle: React.CSSProperties = {
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    padding: "16px 32px",
    borderRadius: "12px",
    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5)",
    display: "flex",
    flexWrap: "nowrap",
    justifyContent: "center",
    alignItems: "center",
    gap: "12px",
  };

  const baseTextStyle: React.CSSProperties = {
    fontFamily,
    fontSize: `${fontSizePx}px`,
    lineHeight,
    letterSpacing: "-0.01em",
    textAlign: "center",
    color: colors.textPrimary,
    fontWeight: 600,
    textShadow: "0 2px 8px rgba(0,0,0,0.8)",
    whiteSpace: "nowrap",
  };

  // If no word-level timing, just show the full text (fallback)
  if (words.length === 0) {
    return (
      <div style={outerStyle}>
        <div style={pillStyle}>
          <span style={baseTextStyle}>{text}</span>
        </div>
      </div>
    );
  }

  // Don't render if no visible words
  if (visibleWords.length === 0) {
    return null;
  }

  // Karaoke-style with sliding window
  return (
    <div style={outerStyle}>
      <div style={pillStyle}>
        {visibleWords.map((word, index) => {
          const isActive = frame >= word.startFrame && frame < word.endFrame;

          return (
            <span
              key={windowStart + index}
              style={{
                ...baseTextStyle,
                color: isActive ? colors.highlight : colors.textPrimary,
                fontWeight: isActive ? 800 : 600,
                transform: isActive ? "scale(1.15)" : "scale(1)",
                transition: "transform 0.1s ease-out, color 0.1s ease-out",
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

