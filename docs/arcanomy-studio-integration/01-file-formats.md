# File Formats Specification

Complete specifications for the three input files consumed by Arcanomy Motion.

---

## 1. claim.json

**Location:** `content/reels/YYYY-MM-DD-{slug}/inputs/claim.json`  
**Purpose:** Machine-readable core claim and metadata

### Schema

```json
{
  "claim_id": "string (required)",
  "claim_text": "string (required)",
  "supporting_data_ref": "string (required)",
  "audit_level": "basic | strict (required)",
  "tags": ["string"] | null,
  "risk_notes": "string | null",
  "thumbnail_text": "string | null"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_id` | string | ✅ | Unique identifier for this reel (use the slug) |
| `claim_text` | string | ✅ | The sacred sentence - the core claim (max 25 words) |
| `supporting_data_ref` | string | ✅ | Data source reference (e.g., `blog:2025-01-15-money-psychology`) |
| `audit_level` | string | ✅ | `"basic"` for most content, `"strict"` for financial claims requiring verification |
| `tags` | array | ❌ | List of topic tags for categorization |
| `risk_notes` | string | ❌ | Any compliance/legal notes |
| `thumbnail_text` | string | ❌ | Text to display on the thumbnail |

### Example

```json
{
  "claim_id": "permission-trap-waiting-game",
  "claim_text": "Starting to invest at 35 instead of 25 costs you more than HALF your wealth.",
  "supporting_data_ref": "blog:2025-12-15-psychology-of-money",
  "audit_level": "basic",
  "tags": ["investing", "psychology", "compound-interest"],
  "thumbnail_text": "The $600K Mistake"
}
```

---

## 2. seed.md

**Location:** `content/reels/YYYY-MM-DD-{slug}/inputs/seed.md`  
**Purpose:** Human-readable creative brief

**Note:** A reel is typically **5–6 subsegments** = **50–60 seconds** (10-second blocks). Seed content should support that pacing.

### Required Sections

The file MUST contain these exact markdown headers:

```markdown
# Hook
# Core Insight
# Visual Vibe
# Script Structure
# Key Data
```

### Section Specifications

#### `# Hook`
- **Purpose:** The scroll-stopping opening line
- **Constraint:** Maximum 15 words
- **Tone:** Confrontational, provocative, specific
- **Bad:** "Money is important for life" ❌
- **Good:** "Starting at 35 instead of 25 costs you HALF your wealth." ✅

#### `# Core Insight`
- **Purpose:** The single main lesson or takeaway
- **Constraint:** Maximum 50 words
- **Must include:** Specific numbers if available
- **Bad:** "Waiting costs money" ❌
- **Good:** "A 25-year-old investing $300/month at 7% until 65 accumulates $1.14 million. Start at 35? You get $540,000. Same effort, half the result." ✅

#### `# Visual Vibe`
- **Purpose:** Mood and aesthetic direction for image/video generation
- **Format:** Descriptive phrases about colors, mood, style
- **Examples:**
  - "Dark, moody, cinematic. Gold accents on black."
  - "Clean, minimal, premium. White space with bold typography."
  - "Warm, human, documentary feel. Natural lighting."

#### `# Script Structure`
- **Purpose:** The TRUTH → MISTAKE → FIX structure
- **Format:** Three labeled subsections

```markdown
# Script Structure
**TRUTH:** A 25-year-old investing $300 monthly at 7% until 65 accumulates $1.14 million. Start at 35? You get $540,000.

**MISTAKE:** We tell ourselves we'll start "when things calm down." But that calm never comes.

**FIX:** Stop asking "when will conditions be right?" Start asking "what can I do TODAY?"
```

#### `# Key Data`
- **Purpose:** Specific statistics and data points to reference
- **Format:** Bulleted list with label: value pairs

```markdown
# Key Data
- Start at 25: ~$1.14 million
- Start at 35: ~$540,000
- Cost of waiting 10 years: More than half your potential wealth
- Monthly investment: $300
- Assumed return: 7% annually
```

### Complete Example

```markdown
# Hook
Starting to invest at 35 instead of 25 costs you more than HALF your wealth.

# Core Insight
A 25-year-old investing $300 monthly at 7% until 65 accumulates $1.14 million. Start at 35 with identical effort and discipline? $540,000. Same money in. Half the result out.

# Visual Vibe
Dark, moody, cinematic. Red and black color palette for danger/urgency. Gold highlights for wealth. Abstract geometric shapes representing compound growth.

# Script Structure
**TRUTH:** A 25-year-old investing $300 monthly at 7% until 65 accumulates $1.14 million. Start at 35? You get $540,000.

**MISTAKE:** We tell ourselves we'll start "when things calm down." But that calm never comes. There's always a reason to wait—student loans, the wedding, the house, the kids.

**FIX:** Stop asking "when will conditions be right?" Start asking "what can I do TODAY?" Even $50/month started now beats $500/month started later.

# Key Data
- Start at 25: ~$1.14 million
- Start at 35: ~$540,000
- Cost of waiting 10 years: $600,000+
- Monthly investment assumed: $300
- Annual return assumed: 7%
```

---

## 3. chart.json (Optional)

**Location:** `content/reels/YYYY-MM-DD-{slug}/inputs/chart.json`  
**Purpose:** Configuration for animated chart rendering via Remotion

See [`02-chart-schema.md`](./02-chart-schema.md) for complete schema documentation.

### When to Include

Include `chart.json` when:
- The content has specific, comparable numbers
- A visual comparison would strengthen the argument
- The format is `math_slap` (data-driven insight)

Skip `chart.json` when:
- The content is purely narrative/story-based
- There are no specific statistics to visualize
- The format is `story_lesson` or `contrarian_truth`

### Quick Reference

```json
{
  "chartType": "bar",
  "dimensions": { "width": 1080, "height": 1080 },
  "background": { "color": "#00FF00" },
  "data": [
    { "label": "Age 25", "value": 1140000, "color": "#FFD700" },
    { "label": "Age 35", "value": 540000, "color": "#FF3B30" }
  ],
  "animation": {
    "duration": 30,
    "style": "simultaneous",
    "velocityMode": true
  }
}
```

---

## File Naming Convention

Use this naming pattern for reel folders:

```
YYYY-MM-DD-{slug}
```

- `YYYY-MM-DD` - The creation date (for sorting)
- `{slug}` - URL-safe lowercase identifier with hyphens

**Examples:**
- `2025-12-26-permission-trap-waiting-game`
- `2025-12-26-compound-interest-math-slap`
- `2025-12-26-sunk-cost-fallacy-explained`

---

## Validation

All files must pass these checks before handoff:

### claim.json
- [ ] Valid JSON syntax
- [ ] All 4 required fields present
- [ ] `claim_text` is under 25 words
- [ ] `audit_level` is either `"basic"` or `"strict"`

### seed.md
- [ ] Has all 5 required headers
- [ ] Hook is under 15 words
- [ ] Core Insight is under 50 words
- [ ] Script Structure has TRUTH, MISTAKE, FIX
- [ ] Key Data has at least 2 data points if format is `math_slap`

### chart.json (if present)
- [ ] Valid JSON syntax
- [ ] `chartType` is a valid type
- [ ] `data` array has 2-6 items
- [ ] All labels are under 10 characters
