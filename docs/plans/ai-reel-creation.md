# AI Reel Creation Plan

**Status:** ✅ Implemented  
**Author:** Arcanomy Engineering  
**Date:** 2025-12-21

---

## Overview

AI Reel Creation enables automatic script generation from a simple claim using LLMs. Instead of manually writing voice text for each subsegment, the AI generates a complete, structured script following the Arcanomy doctrine.

---

## Current State

The current planner (`src/pipeline/planner.py`) uses **hardcoded placeholder text**:

```python
voice_text = {
    subsegment_ids[0]: claim.claim_text,
    subsegment_ids[1]: "Here's the proof.",
    subsegment_ids[2]: "And why it matters.",
    subsegment_ids[3]: "The hidden cost is time.",
    subsegment_ids[4]: "Decide—then move.",
}
```

This creates valid pipeline outputs but produces generic, non-compelling content.

---

## Target State

With `--ai` flag enabled, the pipeline will:

1. **Analyze the claim** from `claim.json`
2. **Generate a dramatic arc** following the Arcanomy structure:
   - Hook (Block 1): Counter-intuitive truth that stops the scroll
   - Support (Block 2-3): Evidence and proof with specific data
   - Implication (Block 4): The hidden cost or stakes
   - Landing (Block 5): Reframe and call to action
3. **Produce voice text** for each subsegment (25-30 words each)
4. **Validate** output follows the doctrine constraints

---

## Architecture

### New Module: `src/pipeline/scriptwriter.py`

```
┌─────────────────────────────────────────────────────────────┐
│                      scriptwriter.py                        │
├─────────────────────────────────────────────────────────────┤
│  generate_script(claim, data, subsegment_count) -> Script   │
│                                                             │
│  Uses LLMService to:                                        │
│  1. Generate dramatic arc from claim                        │
│  2. Write voice text per subsegment (25-30 words each)      │
│  3. Validate word counts and structure                      │
└─────────────────────────────────────────────────────────────┘
```

### Integration Point: `src/pipeline/planner.py`

```python
def generate_plan(reel_path, *, force=False, ai=False):
    # ... existing setup ...
    
    if ai:
        from src.pipeline.scriptwriter import generate_script
        script = generate_script(claim, data, subsegment_count=5)
        voice_text = script.voice_text_by_subsegment
    else:
        # Use deterministic placeholders (current behavior)
        voice_text = {...}
```

### CLI Enhancement: `src/commands.py`

```bash
# New usage
uv run arcanomy run <path> --ai        # Enable AI script generation
uv run arcanomy run <path> --ai -s plan  # Generate AI plan only
```

---

## Script Generation Prompt

The scriptwriter uses a carefully crafted prompt based on the Arcanomy doctrine:

### System Prompt

```
You are the Lead Scriptwriter for Arcanomy short-form video reels.

Your goal: Transform a financial claim into a 50-second script that stops the scroll, 
delivers one sharp insight, and earns the viewer's next 10 seconds at every beat.

RULES (Non-Negotiable):
1. Each subsegment must be 25-30 words (approximately 10 seconds of speech)
2. Follow the dramatic arc: Hook → Support → Implication → Landing
3. Name the psychological trap or fallacy being exposed
4. Use specific numbers, not vague statements
5. Write in a confident, slightly provocative tone—not preachy
6. No em-dashes. Minimal commas. Keep it flowing.
```

### User Prompt Template

```
Generate a 5-subsegment script for this claim:

CLAIM: "{claim_text}"

DATA CONTEXT: {data_summary}

Output as JSON:
{
  "title": "The [Trap Name]",
  "hook_type": "confrontation|question|statistic_punch",
  "subsegments": [
    {"id": "subseg-01", "beat": "hook_claim", "text": "...", "word_count": N},
    {"id": "subseg-02", "beat": "support_proof", "text": "...", "word_count": N},
    {"id": "subseg-03", "beat": "support_proof", "text": "...", "word_count": N},
    {"id": "subseg-04", "beat": "implication_cost", "text": "...", "word_count": N},
    {"id": "subseg-05", "beat": "landing_reframe", "text": "...", "word_count": N}
  ]
}
```

---

## Word Count Constraints

| Target Duration | Word Count | Notes |
|-----------------|------------|-------|
| 10s tight       | 20-24 words | Minimal punctuation |
| 10s comfortable | 25-30 words | Natural pacing |
| 10s+ buffer     | 28-32 words | Deliberate pauses |

**Formula:** ~3 words = 1 second of speech (ElevenLabs at natural pace)

---

## Validation Rules

The scriptwriter validates:

1. **Word count**: Each subsegment must be 20-35 words (hard limits)
2. **Total duration**: Sum of word counts should target ~150 words total
3. **Structure**: Must have exactly 5 subsegments
4. **No prohibited characters**: No em-dashes (—), limited punctuation
5. **Trap naming**: Title should name a psychological trap

