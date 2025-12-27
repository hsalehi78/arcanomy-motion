# Validation Checklist

Pre-flight checks before handing off to Arcanomy Motion.

---

## Quick Validation

Run these checks before every handoff:

### ✅ claim.json

| Check | Requirement |
|-------|-------------|
| [ ] Valid JSON | Parses without error |
| [ ] `claim_id` | Present, string |
| [ ] `claim_text` | Present, under 25 words |
| [ ] `supporting_data_ref` | Present (e.g., `blog:identifier`) |
| [ ] `audit_level` | `"basic"` or `"strict"` |

### ✅ seed.md

| Check | Requirement |
|-------|-------------|
| [ ] `# Hook` section | Present, under 15 words |
| [ ] `# Core Insight` section | Present, under 50 words |
| [ ] `# Visual Vibe` section | Present |
| [ ] `# Script Structure` section | Has TRUTH, MISTAKE, FIX |
| [ ] `# Key Data` section | Present with 2+ data points |
| [ ] No vague language | No "should", "might", "could" |
| [ ] Specific numbers | Uses actual stats from source |
| [ ] No em-dashes | Uses commas or periods instead |

### ✅ chart.json (if present)

| Check | Requirement |
|-------|-------------|
| [ ] Valid JSON | Parses without error |
| [ ] `chartType` | One of: bar, number, pie, line, horizontalBar, stackedBar, scatter, progress |
| [ ] `data` array | 2-6 items |
| [ ] Labels | Each under 10 characters |
| [ ] Values | Numeric, reasonable magnitude |
| [ ] Colors | Use brand palette |
| [ ] Background | `#00FF00` for green screen |
| [ ] Animation | `duration` is 30 (1 second base) |

---

## Detailed Validation

### claim.json Schema Validation

```json
{
  "claim_id": "string (required)",
  "claim_text": "string (required, max 25 words)",
  "supporting_data_ref": "string (required)",
  "audit_level": "basic | strict (required)",
  "tags": ["array of strings (optional)"],
  "thumbnail_text": "string (optional)"
}
```

**Validation Code (pseudo):**
```python
def validate_claim(claim):
    errors = []
    
    if "claim_id" not in claim:
        errors.append("Missing required field: claim_id")
    
    if "claim_text" not in claim:
        errors.append("Missing required field: claim_text")
    elif len(claim["claim_text"].split()) > 25:
        errors.append("claim_text exceeds 25 words")
    
    if "supporting_data_ref" not in claim:
        errors.append("Missing required field: supporting_data_ref")
    
    if claim.get("audit_level") not in ("basic", "strict"):
        errors.append("audit_level must be 'basic' or 'strict'")
    
    return errors
```

---

### seed.md Structure Validation

**Required sections:**
1. `# Hook`
2. `# Core Insight`
3. `# Visual Vibe`
4. `# Script Structure`
5. `# Key Data`

**Validation Code (pseudo):**
```python
def validate_seed(seed_content):
    errors = []
    
    required_sections = [
        "# Hook",
        "# Core Insight",
        "# Visual Vibe",
        "# Script Structure",
        "# Key Data"
    ]
    
    for section in required_sections:
        if section not in seed_content:
            errors.append(f"Missing required section: {section}")
    
    # Extract and validate Hook
    hook_match = re.search(r"# Hook\n(.+?)(?=\n#|\Z)", seed_content, re.DOTALL)
    if hook_match:
        hook = hook_match.group(1).strip()
        if len(hook.split()) > 15:
            errors.append("Hook exceeds 15 words")
    
    # Extract and validate Core Insight
    insight_match = re.search(r"# Core Insight\n(.+?)(?=\n#|\Z)", seed_content, re.DOTALL)
    if insight_match:
        insight = insight_match.group(1).strip()
        if len(insight.split()) > 50:
            errors.append("Core Insight exceeds 50 words")
    
    # Check for TRUTH, MISTAKE, FIX in Script Structure
    script_match = re.search(r"# Script Structure\n(.+?)(?=\n#|\Z)", seed_content, re.DOTALL)
    if script_match:
        script = script_match.group(1)
        if "TRUTH" not in script.upper():
            errors.append("Script Structure missing TRUTH")
        if "MISTAKE" not in script.upper():
            errors.append("Script Structure missing MISTAKE")
        if "FIX" not in script.upper():
            errors.append("Script Structure missing FIX")
    
    # Check for vague language
    vague_words = ["should", "might", "could", "maybe", "possibly"]
    for word in vague_words:
        if word in seed_content.lower():
            errors.append(f"Contains vague language: '{word}'")
    
    return errors
```

---

### chart.json Validation

