"""Segment model - Represents a 10-second block of the reel."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Segment:
    """A single 10-second segment of a reel."""

    id: int
    duration: int  # Always 10 for now
    text: str  # Voiceover script for this segment
    visual_intent: str  # Description of what should be shown

    # Generated assets (populated during pipeline)
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    audio_path: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON output."""
        return {
            "id": self.id,
            "duration": self.duration,
            "text": self.text,
            "visual_intent": self.visual_intent,
            "image_prompt": self.image_prompt,
            "video_prompt": self.video_prompt,
            "image_path": self.image_path,
            "video_path": self.video_path,
            "audio_path": self.audio_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Segment":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            duration=data.get("duration", 10),
            text=data["text"],
            visual_intent=data.get("visual_intent", ""),
            image_prompt=data.get("image_prompt"),
            video_prompt=data.get("video_prompt"),
            image_path=data.get("image_path"),
            video_path=data.get("video_path"),
            audio_path=data.get("audio_path"),
        )

