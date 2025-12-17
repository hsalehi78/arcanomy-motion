"""Stage 6 & 7: Music selection and final assembly."""

import json
from datetime import datetime
from pathlib import Path

from src.domain import Manifest, Objective, Segment
from src.services import RemotionCLI
from src.utils.io import read_file, write_file


def run_music_selection(reel_path: Path) -> dict:
    """Select background music based on mood.

    Args:
        reel_path: Path to the reel folder

    Returns:
        Music selection result
    """
    objective = Objective.from_reel_folder(reel_path)

    # TODO: Implement actual music library search
    # For now, return placeholder
    result = {
        "music_mood": objective.music_mood,
        "selected_track": None,  # Would be path to selected track
        "volume": 0.3,
        "status": "pending",
    }

    # Save input/output
    input_path = reel_path / "06_music.input.md"
    write_file(input_path, f"# Music Selection\n\nMood: {objective.music_mood}")

    output_path = reel_path / "06_music.output.json"
    write_file(output_path, json.dumps(result, indent=2))

    return result


def run_assembly(reel_path: Path) -> Path:
    """Assemble all assets into final video using Remotion.

    Args:
        reel_path: Path to the reel folder

    Returns:
        Path to final video
    """
    objective = Objective.from_reel_folder(reel_path)

    # Load segments with all assets
    segments_path = reel_path / "03.5_generate_assets_agent.output.json"
    with open(segments_path, "r", encoding="utf-8") as f:
        segments_data = json.load(f)
    segments = [Segment.from_dict(s) for s in segments_data]

    # Load audio paths
    audio_path = reel_path / "05.5_generate_audio_agent.output.json"
    if audio_path.exists():
        with open(audio_path, "r", encoding="utf-8") as f:
            audio_data = json.load(f)
        audio_by_id = {a["segment_id"]: a.get("audio_path") for a in audio_data}
        for segment in segments:
            segment.audio_path = audio_by_id.get(segment.id)

    # Load video paths
    video_path = reel_path / "04.5_generate_videos_agent.output.json"
    if video_path.exists():
        with open(video_path, "r", encoding="utf-8") as f:
            video_data = json.load(f)
        video_by_id = {v["segment_id"]: v.get("output_path") for v in video_data}
        for segment in segments:
            segment.video_path = video_by_id.get(segment.id)

    # Load music
    music_path = reel_path / "06_music.output.json"
    music_track = None
    if music_path.exists():
        with open(music_path, "r", encoding="utf-8") as f:
            music_data = json.load(f)
        music_track = music_data.get("selected_track")

    # Build manifest
    manifest = Manifest.from_segments(segments, fps=30, music_path=music_track)

    # Save manifest
    manifest_path = reel_path / "07_assemble_final_agent.output.json"
    write_file(manifest_path, json.dumps(manifest.to_dict(), indent=2))

    # Also save input for audit
    input_path = reel_path / "07_assemble_final_agent.input.md"
    write_file(
        input_path,
        f"# Assembly Input\n\n"
        f"Segments: {len(segments)}\n"
        f"Duration: {objective.duration_seconds}s\n"
        f"Music: {music_track or 'None'}\n",
    )

    # Create final directory
    final_dir = reel_path / "final"
    final_dir.mkdir(exist_ok=True)

    # Render with Remotion
    remotion = RemotionCLI()
    final_video = final_dir / "final.mp4"

    try:
        remotion.render(
            composition_id="MainReel",
            output_path=final_video,
            props=manifest.to_dict(),
        )
    except RuntimeError as e:
        # Log error but continue to create metadata
        write_file(final_dir / "render_error.txt", str(e))

    # Generate metadata
    metadata = {
        "version": "1.0",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "config": {
            "title": objective.title,
            "type": objective.type,
            "duration_blocks": objective.duration_blocks,
            "voice_id": objective.voice_id,
        },
        "data_sources": objective.data_sources,
        "model_ids": {
            "llm": "gpt-4o",
            "voice": objective.voice_id,
            "video": "pending",
        },
        "render_duration_seconds": objective.duration_seconds,
    }

    metadata_path = final_dir / "metadata.json"
    write_file(metadata_path, json.dumps(metadata, indent=2))

    return final_video


def run_delivery(reel_path: Path) -> dict:
    """Prepare final deliverables.

    Args:
        reel_path: Path to the reel folder

    Returns:
        Delivery status
    """
    final_dir = reel_path / "final"

    deliverables = {
        "video": final_dir / "final.mp4",
        "subtitles": final_dir / "final.srt",
        "metadata": final_dir / "metadata.json",
    }

    status = {}
    for name, path in deliverables.items():
        status[name] = {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    return status

