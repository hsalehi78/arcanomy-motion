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

  // If no word-level timing, just show the full text
  if (words.length === 0) {
    return (
      <div
        style={{
          position: "absolute",
          bottom: "20%",
          left: "10%",
          right: "10%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            padding: "16px 24px",
            borderRadius: "8px",
          }}
        >
          <span
            style={{
              color: colors.textPrimary,
              fontSize: "42px",
              fontWeight: 500,
              textAlign: "center",
            }}
          >
            {text}
          </span>
        </div>
      </div>
    );
  }

  // Karaoke-style highlighting
  return (
    <div
      style={{
        position: "absolute",
        bottom: "20%",
        left: "10%",
        right: "10%",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          padding: "16px 24px",
          borderRadius: "8px",
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "8px",
        }}
      >
        {words.map((word, index) => {
          const isActive = frame >= word.startFrame && frame < word.endFrame;
          
          return (
            <span
              key={index}
              style={{
                color: isActive ? colors.highlight : colors.textPrimary,
                fontSize: "42px",
                fontWeight: isActive ? 700 : 500,
                transform: isActive ? "scale(1.1)" : "scale(1)",
                transition: "all 0.1s ease",
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

