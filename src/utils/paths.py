"""Canonical reel folder layout helpers.

This repo intentionally treats the reel folder as the single source of truth for
pipeline state. These helpers centralize all path conventions so stages and CLI
checks don't hardcode filenames/locations.
"""

from __future__ import annotations

from pathlib import Path


def inputs_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "inputs"


def prompts_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "prompts"


def json_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "json"


def renders_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "renders"


def final_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "final"


def seed_path(reel_path: Path) -> Path:
    return inputs_dir(reel_path) / "seed.md"


def reel_yaml_path(reel_path: Path) -> Path:
    return inputs_dir(reel_path) / "reel.yaml"


def data_dir(reel_path: Path) -> Path:
    return inputs_dir(reel_path) / "data"


def prompt_path(reel_path: Path, filename: str) -> Path:
    return prompts_dir(reel_path) / filename


def json_path(reel_path: Path, filename: str) -> Path:
    return json_dir(reel_path) / filename


def images_dir(reel_path: Path) -> Path:
    return renders_dir(reel_path) / "images"


def images_characters_dir(reel_path: Path) -> Path:
    return images_dir(reel_path) / "characters"


def images_backgrounds_dir(reel_path: Path) -> Path:
    return images_dir(reel_path) / "backgrounds"


def images_objects_dir(reel_path: Path) -> Path:
    return images_dir(reel_path) / "objects"


def images_composites_dir(reel_path: Path) -> Path:
    """Anchor images that feed video generation."""
    return images_dir(reel_path) / "composites"


def videos_dir(reel_path: Path) -> Path:
    return renders_dir(reel_path) / "videos"


def audio_dir(reel_path: Path) -> Path:
    return renders_dir(reel_path) / "audio"


def voice_dir(reel_path: Path) -> Path:
    return audio_dir(reel_path) / "voice"


def sfx_dir(reel_path: Path) -> Path:
    return audio_dir(reel_path) / "sfx"


def ensure_reel_layout(reel_path: Path) -> None:
    """Create the canonical directory structure for a reel."""
    for d in (
        inputs_dir(reel_path),
        data_dir(reel_path),
        prompts_dir(reel_path),
        json_dir(reel_path),
        images_characters_dir(reel_path),
        images_backgrounds_dir(reel_path),
        images_objects_dir(reel_path),
        images_composites_dir(reel_path),
        videos_dir(reel_path),
        voice_dir(reel_path),
        sfx_dir(reel_path),
        final_dir(reel_path),
    ):
        d.mkdir(parents=True, exist_ok=True)


# =============================================================================
# V2 (CapCut kit) paths
# =============================================================================


def v2_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "v2"


def v2_meta_dir(reel_path: Path) -> Path:
    return v2_dir(reel_path) / "meta"


def v2_subsegments_dir(reel_path: Path) -> Path:
    return v2_dir(reel_path) / "subsegments"


def v2_charts_dir(reel_path: Path) -> Path:
    return v2_dir(reel_path) / "charts"


def v2_voice_dir(reel_path: Path) -> Path:
    return v2_dir(reel_path) / "voice"


def v2_captions_dir(reel_path: Path) -> Path:
    return v2_dir(reel_path) / "captions"


def v2_thumbnail_dir(reel_path: Path) -> Path:
    return v2_dir(reel_path) / "thumbnail"


def v2_guides_dir(reel_path: Path) -> Path:
    return v2_dir(reel_path) / "guides"


def v2_provenance_path(reel_path: Path) -> Path:
    return v2_meta_dir(reel_path) / "provenance.json"


def v2_quality_gate_path(reel_path: Path) -> Path:
    return v2_meta_dir(reel_path) / "quality_gate.json"


def v2_plan_path(reel_path: Path) -> Path:
    return v2_meta_dir(reel_path) / "plan.json"


def v2_captions_srt_path(reel_path: Path) -> Path:
    return v2_captions_dir(reel_path) / "captions.srt"


def claim_json_path(reel_path: Path) -> Path:
    """Canonical v2 input."""
    return inputs_dir(reel_path) / "claim.json"


def data_json_path(reel_path: Path) -> Path:
    """Canonical v2 input."""
    return inputs_dir(reel_path) / "data.json"


def ensure_v2_layout(reel_path: Path) -> None:
    """Create the canonical v2 output directory structure for a reel."""
    for d in (
        v2_meta_dir(reel_path),
        v2_subsegments_dir(reel_path),
        v2_charts_dir(reel_path),
        v2_voice_dir(reel_path),
        v2_captions_dir(reel_path),
        v2_thumbnail_dir(reel_path),
        v2_guides_dir(reel_path),
    ):
        d.mkdir(parents=True, exist_ok=True)


