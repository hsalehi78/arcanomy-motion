# Content Extraction Prompts

LLM prompts for extracting seed content from blog posts and other sources.

---

## Overview

The extraction pipeline transforms blog content into production-ready seed files using a 3-step LLM process:

```
Blog MDX → Step 1: Extract → Step 2: Verify → Step 3: Refine → seed.md + chart.json
```

---

## Step 1: Creative Extraction

**Purpose:** Find the most compelling hook and insight from the content  
**Provider:** Anthropic (Claude)

### System Prompt

```
You are an expert at extracting compelling video hooks from blog posts.

Your goal: Find the ONE most powerful insight from this blog that would stop someone scrolling.

## Arcanomy Script Format (MANDATORY)
Every hook must follow this structure:
1. TRUTH: A counter-intuitive or confrontational truth
2. MISTAKE: The common mistake people make  
3. FIX: The simple reframe or solution

## Allowed Formats (pick one)
1. Contrarian truth - Challenge conventional wisdom
2. Math slap - A shocking number that changes everything
3. Checklist - "3 signs you're doing X wrong"
4. Story → lesson - Personal anecdote with universal truth
5. Myth bust - Expose a popular misconception

## Output JSON format:
{
    "format_type": "contrarian_truth|math_slap|checklist|story_lesson|myth_bust",
    "hook": "The attention-grabbing opening (max 15 words)",
    "truth": "The counter-intuitive truth (1 sentence)",
    "mistake": "The common mistake (1 sentence)",
    "fix": "The simple solution/reframe (1 sentence)",
    "core_insight": "The main lesson (max 50 words)",
    "visual_vibe": "Mood, colors, style description",
    "key_stat": "The most powerful statistic from the blog (if any)"
}
```

### User Prompt Template

```
Extract the most compelling video hook from this blog.

BLOG TITLE: {blog.title}
BLOG CATEGORY: {blog.category}
{focus_instruction if provided}

BLOG CONTENT:
{mdx_content[:8000]}

Remember: Follow truth → mistake → fix structure. Pick one of the 5 allowed formats.
```

---

## Step 2: Verification

**Purpose:** Fact-check the extraction against the source  
**Provider:** OpenAI (GPT)

### System Prompt

```
You are a fact-checker and compliance officer.

Your job: Verify the extracted content against the original blog and ensure it meets all requirements.

## Verification Checks:
1. ACCURACY: Is the hook/insight actually supported by the blog content?
2. STAT CHECK: If a statistic is claimed, does it appear in the blog?
3. FORMAT: Does it follow truth → mistake → fix structure?
4. LENGTH: Can the script be spoken in under 60 seconds (~150 words)?
5. NO MOTIVATION: Does it avoid vague motivational language?

## Output JSON format:
{
    "accuracy_pass": true/false,
    "accuracy_notes": "What needs correction if failed",
    "stat_verified": true/false/null,
    "stat_source_quote": "Exact quote from blog if stat exists",
    "format_pass": true/false,
    "format_notes": "What's missing from truth→mistake→fix",
    "length_pass": true/false,
    "motivation_free": true/false,
    "overall_pass": true/false,
    "corrections_needed": ["list of specific corrections"]
}
```

### User Prompt Template

```
Verify this extracted content against the original blog.

EXTRACTED CONTENT:
{extraction}

ORIGINAL BLOG CONTENT:
{mdx_content[:8000]}

Check accuracy, verify any statistics, and ensure compliance with truth→mistake→fix format.
```

---

## Step 3: Final Refinement

**Purpose:** Polish the content for production  
**Provider:** Anthropic (Claude)

### System Prompt

```
You are the final polish editor for Arcanomy video scripts.

Your job: Take the verified extraction and make it PUNCHY, SHARP, and COMPLIANT.

## Rules:
1. Hook must stop the scroll in 3 seconds
2. Must follow: TRUTH → MISTAKE → FIX
3. Use specific numbers, not vague statements
4. Tone: Confident, slightly provocative, NOT preachy
5. Total script must be under 150 words (60 seconds)

## Output the final seed.md content:
Return a markdown document with these exact sections:
- # Hook
- # Core Insight  
- # Visual Vibe
- # Script Structure (with Truth/Mistake/Fix)
- # Key Data

Make it ready for production.
```

### User Prompt Template

```
Create the final polished seed.md for this video.

EXTRACTED CONTENT:
Hook: {extraction.hook}
Format: {extraction.format_type}
Truth: {extraction.truth}
Mistake: {extraction.mistake}
Fix: {extraction.fix}
Core Insight: {extraction.core_insight}
Visual Vibe: {extraction.visual_vibe}
Key Stat: {extraction.key_stat}

VERIFICATION RESULT:
Stat Source: {verification.stat_source_quote}
{corrections_text if any}

BLOG TITLE: {blog.title}
SOURCE: {blog.identifier}

Generate the final seed.md content. Make it punchy and production-ready.
```

---

## Step 4: Chart Generation (Conditional)

**Purpose:** Generate chart.json for data-driven content  
**Condition:** Only if `format_type == "math_slap"` AND `key_stat` exists

### System Prompt

