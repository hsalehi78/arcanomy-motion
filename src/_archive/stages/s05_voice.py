"""Stage 5: Voice Prompting - Generate optimized narration for TTS.

This is a Smart Agent stage that:
1. Reads the script segments from Stage 2
2. Optimizes narration text to fit the 8-second audio target
3. Produces an Audio Generation Table with word counts and duration estimates
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.config import get_default_voice_id
from src.domain import Objective
from src.services import LLMService
from src.utils.io import read_file, write_file
from src.utils.paths import json_path, prompt_path

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_voice_system_prompt() -> str:
    """Load the voice system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "05_voice_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    # Fallback if file missing
    return """You are a voice director for short-form video content.
Optimize narration text to fit 8-second audio duration targets.
Each line should be 10 words or less with minimal punctuation."""


def extract_json_from_response(response: str) -> dict | None:
    """Extract JSON from LLM response that may contain markdown."""
    # Try to find JSON code block
    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON object with narrations array
    json_match = re.search(r'\{[\s\S]*"narrations"[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def run_voice_prompting(reel_path: Path, llm: LLMService) -> Path:
    """Generate optimized narration text for TTS.

    This stage:
    1. Reads script segments from Stage 2
    2. Optimizes each narration to target 8-second duration
    3. Produces an Audio Generation Table

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        Path to the voice direction output JSON
    """
    objective = Objective.from_reel_folder(reel_path)
    system_prompt = load_voice_system_prompt()

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

    # Also load human-readable script for context
    script_md_path = prompt_path(reel_path, "02_story_generator.output.md")
    script_md = ""
    if script_md_path.exists():
        script_md = read_file(script_md_path)

    # Get voice config from reel settings (fallback to config default)
    default_voice = get_default_voice_id("elevenlabs")
    voice_id = getattr(objective, "voice_id", default_voice)

    user_prompt = f"""# Voice Direction Request

## Reel Configuration
- **Title:** {objective.title}
- **Type:** {objective.type}
- **Duration:** {objective.duration_blocks} blocks ({objective.duration_seconds} seconds)
- **Voice ID:** {voice_id}

## Production Script (Segments from Stage 2)

```json
{segments_json}
```

## Human-Readable Script
{script_md[:2000] if script_md else "N/A"}

---

## Your Task

Create the **Audio Generation Table** for this script.

For EACH segment:
1. Take the original `text` from the segment
2. Count words and punctuation marks (periods, commas)
3. Calculate estimated duration: (words ÷ 2) + (punctuation × 2) + 1
4. If duration > 8 seconds: REWRITE to reduce words or remove punctuation
5. Ensure NO em-dashes are used

**Target: 8 seconds per narration (range: 7-9 seconds)**

Provide:
1. A markdown table showing the analysis
2. A JSON block with the optimized narrations

**CRITICAL:** Each optimized narration should:
- Be 20-24 words (target 8 seconds at 2.5-3 words/second)
- Use 2-3 sentences with natural punctuation
- Avoid em-dashes (use commas or periods instead)
- Sound natural and documentary-like
- Preserve the core message from the original
"""

    # Save input for audit trail
    input_path = prompt_path(reel_path, "05_voice.input.md")
    input_content = f"""# Voice Direction Stage Input

## System Prompt

{system_prompt}

{"=" * 80}
========================== USER PROMPT BELOW ==========================
{"=" * 80}

{user_prompt}
"""
    write_file(input_path, input_content)

    # Call LLM
    response = llm.complete(user_prompt, system=system_prompt, stage="voice")

    # Save human-readable output
    output_md_path = prompt_path(reel_path, "05_voice.output.md")
    write_file(output_md_path, f"# Voice Direction & Audio Generation Table\n\n{response}")

    # Extract and save JSON output
    json_data = extract_json_from_response(response)
    output_json_path = json_path(reel_path, "05_voice.output.json")

    if json_data:
        # Ensure metadata is present
        if "generated_at" not in json_data:
            json_data["generated_at"] = datetime.now(timezone.utc).isoformat()
        if "voice_config" not in json_data:
            json_data["voice_config"] = {
                "stability": 0.40,
                "similarity_boost": 0.75,
                "style": 0.12,
            }
        write_file(output_json_path, json.dumps(json_data, indent=2))
    else:
        # Create fallback JSON from original segments if extraction failed
        narrations = []
        if segments_data:
            segments_list = segments_data.get("segments", segments_data)
            if isinstance(segments_list, list):
                for seg in segments_list:
                    text = seg.get("text", "")
                    word_count = len(text.split())
                    # Count punctuation
                    punct_count = text.count(".") + text.count(",") + text.count("—")
                    est_duration = (word_count / 2) + (punct_count * 2) + 1

                    narrations.append(
                        {
                            "sequence": seg.get("id", 1),
                            "segment_id": seg.get("id", 1),
                            "original_text": text,
                            "optimized_text": text,  # Use original as fallback
                            "word_count": word_count,
                            "punctuation_count": punct_count,
                            "estimated_duration_seconds": round(est_duration, 1),
                        }
                    )

        fallback = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "voice_config": {
                "stability": 0.40,
                "similarity_boost": 0.75,
                "style": 0.12,
            },
            "narrations": narrations,
            "_warning": "JSON extraction failed. Using original segment text. Check 05_voice.output.md for LLM response.",
        }
        write_file(output_json_path, json.dumps(fallback, indent=2))

    return output_json_path

