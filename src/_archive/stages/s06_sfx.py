"""Stage 6: Sound Effects Prompt Engineering - Create SFX prompts for each clip.

This is a Smart Agent stage that:
1. Reads the script segments from Stage 2
2. Reads the visual plan from Stage 3 (for scene context)
3. Creates sound effect prompts for each segment
4. Produces a Sound Effects Prompt Table
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.domain import Objective
from src.services import LLMService
from src.utils.io import read_file, write_file
from src.utils.paths import json_path, prompt_path

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_sfx_system_prompt() -> str:
    """Load the sound effects system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "06_sound_effects_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    # Fallback if file missing
    return """You are a sound effects designer for documentary-style video content.
Create atmospheric sound effect prompts for each video segment.
Each prompt should describe continuous ambient sounds with action sounds layered on top.
Target 30-50 words per prompt, ending with "subtle documentary sound effect"."""


def extract_json_from_response(response: str) -> dict | None:
    """Extract JSON from LLM response that may contain markdown."""
    # Try to find JSON code block
    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON object with sound_effects array
    json_match = re.search(r'\{[\s\S]*"sound_effects"[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def run_sfx_prompting(reel_path: Path, llm: LLMService) -> Path:
    """Generate sound effect prompts for each video segment.

    This stage:
    1. Reads script segments from Stage 2
    2. Reads visual plan from Stage 3 for scene context
    3. Creates tailored SFX prompts for each segment
    4. Outputs a Sound Effects Prompt Table

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the sound effects output JSON
    """
    objective = Objective.from_reel_folder(reel_path)
    system_prompt = load_sfx_system_prompt()

    # Load script segments
    segments_json_path = json_path(reel_path, "02_story_generator.output.json")
    segments_json = ""
    segments_data = None
    if segments_json_path.exists():
        segments_json = read_file(segments_json_path)
        try:
            segments_data = json.loads(segments_json)
        except json.JSONDecodeError:
            pass

    # Load visual plan for scene context
    visual_plan_path = json_path(reel_path, "03_visual_plan.output.json")
    visual_plan_json = ""
    if visual_plan_path.exists():
        visual_plan_json = read_file(visual_plan_path)

    # Also load human-readable visual plan for context
    visual_plan_md_path = prompt_path(reel_path, "03_visual_plan.output.md")
    visual_plan_md = ""
    if visual_plan_md_path.exists():
        visual_plan_md = read_file(visual_plan_md_path)

    # Count segments
    num_segments = 0
    if segments_data:
        segments_list = segments_data.get("segments", segments_data)
        if isinstance(segments_list, list):
            num_segments = len(segments_list)

    user_prompt = f"""# Sound Effects Prompt Engineering Request

## Reel Configuration
- **Title:** {objective.title}
- **Type:** {objective.type}
- **Duration:** {objective.duration_blocks} blocks ({objective.duration_seconds} seconds)
- **Total Segments:** {num_segments}

## Production Script (Segments from Stage 2)

```json
{segments_json[:4000] if segments_json else "N/A"}
```

## Visual Plan (Scene Context from Stage 3)

```json
{visual_plan_json[:3000] if visual_plan_json else "N/A"}
```

## Visual Plan Details
{visual_plan_md[:2000] if visual_plan_md else "N/A"}

---

## Your Task

Create sound effect prompts for EACH of the {num_segments} segments.

For EACH segment:
1. Analyze the `text` and `visual_intent` from the script
2. Determine the scene environment (indoor, outdoor, office, urban, etc.)
3. Identify 3-4 continuous ambient sounds for that environment
4. Identify action sounds that should layer on top
5. Craft a 30-50 word prompt following this structure:

```
Continuous [environment] ambience with [sound 1], [sound 2], [sound 3],
with [action sound] layered on top, [mood descriptor], subtle documentary sound effect
```

**CRITICAL RULES:**
- Each prompt MUST start with "Continuous [environment] ambience with..."
- Each prompt MUST end with "subtle documentary sound effect"
- Each prompt MUST be 30-50 words
- NO gaps of silence - continuous ambient bed throughout
- Match the emotional tone of each segment
- Realistic sounds only (no music, no fantasy elements)

## Output Format

Provide:
1. A markdown table with all {num_segments} sound effect prompts
2. A JSON block with structured data

**JSON Structure:**
```json
{{
  "generated_at": "TIMESTAMP",
  "total_clips": {num_segments},
  "sound_effects": [
    {{
      "clip_number": 1,
      "segment_id": 1,
      "scene_summary": "Brief description",
      "environment": "setting type",
      "continuous_sounds": ["sound1", "sound2", "sound3"],
      "action_sounds": ["action1"],
      "mood": "emotional tone",
      "prompt": "Continuous [env] ambience with...",
      "duration_seconds": 10
    }}
  ]
}}
```
"""

    # Save input for audit trail
    input_path = prompt_path(reel_path, "06_sound_effects.input.md")
    input_content = f"""# Sound Effects Prompt Engineering Stage Input

## System Prompt

{system_prompt}

{"=" * 80}
========================== USER PROMPT BELOW ==========================
{"=" * 80}

{user_prompt}
"""
    write_file(input_path, input_content)

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt, stage="sfx")

    # Save human-readable output
    output_md_path = prompt_path(reel_path, "06_sound_effects.output.md")
    write_file(output_md_path, f"# Sound Effects Prompts\n\n{response}")

    # Extract and save JSON output
    json_data = extract_json_from_response(response)
    output_json_path = json_path(reel_path, "06_sound_effects.output.json")

    if json_data:
        # Ensure metadata is present
        if "generated_at" not in json_data:
            json_data["generated_at"] = datetime.now(timezone.utc).isoformat()
        if "total_clips" not in json_data:
            json_data["total_clips"] = len(json_data.get("sound_effects", []))
        write_file(output_json_path, json.dumps(json_data, indent=2))
    else:
        # Create fallback JSON from segments if extraction failed
        sound_effects = []
        if segments_data:
            segments_list = segments_data.get("segments", segments_data)
            if isinstance(segments_list, list):
                for seg in segments_list:
                    seg_id = seg.get("id", 1)
                    visual_intent = seg.get("visual_intent", "")
                    text = seg.get("text", "")

                    # Create a basic fallback prompt
                    fallback_prompt = (
                        f"Continuous ambient atmosphere with soft room tone, "
                        f"subtle environmental sounds, gentle background hum, "
                        f"with occasional movement sounds layered on top, "
                        f"calm documentary mood, subtle documentary sound effect"
                    )

                    sound_effects.append(
                        {
                            "clip_number": seg_id,
                            "segment_id": seg_id,
                            "scene_summary": visual_intent[:100] if visual_intent else text[:100],
                            "environment": "general indoor",
                            "continuous_sounds": ["room tone", "ambient hum", "subtle background"],
                            "action_sounds": ["movement sounds"],
                            "mood": "neutral documentary",
                            "prompt": fallback_prompt,
                            "duration_seconds": 10,
                        }
                    )

        fallback = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_clips": len(sound_effects),
            "sound_effects": sound_effects,
            "_warning": "JSON extraction failed. Using fallback prompts. Check 06_sound_effects.output.md for LLM response.",
        }
        write_file(output_json_path, json.dumps(fallback, indent=2))

    return output_json_path

