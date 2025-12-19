"""Stage 4: Video Prompt Engineering - Refine motion prompts for video AI generation."""

import json
import re
from pathlib import Path

from src.domain import Objective
from src.services import LLMService
from src.utils.io import read_file, write_file
from src.utils.paths import images_composites_dir, json_path, prompt_path

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_system_prompt() -> str:
    """Load the video prompt system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "04_video_prompt_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    # Fallback if file missing
    return """You are a Technical Director and AI Prompt Specialist for video production.
Your job is to translate Visual Plans into production-ready video prompts optimized for Kling 2.5 / Runway.

Key Rules:
1. 10-second constraint: Focus on micro-movements, not character displacement
2. Image anchor logic: Motion must match the seed image
3. Priority order: Core action FIRST, camera movement LAST
4. Plain language: Clear, specific sentences - no flowery descriptions
5. Every clip MUST end with exactly ONE camera movement

Output both human-readable markdown AND a JSON block with the video shot list."""


def extract_json_from_response(response: str) -> dict | None:
    """Extract JSON from LLM response that may contain markdown."""
    # Try to find JSON code block
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find raw JSON object with clips array
    json_match = re.search(r'\{[\s\S]*"clips"[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def run_video_prompting(reel_path: Path, llm: LLMService) -> Path:
    """Generate production-ready video prompts from visual plan.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the video prompt output file
    """
    objective = Objective.from_reel_folder(reel_path)
    system_prompt = load_system_prompt()

    # Load visual plan (Stage 3 output)
    visual_plan_json_path = json_path(reel_path, "03_visual_plan.output.json")
    visual_plan_md_path = prompt_path(reel_path, "03_visual_plan.output.md")
    
    visual_plan_json = ""
    visual_plan_md = ""
    
    if visual_plan_json_path.exists():
        visual_plan_json = read_file(visual_plan_json_path)
    if visual_plan_md_path.exists():
        visual_plan_md = read_file(visual_plan_md_path)

    # Load script segments (for context on segment-to-asset mapping)
    segments_json_path = json_path(reel_path, "02_story_generator.output.json")
    segments_json = ""
    if segments_json_path.exists():
        segments_json = read_file(segments_json_path)

    # Check which assets have been generated
    renders_path = images_composites_dir(reel_path)
    existing_assets = []
    if renders_path.exists():
        existing_assets = [f.name for f in renders_path.iterdir() if f.suffix == ".png"]

    user_prompt = f"""# Video Prompt Engineering Request

## Reel Configuration
- **Title:** {objective.title}
- **Type:** {objective.type}
- **Duration:** {objective.duration_blocks} blocks ({objective.duration_seconds} seconds)

## Visual Plan (03_visual_plan.output.json)

```json
{visual_plan_json}
```

## Visual Plan (Human-Readable)
{visual_plan_md}

## Production Script (02_story_generator.output.json)

```json
{segments_json}
```

## Generated Assets
The following images exist in `renders/images/composites/`:
{chr(10).join(f"- {asset}" for asset in existing_assets) if existing_assets else "- No assets generated yet"}

---

## Your Task

Generate the complete Video Shot List following the structure in your system prompt:

1. **Part 1: Asset Review & Scene Analysis** - Review each asset for motion feasibility
2. **Part 2: Video Shot List** - Table of all clips with refined prompts
3. **Part 3: Complete Video Prompts** - Full production prompts per clip

**CRITICAL RULES:**
- Core action FIRST, camera movement LAST in every prompt
- Use plain language - no flowery descriptions
- Every clip MUST end with exactly ONE camera movement
- Motion must be sustainable for 10 seconds (slow, subtle movements)
- Motion must match what's visible in the seed image

**CRITICAL:** At the end of your response, include a JSON block with this structure:

```json
{{
  "generated_at": "2025-12-18T10:00:00Z",
  "total_clips": 2,
  "clips": [
    {{
      "clip_number": 1,
      "segment_id": 1,
      "seed_image": "renders/images/composites/object_clock_spinning.png",
      "video_prompt": "Clock face glows in dim light. Second hand ticks forward slowly. Red and blue light flickers on glass surface. Screen reflection pulses in background. Slow push in.",
      "camera_movement": "Slow push in",
      "duration_seconds": 10,
      "movement_type": "micro",
      "notes": "Opening tension shot"
    }}
  ]
}}
```

This JSON is required for the automated video generation pipeline (Stage 4.5) to work."""

    # Save input (both system + user for full audit trail)
    input_path = prompt_path(reel_path, "04_video_prompt.input.md")
    input_content = f"""# Video Prompt Stage Input

## System Prompt

{system_prompt}

{"=" * 80}
========================== USER PROMPT BELOW ==========================
{"=" * 80}

{user_prompt}
"""
    write_file(input_path, input_content)

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt, stage="vidprompt")

    # Save human-readable output
    output_md_path = prompt_path(reel_path, "04_video_prompt.output.md")
    write_file(output_md_path, f"# Video Shot List\n\n{response}")

    # Extract and save JSON output
    json_data = extract_json_from_response(response)
    output_json_path = json_path(reel_path, "04_video_prompt.output.json")
    
    if json_data:
        write_file(output_json_path, json.dumps(json_data, indent=2))
    else:
        # Create placeholder JSON if extraction failed
        placeholder = {
            "generated_at": None,
            "total_clips": 0,
            "clips": [],
            "_error": "Could not extract JSON from LLM response. Check 04_video_prompt.output.md and manually create the JSON."
        }
        write_file(output_json_path, json.dumps(placeholder, indent=2))

    return output_md_path

