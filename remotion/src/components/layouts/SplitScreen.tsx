import { AbsoluteFill } from "remotion";
import { COLORS } from "../../lib/constants";

interface SplitScreenProps {
  left: React.ReactNode;
  right: React.ReactNode;
  ratio?: number; // 0-1, percentage for left side
  vertical?: boolean;
  colors?: typeof COLORS;
}

export const SplitScreen: React.FC<SplitScreenProps> = ({
  left,
  right,
  ratio = 0.5,
  vertical = false,
  colors = COLORS,
}) => {
  const leftPercent = `${ratio * 100}%`;
  const rightPercent = `${(1 - ratio) * 100}%`;

  if (vertical) {
    return (
      <AbsoluteFill style={{ backgroundColor: colors.bg }}>
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: leftPercent,
            overflow: "hidden",
          }}
        >
          {left}
        </div>
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: rightPercent,
            overflow: "hidden",
          }}
        >
          {right}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          bottom: 0,
          width: leftPercent,
          overflow: "hidden",
        }}
      >
        {left}
      </div>
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          bottom: 0,
          width: rightPercent,
          overflow: "hidden",
        }}
      >
        {right}
      </div>
    </AbsoluteFill>
  );
};

