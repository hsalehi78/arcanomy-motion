import { Composition } from "remotion";
import { MainReel } from "./compositions/MainReel";
import { Shorts } from "./compositions/Shorts";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MainReel"
        component={MainReel}
        durationInFrames={900} // 30 seconds at 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
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
      />
      <Composition
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

