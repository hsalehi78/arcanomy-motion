"""Stage 3: Visual Planning - Create asset manifest and generation prompts."""

import json
import re
from pathlib import Path

from src.domain import Objective
from src.services import LLMService
from src.utils.io import read_file, write_file

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_system_prompt() -> str:
    """Load the visual plan system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "03_visual_plan_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    # Fallback if file missing
    return """You are a visual director and prompt engineer for short-form video content.
Your job is to create complete asset prompts for image and video generation.

For each segment, provide:
1. Asset manifest (list of assets needed)
2. Segment-to-asset mapping
3. Global atmosphere block
4. Complete image prompts (for DALL-E/Midjourney)
5. Video motion prompts (for Kling/Runway)

Output both human-readable markdown AND a JSON block with the asset definitions."""


def extract_json_from_response(response: str) -> dict | None:
    """Extract JSON from LLM response that may contain markdown."""
    # Try to find JSON code block
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find raw JSON object
    json_match = re.search(r'\{[\s\S]*"global_atmosphere"[\s\S]*"assets"[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def run_visual_plan(reel_path: Path, llm: LLMService) -> Path:
    """Generate visual plan with asset manifest and prompts.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the visual plan output file
    """
    objective = Objective.from_reel_folder(reel_path)
    system_prompt = load_system_prompt()

    # Load script segments (JSON for structured data)
    segments_json_path = reel_path / "02_story_generator.output.json"
    segments_md_path = reel_path / "02_story_generator.output.md"
    
    segments_json = ""
    segments_md = ""
    
    if segments_json_path.exists():
        segments_json = read_file(segments_json_path)
    if segments_md_path.exists():
        segments_md = read_file(segments_md_path)

    # Load seed for visual vibe context
    seed_path = reel_path / "00_seed.md"
    seed_content = read_file(seed_path) if seed_path.exists() else ""

    user_prompt = f"""# Visual Plan Generation Request

## Reel Configuration
- **Title:** {objective.title}
- **Type:** {objective.type}
- **Duration:** {objective.duration_blocks} blocks ({objective.duration_seconds} seconds)
- **Aspect Ratio:** 9:16 (vertical for Reels/TikTok)

## Seed Document (00_seed.md)
{seed_content}

## Production Script (02_story_generator.output.json)

```json
{segments_json}
```

## Human-Readable Script
{segments_md}

---

## Your Task

Generate the complete Visual Plan following the structure in your system prompt:

1. **Part 1: Asset Manifest** - List all unique assets needed
2. **Part 2: Segment-to-Asset Mapping Table** - Which asset goes in which segment
3. **Part 3: Global Atmosphere Block** - 100-150 word consistency paragraph
4. **Part 4: Master Image Prompts** - Complete DALL-E/Midjourney prompts in code blocks
5. **Part 5: Video Motion Prompts** - Kling/Runway prompts for each asset

**CRITICAL:** At the end of your response, include a JSON block with this structure:

```json
{{
  "global_atmosphere": "The complete atmosphere block...",
  "assets": [
    {{
      "id": "asset_id_here",
      "name": "Asset Name (State)",
      "type": "object|character|environment",
      "used_in_segments": [1],
      "image_prompt": "Complete image prompt...",
      "motion_prompt": "Complete motion prompt...",
      "suggested_filename": "asset_id.png"
    }}
  ]
}}
```

This JSON is required for the automated asset generation pipeline to work."""

    # Save input (both system + user for full audit trail)
    input_path = reel_path / "03_visual_plan.input.md"
    input_content = f"""# Visual Plan Stage Input

## System Prompt

{system_prompt}

{"=" * 80}
========================== USER PROMPT BELOW ==========================
{"=" * 80}

{user_prompt}
"""
    write_file(input_path, input_content)

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt, stage="plan")

    # Save human-readable output
    output_md_path = reel_path / "03_visual_plan.output.md"
    write_file(output_md_path, f"# Visual Plan\n\n{response}")

    # Extract and save JSON output
    json_data = extract_json_from_response(response)
    output_json_path = reel_path / "03_visual_plan.output.json"
    
    if json_data:
        write_file(output_json_path, json.dumps(json_data, indent=2))
    else:
        # Create placeholder JSON if extraction failed
        placeholder = {
            "global_atmosphere": "EXTRACTION FAILED - Please manually create this file",
            "assets": [],
            "_error": "Could not extract JSON from LLM response. Check 03_visual_plan.output.md and manually create the JSON."
        }
        write_file(output_json_path, json.dumps(placeholder, indent=2))

    return output_md_path
