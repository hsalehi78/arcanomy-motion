"""Manifest model - The render payload sent to Remotion."""

from dataclasses import dataclass, field
from typing import Optional

from .segment import Segment


@dataclass
class ManifestSegment:
    """Segment data formatted for Remotion timeline."""

    id: int
    start_frame: int
    duration_frames: int
    video_path: str
    audio_path: Optional[str]
    text: str
    subtitle_words: list[dict]  # [{word, start_frame, end_frame}]


@dataclass
class Manifest:
    """Complete render manifest for Remotion."""

    fps: int = 30
    width: int = 1080
    height: int = 1920  # 9:16 aspect ratio
    total_frames: int = 0

    segments: list[ManifestSegment] = field(default_factory=list)
    music_path: Optional[str] = None
    music_volume: float = 0.3

    # Style overrides
    colors: dict = field(default_factory=lambda: {
        "bg": "#000000",
        "bgSecondary": "#0A0A0A",
        "textPrimary": "#F5F5F5",
        "highlight": "#FFD700",
        "chartLine": "#FFB800",
        "danger": "#FF3B30",
    })

    @classmethod
    def from_segments(
        cls,
        segments: list[Segment],
        fps: int = 30,
        music_path: Optional[str] = None,
    ) -> "Manifest":
        """Build manifest from processed segments."""
        manifest = cls(fps=fps, music_path=music_path)

        current_frame = 0
        for seg in segments:
            duration_frames = seg.duration * fps

            manifest_seg = ManifestSegment(
                id=seg.id,
                start_frame=current_frame,
                duration_frames=duration_frames,
                video_path=seg.video_path or "",
                audio_path=seg.audio_path,
                text=seg.text,
                subtitle_words=[],  # TODO: Word-level timing from ElevenLabs
            )
            manifest.segments.append(manifest_seg)
            current_frame += duration_frames

        manifest.total_frames = current_frame
        return manifest

    def to_dict(self) -> dict:
        """Serialize for JSON export to Remotion."""
        return {
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "totalFrames": self.total_frames,
            "segments": [
                {
                    "id": s.id,
                    "startFrame": s.start_frame,
                    "durationFrames": s.duration_frames,
                    "videoPath": s.video_path,
                    "audioPath": s.audio_path,
                    "text": s.text,
                    "subtitleWords": s.subtitle_words,
                }
                for s in self.segments
            ],
            "musicPath": self.music_path,
            "musicVolume": self.music_volume,
            "colors": self.colors,
        }

