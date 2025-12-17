"""Stage 5: Audio Generation and Assembly preparation."""

import json
from pathlib import Path

from src.domain import Segment
from src.services import ElevenLabsService, LLMService
from src.utils.io import read_file, write_file


def run_voice_prompting(reel_path: Path, llm: LLMService) -> Path:
    """Generate voice direction annotations for the script.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the voice direction output
    """
    # Load script
    script_path = reel_path / "02_story_generator.output.md"
    script = read_file(script_path) if script_path.exists() else ""

    system_prompt = """You are a voice director for short-form video content.
Annotate the script with prosody and emotion directions for text-to-speech.

Use annotations like:
- [pause 0.5s]
- [emphasis]word[/emphasis]
- [slower]phrase[/slower]
- [whisper]phrase[/whisper]

Keep the natural flow while adding subtle emotional guidance."""

    user_prompt = f"""Add voice direction to this script:

{script}

Annotate each segment with prosody directions that make the delivery feel natural and engaging."""

    # Save input
    input_path = reel_path / "05_voice_prompt_engineer.input.md"
    write_file(input_path, f"# Voice Direction Prompt\n\n{user_prompt}")

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt)

    # Save output
    output_path = reel_path / "05_voice_prompt_engineer.output.md"
    write_file(output_path, f"# Voice Direction\n\n{response}")

    return output_path


def run_audio_generation(reel_path: Path, voice_id: str) -> list[dict]:
    """Generate audio for each segment using ElevenLabs.

    Args:
        reel_path: Path to the reel folder
        voice_id: ElevenLabs voice ID

    Returns:
        List of audio generation results
    """
    # Load segments
    segments_path = reel_path / "02_story_generator.output.json"
    with open(segments_path, "r", encoding="utf-8") as f:
        segments_data = json.load(f)
    segments = [Segment.from_dict(s) for s in segments_data]

    renders_dir = reel_path / "renders"
    renders_dir.mkdir(exist_ok=True)

    elevenlabs = ElevenLabsService()
    results = []

    for segment in segments:
        output_path = renders_dir / f"voice_{segment.id:02d}.mp3"

        try:
            elevenlabs.generate_speech(
                text=segment.text,
                voice_id=voice_id,
                output_path=output_path,
            )
            segment.audio_path = str(output_path)
            results.append({
                "segment_id": segment.id,
                "audio_path": str(output_path),
                "status": "completed",
            })
        except Exception as e:
            results.append({
                "segment_id": segment.id,
                "audio_path": None,
                "status": "failed",
                "error": str(e),
            })

    # Save results
    output_path = reel_path / "05.5_generate_audio_agent.output.json"
    write_file(output_path, json.dumps(results, indent=2))

    return results

