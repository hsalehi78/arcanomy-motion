"""AI-powered script generation for reels.

Uses LLM to transform a claim into a structured, compelling script
following the Arcanomy doctrine (dramatic arc, word counts, tone).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from src.config import get_default_provider
from src.services import LLMService
from src.utils.logger import get_logger

logger = get_logger()

# Word count constraints (doctrine)
MIN_WORDS_PER_SUBSEGMENT = 20
MAX_WORDS_PER_SUBSEGMENT = 35
TARGET_WORDS_PER_SUBSEGMENT = 27


SYSTEM_PROMPT = """You are the Lead Scriptwriter for Arcanomy short-form video reels.

Your goal: Transform a financial claim into a compelling script that stops the scroll, delivers one sharp insight, and earns the viewer's next 10 seconds at every beat.

## The Arcanomy Voice

Tone: Confident, slightly provocative, earned wisdom. Not preachy or lecturing.
Vocabulary: Accessible but not dumbed down. 8th-grade reading level with power words.
Rhythm: Short punchy sentences. Occasional longer sentence for breathing room. Never rambling.

## Dramatic Arc Structure

Every reel follows this structure:
1. **Hook (Block 1)**: Stop the scroll. Counter-intuitive truth, confrontation, or pattern interrupt.
2. **Support (Blocks 2-3)**: Evidence and proof. Specific data. Why this matters.
3. **Implication (Block 4)**: The hidden cost. What's at stake. The emotional punch.
4. **Landing (Block 5)**: Reframe the mental model. Call to action. Earned takeaway.

## Non-Negotiable Rules

1. Each subsegment MUST be 25-30 words (approximately 10 seconds of speech at 3 words/second)
2. Name the psychological trap or fallacy being exposed in the title
3. Use specific numbers, not vague statements ("10 years" not "years")
4. No em-dashes (—). Minimal commas. Keep it flowing.
5. First subsegment must stop the scroll in 3 seconds
6. Every statistic must feel weighty and specific

## Examples of Great Hooks

✅ "You don't have a timing problem. You have a permission problem."
✅ "The average millionaire goes bankrupt 3.5 times. You're afraid of failing once."
✅ "Everyone's chasing passive income. Nobody's building active patience."

## Examples of Bad Hooks (Avoid These)

❌ "Today I want to talk about investing..." (boring, educational tone)
❌ "Here are 5 tips to save money..." (list format, no emotional hook)
❌ "Did you know that many people..." (weak, vague)"""


USER_PROMPT_TEMPLATE = """Generate a {subsegment_count}-subsegment script for this claim:

CLAIM: "{claim_text}"

{data_context}

Output ONLY valid JSON in this exact format:
{{
  "title": "The [Trap/Fallacy Name]",
  "hook_type": "confrontation|question|statistic_punch|pattern_interrupt",
  "subsegments": [
    {{"id": "subseg-01", "beat": "hook_claim", "text": "Your hook text here. 25-30 words.", "word_count": 27}},
    {{"id": "subseg-02", "beat": "support_proof", "text": "Support and evidence. 25-30 words.", "word_count": 28}},
    {{"id": "subseg-03", "beat": "support_proof", "text": "More evidence or why it matters. 25-30 words.", "word_count": 26}},
    {{"id": "subseg-04", "beat": "implication_cost", "text": "The hidden cost and stakes. 25-30 words.", "word_count": 29}},
    {{"id": "subseg-05", "beat": "landing_reframe", "text": "Reframe and call to action. 25-30 words.", "word_count": 27}}
  ]
}}