**Valid chart types:**
- `bar`
- `horizontalBar`
- `stackedBar`
- `pie`
- `line`
- `scatter`
- `progress`
- `number`

**Validation Code (pseudo):**
```python
def validate_chart(chart):
    errors = []
    
    valid_types = ["bar", "horizontalBar", "stackedBar", "pie", "line", "scatter", "progress", "number"]
    
    chart_type = chart.get("chartType")
    if chart_type not in valid_types:
        errors.append(f"Invalid chartType: {chart_type}. Must be one of: {valid_types}")
    
    # Validate data array
    data = chart.get("data", [])
    if chart_type != "number":  # Number counter doesn't have data array
        if len(data) < 2:
            errors.append("data array must have at least 2 items")
        if len(data) > 6:
            errors.append("data array should have at most 6 items for readability")
        
        for i, item in enumerate(data):
            label = item.get("label", "")
            if len(label) > 10:
                errors.append(f"data[{i}].label '{label}' exceeds 10 characters")
    
    # Validate background for green screen
    bg_color = chart.get("background", {}).get("color", "")
    if bg_color != "#00FF00":
        errors.append(f"background.color should be '#00FF00' for green screen, got '{bg_color}'")
    
    # Validate animation duration
    anim_duration = chart.get("animation", {}).get("duration", 30)
    if anim_duration < 15 or anim_duration > 60:
        errors.append(f"animation.duration {anim_duration} is unusual (expected 15-60)")
    
    return errors
```

---

## Content Quality Checks

### Hook Quality

| ✅ Good Hook | ❌ Bad Hook |
|--------------|-------------|
| Specific number or fact | Vague statement |
| Creates tension/curiosity | Generic advice |
| Under 15 words | Long-winded |
| Confrontational tone | Preachy tone |

**Examples:**

✅ "Starting at 35 instead of 25 costs you HALF your wealth."  
❌ "Investing early is important for your financial future."

✅ "Your brain lies to you about money. Here's the proof."  
❌ "Understanding psychology can help you make better decisions."

### Core Insight Quality

| ✅ Good Insight | ❌ Bad Insight |
|-----------------|----------------|
| Specific data | Generalities |
| Cause and effect | Just stating facts |
| Surprising contrast | Obvious conclusions |

**Examples:**

✅ "$300/month from 25-65 = $1.14M. From 35-65? $540K. Same money. Half the result."  
❌ "Starting early with investing helps you save more money over time."

### Visual Vibe Quality

| ✅ Good Vibe | ❌ Bad Vibe |
|--------------|-------------|
| Specific colors mentioned | "Nice looking" |
| Mood words | Just color names |
| Reference style | Generic |

**Examples:**

✅ "Dark, moody, cinematic. Red and black for urgency. Gold highlights for wealth. Abstract geometric shapes."  
❌ "Make it look good. Use nice colors."

---

## Final Checklist Format

Copy this for every handoff:

```markdown
## Pre-Handoff Validation Report

### claim.json
- [ ] Valid JSON syntax
- [ ] claim_id present
- [ ] claim_text under 25 words
- [ ] supporting_data_ref present
- [ ] audit_level is "basic" or "strict"

### seed.md
- [ ] # Hook section present and under 15 words
- [ ] # Core Insight present and under 50 words
- [ ] # Visual Vibe present with mood/color description
- [ ] # Script Structure has TRUTH, MISTAKE, FIX
- [ ] # Key Data has 2+ data points
- [ ] No vague language (should, might, could)
- [ ] Uses specific numbers from source
- [ ] No em-dashes (—)

### chart.json (if present)
- [ ] Valid JSON syntax
- [ ] chartType is valid (bar/number/pie/line/horizontalBar/stackedBar/scatter/progress)
- [ ] data array has 2-6 items
- [ ] All labels under 10 characters
- [ ] background.color is "#00FF00"
- [ ] animation.duration is 30

### Content Quality
- [ ] Hook stops the scroll in 3 seconds
- [ ] Follows TRUTH → MISTAKE → FIX structure
- [ ] Tone is confident, not preachy
- [ ] Statistics are verified from source

### Ready for Handoff
- [ ] All files created in correct folder structure
- [ ] All validation checks pass
```

---

## Common Errors and Fixes

| Error | Fix |
|-------|-----|
| Hook too long | Cut to 15 words max, focus on the shocking fact |
| Missing TRUTH/MISTAKE/FIX | Restructure Script Structure section with bold labels |
| Vague language | Replace "should" with specific actions, "might" with data |
| Chart labels too long | Abbreviate (e.g., "United States" → "US") |
| Wrong background color | Set to `#00FF00` for green screen |
| No specific numbers | Pull exact stats from source blog |
