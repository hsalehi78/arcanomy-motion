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
# Pipeline output paths (CapCut kit)
# =============================================================================


def meta_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "meta"


def subsegments_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "subsegments"


def charts_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "charts"


def pipeline_voice_dir(reel_path: Path) -> Path:
    """Voice output for pipeline (subseg-*.wav)."""
    return Path(reel_path) / "voice"


def captions_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "captions"


def thumbnail_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "thumbnail"


def guides_dir(reel_path: Path) -> Path:
    return Path(reel_path) / "guides"


def provenance_path(reel_path: Path) -> Path:
    return meta_dir(reel_path) / "provenance.json"


def quality_gate_path(reel_path: Path) -> Path:
    return meta_dir(reel_path) / "quality_gate.json"


def plan_path(reel_path: Path) -> Path:
    return meta_dir(reel_path) / "plan.json"


def captions_srt_path(reel_path: Path) -> Path:
    return captions_dir(reel_path) / "captions.srt"


def claim_json_path(reel_path: Path) -> Path:
    """Canonical pipeline input."""
    return inputs_dir(reel_path) / "claim.json"


def data_json_path(reel_path: Path) -> Path:
    """Canonical pipeline input."""
    return inputs_dir(reel_path) / "data.json"


def ensure_pipeline_layout(reel_path: Path) -> None:
    """Create the canonical pipeline output directory structure for a reel."""
    for d in (
        inputs_dir(reel_path),
        meta_dir(reel_path),
        subsegments_dir(reel_path),
        charts_dir(reel_path),
        pipeline_voice_dir(reel_path),
        captions_dir(reel_path),
        thumbnail_dir(reel_path),
        guides_dir(reel_path),
    ):
        d.mkdir(parents=True, exist_ok=True)


# Legacy aliases for backwards compatibility during migration
v2_dir = lambda reel_path: Path(reel_path)  # No more v2 subfolder
v2_meta_dir = meta_dir
v2_subsegments_dir = subsegments_dir
v2_charts_dir = charts_dir
v2_voice_dir = pipeline_voice_dir
v2_captions_dir = captions_dir
v2_thumbnail_dir = thumbnail_dir
v2_guides_dir = guides_dir
v2_provenance_path = provenance_path
v2_quality_gate_path = quality_gate_path
v2_plan_path = plan_path
v2_captions_srt_path = captions_srt_path
ensure_v2_layout = ensure_pipeline_layout