CRITICAL: 
- Each text field MUST be 25-30 words. Count carefully before responding.
- The word_count field must match the actual word count of the text.
- The first subsegment must grab attention in the first 3 seconds.
- No em-dashes. Minimal punctuation. Natural speech rhythm."""


@dataclass
class ScriptSubsegment:
    """A single subsegment of the generated script."""
    id: str
    beat: str
    text: str
    word_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "beat": self.beat,
            "text": self.text,
            "word_count": self.word_count,
        }


@dataclass
class Script:
    """AI-generated script for a reel."""
    title: str
    hook_type: str
    subsegments: list[ScriptSubsegment] = field(default_factory=list)
    
    @property
    def voice_text_by_subsegment(self) -> dict[str, str]:
        """Return mapping of subsegment_id -> voice text."""
        return {ss.id: ss.text for ss in self.subsegments}
    
    @property
    def total_word_count(self) -> int:
        return sum(ss.word_count for ss in self.subsegments)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "hook_type": self.hook_type,
            "subsegments": [ss.to_dict() for ss in self.subsegments],
            "total_word_count": self.total_word_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Script":
        subsegments = [
            ScriptSubsegment(
                id=ss["id"],
                beat=ss["beat"],
                text=ss["text"],
                word_count=ss.get("word_count", len(ss["text"].split())),
            )
            for ss in data.get("subsegments", [])
        ]
        return cls(
            title=data.get("title", "Untitled"),
            hook_type=data.get("hook_type", "unknown"),
            subsegments=subsegments,
        )


def _count_words(text: str) -> int:
    """Count words in text (simple whitespace split)."""
    return len(text.split())


def _validate_script(script: Script, subsegment_count: int) -> list[str]:
    """Validate script against doctrine constraints. Returns list of errors."""
    errors: list[str] = []
    
    if len(script.subsegments) != subsegment_count:
        errors.append(
            f"Expected {subsegment_count} subsegments, got {len(script.subsegments)}"
        )
    
    for ss in script.subsegments:
        actual_words = _count_words(ss.text)
        if actual_words < MIN_WORDS_PER_SUBSEGMENT:
            errors.append(
                f"{ss.id}: Too few words ({actual_words} < {MIN_WORDS_PER_SUBSEGMENT})"
            )
        if actual_words > MAX_WORDS_PER_SUBSEGMENT:
            errors.append(
                f"{ss.id}: Too many words ({actual_words} > {MAX_WORDS_PER_SUBSEGMENT})"
            )
        # Check for em-dashes
        if "—" in ss.text or "--" in ss.text:
            errors.append(f"{ss.id}: Contains em-dash (prohibited)")
    
    return errors


def _fix_word_counts(script: Script) -> Script:
    """Recalculate word counts based on actual text."""
    for ss in script.subsegments:
        ss.word_count = _count_words(ss.text)
    return script


def _build_data_context(data: dict[str, Any] | None) -> str:
    """Build data context string from data.json contents."""
    if not data or data.get("type") == "none":
        return "DATA CONTEXT: No specific data provided. Focus on the claim itself."
    
    parts: list[str] = ["DATA CONTEXT:"]
    
    datasets = data.get("datasets", [])
    if datasets:
        parts.append("Available datasets:")
        for ds in datasets[:3]:  # Limit to first 3
            if isinstance(ds, dict):
                name = ds.get("name", "unnamed")
                desc = ds.get("description", "")
                parts.append(f"  - {name}: {desc}")
    
    charts = data.get("charts", [])
    if charts:
        parts.append(f"Charts available: {len(charts)}")
    
    return "\n".join(parts) if len(parts) > 1 else parts[0]


def generate_script(
    claim_text: str,
    data: dict[str, Any] | None = None,
    *,
    subsegment_count: int = 5,
    provider: str | None = None,
    max_retries: int = 2,
) -> Script:
    """Generate an AI-powered script from a claim.
    
    Args:
        claim_text: The sacred claim text from claim.json
        data: Optional data.json contents for context
        subsegment_count: Number of 10-second subsegments (default 5 = 50s)
        provider: LLM provider override (default: uses config default for 'script')
        max_retries: Number of retries if validation fails
        
    Returns:
        Script object with voice text for each subsegment
        
    Raises:
        ValueError: If script generation fails after retries
    """
    if not provider:
        provider = get_default_provider("script")
    
    llm = LLMService(provider=provider)
    data_context = _build_data_context(data)
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        subsegment_count=subsegment_count,
        claim_text=claim_text,
        data_context=data_context,
    )
    
    last_errors: list[str] = []
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"[AI Script] Generating script (attempt {attempt + 1}/{max_retries + 1})...")
            
            response = llm.complete_json(
                prompt=user_prompt,
                system=SYSTEM_PROMPT,
                stage="script",
            )
            
            script = Script.from_dict(response)
            script = _fix_word_counts(script)
            
            errors = _validate_script(script, subsegment_count)
            
            if not errors:
                logger.info(f"[AI Script] Generated '{script.title}' ({script.total_word_count} words)")
                return script
            
            last_errors = errors
            logger.warning(f"[AI Script] Validation errors: {errors}")
            
            # On retry, add error context to prompt
            if attempt < max_retries:
                user_prompt = USER_PROMPT_TEMPLATE.format(
                    subsegment_count=subsegment_count,
                    claim_text=claim_text,
                    data_context=data_context,
                ) + f"\n\nPREVIOUS ATTEMPT HAD ERRORS: {', '.join(errors)}\nPlease fix these issues."
                
        except json.JSONDecodeError as e:
            last_errors = [f"JSON parse error: {e}"]
            logger.warning(f"[AI Script] JSON parse error: {e}")
        except Exception as e:
            last_errors = [f"Generation error: {e}"]
            logger.error(f"[AI Script] Generation error: {e}")
    
    raise ValueError(
        f"Script generation failed after {max_retries + 1} attempts. "
        f"Last errors: {', '.join(last_errors)}"
    )


def generate_script_from_claim(
    claim: dict[str, Any],
    data: dict[str, Any] | None = None,
    *,
    subsegment_count: int = 5,
    provider: str | None = None,
) -> Script:
    """Convenience wrapper that takes a claim dict.
    
    Args:
        claim: Parsed claim.json dict with 'claim_text' key
        data: Optional parsed data.json dict
        subsegment_count: Number of subsegments
        provider: LLM provider override
        
    Returns:
        Script object
    """
    claim_text = claim.get("claim_text", "")
    if not claim_text:
        raise ValueError("claim.json must have a 'claim_text' field")
    
    return generate_script(
        claim_text=claim_text,
        data=data,
        subsegment_count=subsegment_count,
        provider=provider,
    )


def get_fallback_voice_text(
    claim_text: str,
    subsegment_ids: list[str],
) -> dict[str, str]:
    """Return deterministic fallback voice text (non-AI).
    
    Used when AI generation fails or is disabled.
    """
    if len(subsegment_ids) < 1:
        return {}
    
    fallback = {
        0: claim_text,
        1: "Here's the proof.",
        2: "And why it matters.",
        3: "The hidden cost is time.",
        4: "Decide—then move.",
    }
    
    return {
        sid: fallback.get(i, f"Subsegment {i + 1}.")
        for i, sid in enumerate(subsegment_ids)
    }

