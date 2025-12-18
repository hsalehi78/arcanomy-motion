"""Stage 4: Asset Generation - Generate images and videos for each segment."""

import json
from pathlib import Path

from src.domain import Segment
from src.services import LLMService
from src.utils.io import read_file, write_file

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_system_prompt() -> str:
    """Load the assets system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "assets_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    # Fallback if file missing
    return """You are a prompt engineer for AI image generation.
Create detailed, specific prompts that will produce consistent, high-quality images.

For each segment, provide:
1. An image prompt (for DALL-E 3 or similar)
2. A video motion prompt (for Kling/Runway - describe camera movement and subject motion)

Style should be consistent across all segments.
Output as JSON array."""


def run_asset_generation(reel_path: Path, llm: LLMService) -> list[Segment]:
    """Generate image and video prompts for each segment.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        List of Segment objects with prompts populated
    """
    system_prompt = load_system_prompt()

    # Load segments
    segments_path = reel_path / "02_story_generator.output.json"
    with open(segments_path, "r", encoding="utf-8") as f:
        segments_data = json.load(f)
    
    # Handle both formats: {"segments": [...]} or just [...]
    if isinstance(segments_data, dict) and "segments" in segments_data:
        segments_list = segments_data["segments"]
    else:
        segments_list = segments_data
    
    segments = [Segment.from_dict(s) for s in segments_list]

    # Load visual plan
    visual_plan_path = reel_path / "03_character_generation.output.md"
    visual_plan = read_file(visual_plan_path) if visual_plan_path.exists() else ""

    segments_desc = "\n".join(
        f"Segment {s.id}: {s.visual_intent}" for s in segments
    )

    user_prompt = f"""Generate prompts for these segments:

## Visual Style Guide
{visual_plan}

## Segments
{segments_desc}

Output format:
{{
  "prompts": [
    {{"segment_id": 1, "image_prompt": "...", "video_prompt": "..."}}
  ]
}}"""

    # Save input (both system + user for full audit trail)
    input_path = reel_path / "03.5_generate_assets_agent.input.md"
    input_content = f"""# Asset Generation Stage Input

## System Prompt

{system_prompt}

{"=" * 80}
========================== USER PROMPT BELOW ==========================
{"=" * 80}

{user_prompt}
"""
    write_file(input_path, input_content)

    # Call LLM
    response = llm.complete_json(user_prompt, system=system_prompt)

    # Update segments with prompts
    prompts_by_id = {p["segment_id"]: p for p in response.get("prompts", [])}
    for segment in segments:
        if segment.id in prompts_by_id:
            prompt_data = prompts_by_id[segment.id]
            segment.image_prompt = prompt_data.get("image_prompt")
            segment.video_prompt = prompt_data.get("video_prompt")

    # Save output
    output_path = reel_path / "03.5_generate_assets_agent.output.json"
    write_file(
        output_path,
        json.dumps([s.to_dict() for s in segments], indent=2),
    )

    return segments


def run_video_generation(reel_path: Path) -> list[Segment]:
    """Execute video generation (placeholder for actual API calls).

    This is the "dumb script" that calls video generation APIs.

    Args:
        reel_path: Path to the reel folder

    Returns:
        List of Segment objects with video paths populated
    """
    # Load segments with prompts
    prompts_path = reel_path / "03.5_generate_assets_agent.output.json"
    with open(prompts_path, "r", encoding="utf-8") as f:
        segments_data = json.load(f)
    segments = [Segment.from_dict(s) for s in segments_data]

    renders_dir = reel_path / "renders"
    renders_dir.mkdir(exist_ok=True)

    # TODO: Implement actual video generation API calls
    # For now, just log what would be generated
    execution_log = []
    for segment in segments:
        video_path = renders_dir / f"bg_{segment.id:02d}.mp4"
        segment.video_path = str(video_path)
        execution_log.append({
            "segment_id": segment.id,
            "video_prompt": segment.video_prompt,
            "output_path": str(video_path),
            "status": "pending",
        })

    # Save execution plan
    output_path = reel_path / "04.5_generate_videos_agent.output.json"
    write_file(output_path, json.dumps(execution_log, indent=2))

    return segments