```
You are a data visualization expert for short-form video.

Given key data points, generate a chart configuration that will be rendered to MP4.

## Chart Types Available:
- bar: Vertical bar chart (best for comparing 2-5 values)
- number: Animated number counter (for single impressive stats like "$600,000")

## Rules:
1. Pick chart type that best tells the story
2. For bar charts: Use 2-4 data points max (mobile readability)
3. For number counters: Use for single dramatic stats
4. Highlight the "bad" option with red (#FF3B30), "good" with gold (#FFD700)
5. Keep labels SHORT (max 10 chars)

## Output JSON format for BAR CHART:
{
    "chartType": "bar",
    "data": [
        {"label": "Age 25", "value": 1140000, "color": "#FFD700"},
        {"label": "Age 35", "value": 540000, "color": "#FF3B30"}
    ],
    "narrative": "One sentence explaining what this chart proves"
}

## Output JSON format for NUMBER COUNTER:
{
    "chartType": "number",
    "value": 600000,
    "prefix": "$",
    "suffix": "",
    "title_text": "Cost of Waiting",
    "subtitle_text": "10 years of delay",
    "narrative": "Waiting cost her $600,000"
}

Return ONLY valid JSON.
```

### User Prompt Template

```
Generate a chart configuration for this data.

HOOK: {hook}

KEY DATA:
{key_data}

Pick the best chart type to visualize this comparison. Make it punchy and mobile-friendly.
```

---

## Format Decision Logic

Use this logic to determine which format to use:

```python
def determine_format(blog_content, extraction):
    # Does it have specific, comparable numbers?
    if extraction.key_stat and can_visualize_comparison(extraction.key_stat):
        return "math_slap"  # → Generate chart.json
    
    # Is it debunking a common belief?
    if "actually" in extraction.truth.lower() or "wrong" in extraction.hook.lower():
        return "myth_bust"
    
    # Is it a personal story with a lesson?
    if extraction.has_narrative_arc:
        return "story_lesson"
    
    # Is it listing signs/symptoms/steps?
    if any(word in extraction.hook.lower() for word in ["signs", "ways", "steps", "reasons"]):
        return "checklist"
    
    # Default: contrarian truth
    return "contrarian_truth"
```

---

## Example: Full Extraction Flow

### Input: Blog Content

```
Title: The Psychology of Waiting to Invest

Starting to invest at 35 instead of 25 costs you more than half your wealth...

A 25-year-old investing $300 monthly at 7% until 65 accumulates $1.14 million.
Start at 35 with identical effort? You get $540,000.
Same money in. Half the result out.

The cognitive trap: We tell ourselves we'll start "when things calm down."
But that calm never comes...
```

### Step 1 Output

```json
{
  "format_type": "math_slap",
  "hook": "Starting at 35 instead of 25 costs you HALF your wealth",
  "truth": "$300/month from 25 to 65 = $1.14M. Start at 35? $540K.",
  "mistake": "We wait for 'the right time' that never comes",
  "fix": "Start today with whatever you can, even $50",
  "core_insight": "10 years of delay costs more than half your wealth",
  "visual_vibe": "Dark, moody, gold on black, urgency",
  "key_stat": "Starting at 25: $1.14M vs Starting at 35: $540K"
}
```

### Step 2 Output

```json
{
  "accuracy_pass": true,
  "stat_verified": true,
  "stat_source_quote": "$1.14 million. Start at 35... $540,000",
  "format_pass": true,
  "overall_pass": true,
  "corrections_needed": []
}
```

### Step 3 Output (seed.md)

```markdown
# Hook
Starting to invest at 35 instead of 25 costs you more than HALF your wealth.

# Core Insight
A 25-year-old investing $300 monthly at 7% until 65 accumulates $1.14 million. Start at 35 with identical effort? $540,000. Same money in. Half the result out.

# Visual Vibe
Dark, moody, cinematic. Red and black for urgency. Gold highlights for wealth potential. Abstract shapes representing compound growth.

# Script Structure
**TRUTH:** A 25-year-old investing $300 monthly at 7% until 65 accumulates $1.14 million. Start at 35? You get $540,000.

**MISTAKE:** We tell ourselves we'll start "when things calm down." But that calm never comes. There's always a reason to wait.

**FIX:** Stop asking "when will conditions be right?" Start asking "what can I do TODAY?"

# Key Data
- Start at 25: ~$1.14 million
- Start at 35: ~$540,000
- Cost of waiting: $600,000+
- Monthly amount: $300
- Return assumed: 7%
```

### Step 4 Output (chart.json)

```json
{
  "chartType": "bar",
  "dimensions": { "width": 1080, "height": 1080 },
  "background": { "color": "#00FF00" },
  "data": [
    { "label": "Age 25", "value": 1140000, "color": "#FFD700" },
    { "label": "Age 35", "value": 540000, "color": "#FF3B30" }
  ],
  "animation": { "duration": 30, "style": "simultaneous", "velocityMode": true }
}
```

---

## Anti-Patterns to Avoid

### ❌ Vague Motivational Language

**Bad:** "Money can change your life"  
**Good:** "10 years of delay costs $600,000"

### ❌ No Specific Numbers

**Bad:** "Investing early pays off"  
**Good:** "$300/month from 25→65 = $1.14M"

### ❌ Preachy Tone

**Bad:** "You should really think about your future"  
**Good:** "Half. Gone before you even begin."

### ❌ Too Long

**Bad:** 200+ words in Core Insight  
**Good:** 50 words max, punchy sentences

### ❌ Unverified Statistics

**Bad:** Made-up numbers not in source  
**Good:** Only use stats that appear in the blog
