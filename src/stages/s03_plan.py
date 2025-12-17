"""Stage 3: Visual Planning - Define visual language and character style."""

from pathlib import Path

from src.domain import Objective
from src.services import LLMService
from src.utils.io import read_file, write_file


def run_visual_plan(reel_path: Path, llm: LLMService) -> Path:
    """Generate visual style guide and character descriptions.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the visual plan output file
    """
    objective = Objective.from_reel_folder(reel_path)

    # Load script
    script_path = reel_path / "02_story_generator.output.md"
    script = read_file(script_path) if script_path.exists() else ""

    system_prompt = """You are a visual director for short-form video content.
Your job is to define the visual language, style, and any characters/elements.

Consider:
- Color palette and mood
- Typography style
- Motion/animation approach
- Any recurring visual elements
- Character or presenter descriptions (if applicable)

Be specific and actionable for image/video generation."""

    user_prompt = f"""Define the visual style for this reel:

## Visual Vibe (from brief)
{objective.visual_vibe}

## Reel Type
{objective.type}

## Script
{script}

Please provide:
1. Overall visual mood and atmosphere
2. Color palette (specific hex codes if possible)
3. Typography recommendations
4. Key visual elements per segment
5. Motion/animation style
6. Any character or object descriptions"""

    # Save input
    input_path = reel_path / "03_character_generation.input.md"
    write_file(input_path, f"# Visual Planning Prompt\n\n{user_prompt}")

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt)

    # Save output
    output_path = reel_path / "03_character_generation.output.md"
    write_file(output_path, f"# Visual Plan\n\n{response}")

    return output_path

