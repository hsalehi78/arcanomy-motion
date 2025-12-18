"""Stage 1: Research - Ground the seed concept in facts."""

from pathlib import Path

from src.domain import Objective
from src.services import LLMService
from src.utils.io import read_file, write_file

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_system_prompt() -> str:
    """Load the research system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "research_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    # Fallback if file missing
    return "You are a research assistant for financial content creation."


def run_research(reel_path: Path, llm: LLMService) -> Path:
    """Run research stage to gather context for the reel.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the research output file
    """
    objective = Objective.from_reel_folder(reel_path)
    system_prompt = load_system_prompt()

    # Load any CSV data from 00_data folder
    data_dir = reel_path / "00_data"
    data_context = ""
    if data_dir.exists():
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            data_snippets = []
            for csv_file in csv_files:
                content = read_file(csv_file)
                # Show first 20 lines max
                lines = content.strip().split("\n")[:20]
                csv_preview = "\n".join(lines)
                data_snippets.append(f"**{csv_file.name}:**\n```csv\n{csv_preview}\n```")
            data_context = "\n\n".join(data_snippets)

    # Build data section
    if data_context:
        data_section = f"## Available Data\n{data_context}"
    else:
        data_section = "## Available Data\nNo CSV data provided. Research from public sources."

    user_prompt = f"""# Research Brief

## The Hook (Opening Line)
> {objective.hook}

## The Core Insight (The Lesson)
> {objective.core_insight}

## Visual Vibe (Mood Direction)
> {objective.visual_vibe}

## Format Constraints
- **Duration:** {objective.duration_blocks} blocks ({objective.duration_seconds} seconds)
- **Reel Type:** {objective.type}

{data_section}

---

Generate a complete research document following the 7-section structure in your instructions. Ensure all statistics are sourced and all visual metaphors are concrete and filmable.
"""

    # Save input prompt (both system + user for full audit trail)
    input_path = reel_path / "01_research.input.md"
    input_content = f"""# Research Stage Input

## System Prompt

{system_prompt}

{"=" * 80}
========================== USER PROMPT BELOW ==========================
{"=" * 80}

{user_prompt}
"""
    write_file(input_path, input_content)

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt)

    # Save output
    output_path = reel_path / "01_research.output.md"
    write_file(output_path, f"# Research Output\n\n{response}")

    return output_path

