"""Stage 6.5: Sound Effects Generation - Generate SFX audio with ElevenLabs.

This is a Dumb Script stage that:
1. Reads sound effect prompts from Stage 6
2. Generates audio using ElevenLabs Sound Effects API
3. Saves audio files to renders/sfx/
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.services import ElevenLabsService
from src.utils.io import write_file
from src.utils.logger import get_logger

logger = get_logger()

# Default sound effect duration (matches video clip duration)
DEFAULT_DURATION_SECONDS = 10.0
DEFAULT_PROMPT_INFLUENCE = 0.3


def run_sfx_generation(
    reel_path: Path,
    dry_run: bool = False,
    prompt_influence: float = DEFAULT_PROMPT_INFLUENCE,
) -> list[dict]:
    """Generate sound effects for each clip using ElevenLabs.

    This stage:
    1. Reads sound effect prompts from Stage 6 (06_sound_effects.output.json)
    2. Generates audio using ElevenLabs Sound Effects API
    3. Saves audio files to renders/sfx/

    Args:
        reel_path: Path to the reel folder
        dry_run: If True, only save prompts without calling API
        prompt_influence: How closely to follow the prompt (0-1, default 0.3)

    Returns:
        List of generation results
    """
    # Load sound effect prompts from Stage 6
    sfx_prompts_path = reel_path / "06_sound_effects.output.json"

    if not sfx_prompts_path.exists():
        logger.error("No sound effects prompts found. Run Stage 6 (sfx) first.")
        return []

    with open(sfx_prompts_path, "r", encoding="utf-8") as f:
        sfx_data = json.load(f)

    sound_effects = sfx_data.get("sound_effects", [])

    if not sound_effects:
        logger.error("No sound effects found in 06_sound_effects.output.json")
        return []

    # Prepare output directory
    sfx_dir = reel_path / "renders" / "sfx"
    sfx_dir.mkdir(parents=True, exist_ok=True)

    # Initialize ElevenLabs service
    elevenlabs = None
    if not dry_run:
        elevenlabs = ElevenLabsService()

    results = []
    execution_log = []

    for sfx in sound_effects:
        clip_num = sfx.get("clip_number", sfx.get("segment_id", 1))
        prompt = sfx.get("prompt", "")
        duration = sfx.get("duration_seconds", DEFAULT_DURATION_SECONDS)
        output_path = sfx_dir / f"clip_{clip_num:02d}_sfx.mp3"

        execution_log.append(f"\n## Clip {clip_num:02d}")
        execution_log.append(f"- Scene: {sfx.get('scene_summary', 'N/A')[:50]}")
        execution_log.append(f"- Prompt: \"{prompt[:80]}...\"")
        execution_log.append(f"- Duration: {duration}s")

        if not prompt:
            execution_log.append("- Status: SKIPPED (no prompt)")
            results.append(
                {
                    "clip_number": clip_num,
                    "segment_id": sfx.get("segment_id", clip_num),
                    "prompt": prompt,
                    "audio_path": None,
                    "status": "skipped_no_prompt",
                }
            )
            continue

        if dry_run:
            # Save prompt to text file
            prompt_path = output_path.with_suffix(".prompt.txt")
            write_file(
                prompt_path,
                f"# Sound Effect Prompt (Dry Run)\n\n"
                f"Clip: {clip_num}\n"
                f"Duration: {duration}s\n"
                f"Prompt Influence: {prompt_influence}\n\n"
                f"## Prompt:\n{prompt}\n",
            )
            results.append(
                {
                    "clip_number": clip_num,
                    "segment_id": sfx.get("segment_id", clip_num),
                    "prompt": prompt,
                    "audio_path": str(output_path),
                    "prompt_file": str(prompt_path),
                    "status": "dry_run",
                }
            )
            execution_log.append(f"- Status: DRY RUN (prompt saved to {prompt_path.name})")
            continue

        # Generate sound effect
        try:
            execution_log.append("- Status: Generating...")

            audio_path = elevenlabs.generate_sound_effect(
                text=prompt,
                output_path=output_path,
                duration_seconds=duration,
                prompt_influence=prompt_influence,
            )

            results.append(
                {
                    "clip_number": clip_num,
                    "segment_id": sfx.get("segment_id", clip_num),
                    "prompt": prompt,
                    "audio_path": str(audio_path),
                    "duration_seconds": duration,
                    "status": "success",
                }
            )
            execution_log.append(f"- Status: [OK] Saved to {output_path.name}")
            logger.info(f"[OK] Clip {clip_num:02d}: {output_path.name}")

        except Exception as e:
            results.append(
                {
                    "clip_number": clip_num,
                    "segment_id": sfx.get("segment_id", clip_num),
                    "prompt": prompt,
                    "audio_path": None,
                    "status": "failed",
                    "error": str(e),
                }
            )
            execution_log.append(f"- Status: [!!] FAILED - {e}")
            logger.error(f"[!!] Clip {clip_num:02d}: Failed - {e}")

    # Save execution log
    input_log_path = reel_path / "06.5_sound_effects_generation.input.md"
    log_content = f"""# Sound Effects Generation Execution Log

Generated: {datetime.now(timezone.utc).isoformat()}

## Configuration
- Prompt Influence: {prompt_influence}
- Duration: {DEFAULT_DURATION_SECONDS}s
- Total Clips: {len(sound_effects)}
- Mode: {"Dry Run" if dry_run else "Live Generation"}

## Execution Log
{"".join(execution_log)}
"""
    write_file(input_log_path, log_content)

    # Save results JSON
    output_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt_influence": prompt_influence,
        "duration_seconds": DEFAULT_DURATION_SECONDS,
        "total_clips": len(results),
        "successful": sum(1 for r in results if r.get("status") in ("success", "dry_run")),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "clips": results,
    }
    output_path = reel_path / "06.5_sound_effects_generation.output.json"
    write_file(output_path, json.dumps(output_json, indent=2))

    # Print summary
    success_count = output_json["successful"]
    failed_count = output_json["failed"]
    logger.info(f"Sound effects generation complete: {success_count}/{len(results)} successful")

    if failed_count > 0:
        logger.warning(f"   {failed_count} clips failed - check execution log")

    return results

