"""Stage 2: Script - Write voiceover and segment into 10s blocks."""

import json
from pathlib import Path

from src.domain import Objective, Segment
from src.services import LLMService
from src.utils.io import read_file, write_file


def run_script(reel_path: Path, llm: LLMService) -> list[Segment]:
    """Generate script and segment it into 10-second blocks.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        List of Segment objects
    """
    objective = Objective.from_reel_folder(reel_path)

    # Load research if available
    research_path = reel_path / "01_research.output.md"
    research = read_file(research_path) if research_path.exists() else ""

    system_prompt = """You are a scriptwriter for short-form financial video content.
Your job is to write punchy, clear voiceover scripts that fit into 10-second blocks.

Rules:
- Each 10-second block = ~25-30 words of spoken text
- First block must grab attention (the hook)
- Each block should flow naturally into the next
- Use simple language (8th grade reading level)
- Avoid jargon unless you immediately explain it

Output JSON format:
{
  "segments": [
    {"id": 1, "duration": 10, "text": "voiceover text", "visual_intent": "what should be shown"}
  ]
}"""

    user_prompt = f"""Write a {objective.duration_blocks}-block script ({objective.duration_seconds} seconds total).

## Hook
{objective.hook}

## Core Insight
{objective.core_insight}

## Research
{research}

## Reel Type
{objective.type}

Remember: Each block is exactly 10 seconds (~25-30 words).
Return valid JSON with the segments array."""

    # Save input
    input_path = reel_path / "02_story_generator.input.md"
    write_file(input_path, f"# Script Generation Prompt\n\n{user_prompt}")

    # Call LLM for JSON response
    response = llm.complete_json(user_prompt, system=system_prompt)

    # Parse segments
    segments = [Segment.from_dict(s) for s in response.get("segments", [])]

    # Save outputs
    output_md_path = reel_path / "02_story_generator.output.md"
    script_text = "\n\n".join(
        f"## Block {s.id} ({s.duration}s)\n{s.text}\n\n*Visual: {s.visual_intent}*"
        for s in segments
    )
    write_file(output_md_path, f"# Generated Script\n\n{script_text}")

    output_json_path = reel_path / "02_story_generator.output.json"
    write_file(
        output_json_path,
        json.dumps([s.to_dict() for s in segments], indent=2),
    )

    return segments

