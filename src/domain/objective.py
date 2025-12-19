"""Objective model - Parses inputs/seed.md and inputs/reel.yaml into a unified config."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import yaml

from src.utils.paths import reel_yaml_path, seed_path


@dataclass
class Objective:
    """Represents the complete reel objective from seed + config."""

    # From inputs/reel.yaml
    title: str
    type: Literal["chart_explainer", "text_cinematic", "story_essay"]
    duration_blocks: int
    voice_id: str
    music_mood: str
    aspect_ratio: str = "9:16"
    subtitles: str = "burned_in"
    audit_level: Literal["strict", "loose"] = "strict"

    # From inputs/seed.md
    hook: str = ""
    core_insight: str = ""
    visual_vibe: str = ""
    data_sources: list[str] = field(default_factory=list)

    # Computed
    reel_path: Optional[Path] = None

    @classmethod
    def from_reel_folder(cls, reel_path: Path) -> "Objective":
        """Load objective from a reel folder containing inputs/seed.md and inputs/reel.yaml."""
        reel_path = Path(reel_path)

        # Load YAML config
        yaml_path = reel_yaml_path(reel_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config not found: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Load seed markdown
        s_path = seed_path(reel_path)
        seed_data = cls._parse_seed(s_path) if s_path.exists() else {}

        return cls(
            title=config.get("title", "Untitled"),
            type=config.get("type", "chart_explainer"),
            duration_blocks=config.get("duration_blocks", 2),
            voice_id=config.get("voice_id", ""),
            music_mood=config.get("music_mood", ""),
            aspect_ratio=config.get("aspect_ratio", "9:16"),
            subtitles=config.get("subtitles", "burned_in"),
            audit_level=config.get("audit_level", "strict"),
            hook=seed_data.get("hook", ""),
            core_insight=seed_data.get("core_insight", ""),
            visual_vibe=seed_data.get("visual_vibe", ""),
            data_sources=seed_data.get("data_sources", []),
            reel_path=reel_path,
        )

    @staticmethod
    def _parse_seed(seed_path: Path) -> dict:
        """Parse inputs/seed.md into structured sections."""
        with open(seed_path, "r", encoding="utf-8") as f:
            content = f.read()

        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("# "):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[2:].lower().replace(" ", "_")
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        # Parse data sources list
        if "data_sources" in sections:
            sources = []
            for line in sections["data_sources"].split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    sources.append(line[2:].strip())
            sections["data_sources"] = sources

        return sections

    @property
    def duration_seconds(self) -> int:
        """Total duration in seconds."""
        return self.duration_blocks * 10

