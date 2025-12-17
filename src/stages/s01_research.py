"""Stage 1: Research - Ground the seed concept in facts."""

from pathlib import Path

from src.domain import Objective
from src.services import LLMService
from src.utils.io import read_file, write_file


def run_research(reel_path: Path, llm: LLMService) -> Path:
    """Run research stage to gather context for the reel.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the research output file
    """
    objective = Objective.from_reel_folder(reel_path)

    # Build research prompt
    system_prompt = """You are a research assistant for financial content creation.
Your job is to gather relevant facts, statistics, and context for a short-form video.
Focus on:
- Verifiable data points
- Behavioral psychology insights
- Common misconceptions to address
- Key takeaways for the audience

Be concise and cite sources where possible."""

    user_prompt = f"""Research the following topic for a short video:

## Hook
{objective.hook}

## Core Insight
{objective.core_insight}

## Visual Vibe
{objective.visual_vibe}

## Duration
{objective.duration_blocks} blocks ({objective.duration_seconds} seconds)

Please provide:
1. Key facts and statistics (3-5 points)
2. Psychological angle (why this matters to viewers)
3. Common objections or misconceptions
4. Suggested narrative arc for {objective.duration_blocks} segments
"""

    # Save input prompt
    input_path = reel_path / "01_research.input.md"
    write_file(input_path, f"# Research Prompt\n\n{user_prompt}")

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt)

    # Save output
    output_path = reel_path / "01_research.output.md"
    write_file(output_path, f"# Research Output\n\n{response}")

    return output_path

