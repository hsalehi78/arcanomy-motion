"""Stage 2: Script - Write voiceover and segment into 10s blocks."""

import json
from pathlib import Path

from src.domain import Objective, Segment
from src.services import LLMService
from src.utils.io import read_file, write_file

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_system_prompt() -> str:
    """Load the script system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "02_script_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    # Fallback if file missing
    return """You are a scriptwriter for short-form financial video content.
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


def run_script(reel_path: Path, llm: LLMService) -> list[Segment]:
    """Generate script and segment it into 10-second blocks.

    Args:
        reel_path: Path to the reel folder
        llm: LLM service instance

    Returns:
        List of Segment objects
    """
    objective = Objective.from_reel_folder(reel_path)
    system_prompt = load_system_prompt()

    # Load research if available
    research_path = reel_path / "01_research.output.md"
    research = read_file(research_path) if research_path.exists() else ""

    # Load reel config for additional context
    config_path = reel_path / "00_reel.yaml"
    config_yaml = read_file(config_path) if config_path.exists() else ""

    user_prompt = f"""# Script Generation Request

## Configuration
- **Duration:** {objective.duration_blocks} blocks ({objective.duration_seconds} seconds)
- **Type:** {objective.type}

## Creative Brief (from 00_seed.md)

### Hook
> {objective.hook}

### Core Insight
> {objective.core_insight}

### Visual Vibe
> {objective.visual_vibe}

---

## Research (from 01_research.output.md)

{research if research else "*No research available. Generate script from seed only.*"}

---

## Instructions

Since this is an automated pipeline run, skip Phase 1 (story options) and proceed directly to Phase 2 (production scripting).

Generate a {objective.duration_blocks}-block production script following the JSON format:

```json
{{
  "title": "The Title",
  "total_duration_seconds": {objective.duration_seconds},
  "segments": [
    {{
      "id": 1,
      "duration": 10,
      "text": "Voiceover text here (25-30 words)",
      "visual_intent": "Shot Type: ... Subject: ... Environment: ... Movement: ...",
      "word_count": 27
    }}
  ]
}}
```

**Constraints:**
- Each segment MUST be 25-30 words
- Each segment MUST have visual_intent with Shot Type, Subject, Environment, Movement
- All statistics MUST come from the research document
- First segment MUST stop the scroll (the hook)
- Story MUST have clear arc: Hook → Tension → Evidence → Reframe → Resolution

Return ONLY valid JSON. No markdown code fences."""

    # Save input (both system + user for full audit trail)
    input_path = reel_path / "02_story_generator.input.md"
    input_content = f"""# Script Stage Input

## System Prompt

{system_prompt}

{"=" * 80}
========================== USER PROMPT BELOW ==========================
{"=" * 80}

{user_prompt}
"""
    write_file(input_path, input_content)

    # Call LLM for JSON response
    response = llm.complete_json(user_prompt, system=system_prompt, stage="script")

    # Parse segments
    segments_data = response.get("segments", [])
    segments = [Segment.from_dict(s) for s in segments_data]

    # Save human-readable output
    output_md_path = reel_path / "02_story_generator.output.md"
    title = response.get("title", "Untitled")
    total_duration = response.get("total_duration_seconds", objective.duration_seconds)
    
    script_text = f"**Title:** {title}\n"
    script_text += f"**Total Duration:** {total_duration}s ({len(segments)} blocks)\n\n"
    script_text += "---\n\n"
    
    for s in segments:
        word_count = len(s.text.split()) if s.text else 0
        script_text += f"## Block {s.id} ({s.duration}s) — {word_count} words\n\n"
        script_text += f"> {s.text}\n\n"
        script_text += f"**Visual:** {s.visual_intent}\n\n"
        script_text += "---\n\n"
    
    write_file(output_md_path, f"# Generated Script\n\n{script_text}")

    # Save JSON output
    output_json_path = reel_path / "02_story_generator.output.json"
    write_file(
        output_json_path,
        json.dumps(response, indent=2),
    )

    return segments