---

## Error Handling

If AI generation fails:
1. Log the error with context
2. Fall back to deterministic placeholders
3. Mark in provenance that AI generation was attempted but failed

---

## Configuration

Uses existing `src/config.py` settings:

```python
DEFAULT_PROVIDERS = {
    "script": "anthropic",  # claude-opus-4.5 for creative writing
}
```

The scriptwriter uses `stage="script"` for model selection, allowing stage-specific overrides.

---

## Blog Seed Extraction Flow

When ingesting a blog, we use a 3-step LLM pipeline:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SEED EXTRACTION PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Blog MDX ──► [1] ANTHROPIC (opus 4.5) ──► Initial extraction       │
│                   "Creative Extractor"      (hook, insight, vibe)   │
│                                                                     │
│              ──► [2] OPENAI (gpt-5.2) ──► Verification              │
│                   "Fact Checker"            (verify claims vs blog) │
│                                                                     │
│              ──► [3] ANTHROPIC (opus 4.5) ──► Final refinement      │
│                   "Creative Refiner"         (polish & enhance)     │
│                                                                     │
│                                        ──► seed.md + claim.json     │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Flow?

1. **Anthropic (Creative)**: Best at understanding narrative, extracting compelling hooks
2. **OpenAI (Analytical)**: Best at fact-checking, verifying claims against source
3. **Anthropic (Creative)**: Best at final polish, making the hook punchy

### Configuration

```python
SEED_EXTRACTION = {
    "extractor": "anthropic",    # Step 1: Creative extraction
    "verifier": "openai",        # Step 2: Fact verification
    "refiner": "anthropic",      # Step 3: Final polish
}
```

### Checklist Compliance

The seed extraction enforces the Arcanomy Operating System checklist:

**A. Pre-Recording Compliance:**
- ✅ Reel topic fits one of 5 formats (contrarian_truth, math_slap, checklist, story_lesson, myth_bust)
- ✅ Script follows: truth → mistake → fix
- ✅ Script under 60 seconds (~150 words)
- ✅ No motivation-dependent language

**Prompts enforce:**
- Step 1 (Anthropic): Extracts in truth→mistake→fix format, picks one of 5 allowed formats
- Step 2 (OpenAI): Verifies compliance, checks stats against blog
- Step 3 (Anthropic): Final polish, ensures punchiness

---

## Testing Strategy

1. **Unit tests** for word count validation
2. **Integration tests** with mocked LLM responses
3. **Manual testing** with real API calls on sample claims

---

## Implementation Checklist

- [x] Create plan document (`docs/plans/ai-reel-creation.md`)
- [x] Create `src/pipeline/scriptwriter.py` module
- [x] Update `src/pipeline/planner.py` with `ai=False` parameter
- [x] Update `src/commands.py` with `--ai` flag
- [x] Update `src/pipeline/__init__.py` exports
- [ ] Add unit tests for scriptwriter

---

## Example Output

**Input claim.json:**
```json
{
  "claim_id": "permission-trap",
  "claim_text": "The average person wastes 10 years waiting for the right moment.",
  "supporting_data_ref": "ds-01",
  "audit_level": "basic"
}
```

**Generated script (AI):**
```json
{
  "title": "The Permission Trap",
  "hook_type": "confrontation",
  "subsegments": [
    {
      "id": "subseg-01",
      "beat": "hook_claim",
      "text": "You don't have a timing problem. You have a permission problem. Every time you wait for the perfect moment, you're giving yourself permission to stay stuck.",
      "word_count": 29
    },
    {
      "id": "subseg-02",
      "beat": "support_proof",
      "text": "The average person spends ten years waiting. Not preparing. Not researching. Just waiting. For a sign that never comes. For certainty that doesn't exist.",
      "word_count": 28
    },
    {
      "id": "subseg-03",
      "beat": "support_proof",
      "text": "Missing just ten of the best market days in twenty years cuts your returns in half. The cost of waiting isn't zero. It's everything.",
      "word_count": 28
    },
    {
      "id": "subseg-04",
      "beat": "implication_cost",
      "text": "Every year you wait, compound interest works for someone else. Your future self is paying for your present hesitation. Time is the only resource you can't earn back.",
      "word_count": 30
    },
    {
      "id": "subseg-05",
      "beat": "landing_reframe",
      "text": "The perfect moment is a myth. Start ugly. Start scared. Start confused. The only wrong move is no move at all. Decide, then move.",
      "word_count": 28
    }
  ]
}
```

---

## Future Enhancements

1. **Visual intent generation**: AI-generate `visual_intent` for each subsegment
2. **Chart suggestions**: Analyze data.json and suggest chart placements
3. **Multiple script options**: Generate 3 angles, let user pick
4. **Iterative refinement**: Allow user to regenerate individual subsegments

