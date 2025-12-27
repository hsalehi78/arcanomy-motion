# R2 Storage Integration

How Arcanomy Studio should store generated files on R2 for Arcanomy Motion to consume.

---

## Overview

Generated seed files should be stored on **Cloudflare R2** (CDN: `cdn.arcanomydata.com`) so that Arcanomy Motion can fetch and process them.

### Architecture

```
Arcanomy Studio                        R2 Storage                         Arcanomy Motion
────────────────                       ──────────                         ────────────────────
                                              
1. Generate files      ───────▶  2. Upload to R2  ───────▶  3. Fetch & Run Pipeline
   - claim.json                   /content/reels/{id}/        
   - seed.md                        ├── claim.json             uv run arcanomy fetch {id}
   - chart.json                     ├── seed.md                uv run arcanomy run
                                    └── chart.json               
```

---

## R2 Folder Structure

### Base URL

```
https://cdn.arcanomydata.com/content/reels/
```

### Per-Reel Structure

For each reel, create this folder structure on R2:

```
content/reels/{reel-identifier}/
├── claim.json          # Required
├── seed.md             # Required
├── chart.json          # Optional (for data-driven reels)
└── assets/             # Optional (for custom images)
    └── hero.webp       # Hero image if needed
```

### Reel Identifier Format

Use this naming convention:

```
YYYY-MM-DD-{section}-{slug}
```

**Examples:**
- `2025-12-26-knowledge-permission-trap-waiting-game`
- `2025-12-26-perspectives-compound-interest-math-slap`
- `2025-12-26-insights-sunk-cost-fallacy-explained`

---

## Full R2 URLs

For a reel with identifier `2025-12-26-knowledge-permission-trap`:

| File | R2 URL |
|------|--------|
| claim.json | `https://cdn.arcanomydata.com/content/reels/2025-12-26-knowledge-permission-trap/claim.json` |
| seed.md | `https://cdn.arcanomydata.com/content/reels/2025-12-26-knowledge-permission-trap/seed.md` |
| chart.json | `https://cdn.arcanomydata.com/content/reels/2025-12-26-knowledge-permission-trap/chart.json` |

---

## Index File

### Reels Index

Maintain an index at:

```
https://cdn.arcanomydata.com/content/reels/_indexes/ready.json
```

**Schema:**

```json
{
  "reels": [
    {
      "identifier": "2025-12-26-knowledge-permission-trap",
      "title": "The Permission Trap",
      "created_at": "2025-12-26T10:00:00Z",
      "format_type": "math_slap",
      "has_chart": true,
      "source_blog": "2025-12-26-psychology-of-money",
      "status": "ready"
    }
  ],
  "updated_at": "2025-12-26T10:00:00Z"
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `identifier` | string | Unique reel identifier (folder name on R2) |
| `title` | string | Display title from claim |
| `created_at` | ISO date | When files were uploaded |
| `format_type` | string | One of: contrarian_truth, math_slap, checklist, story_lesson, myth_bust |
| `has_chart` | boolean | Whether chart.json exists |
| `source_blog` | string | Source blog identifier (if derived from blog) |
| `status` | string | `ready` or `processing` |

---

## Upload Workflow

### Step 1: Generate Files Locally

```
temp/
├── claim.json
├── seed.md
└── chart.json (if math_slap)
```

### Step 2: Validate Files

Before upload, run validation (see `06-validation-checklist.md`):

- [ ] claim.json is valid
- [ ] seed.md has all required sections
- [ ] chart.json (if present) has valid schema

### Step 3: Upload to R2

Upload all files to the reel folder:

```bash
# Using rclone (example)
rclone copy temp/ arcanomy-r2:arcanomy-cdn/content/reels/2025-12-26-knowledge-permission-trap/

# Or using wrangler (Cloudflare)
wrangler r2 object put arcanomy-cdn/content/reels/2025-12-26-knowledge-permission-trap/claim.json --file=temp/claim.json
wrangler r2 object put arcanomy-cdn/content/reels/2025-12-26-knowledge-permission-trap/seed.md --file=temp/seed.md
```

### Step 4: Update Index

Update `_indexes/ready.json` to include the new reel.

---

## How Arcanomy Motion Fetches

Once files are on R2, Arcanomy Motion can:

### Option 1: Fetch and Run

```bash
# Fetch reel from R2 to local content/reels/
uv run arcanomy fetch 2025-12-26-knowledge-permission-trap

# Run the pipeline
uv run arcanomy run
```

### Option 2: List Available Reels

```bash
# List reels ready for processing from R2
uv run arcanomy list-reels --source r2

# Interactive picker
uv run arcanomy ingest-reel
```

---

## File Content Requirements

### claim.json on R2

Must contain (see `01-file-formats.md`):

```json
{
  "claim_id": "permission-trap-waiting-game",
  "claim_text": "Starting to invest at 35 instead of 25 costs you more than HALF your wealth.",
  "supporting_data_ref": "blog:2025-12-26-psychology-of-money",
  "audit_level": "basic",
  "tags": ["investing", "psychology"],
  "thumbnail_text": "The $600K Mistake"
}
```

### seed.md on R2

Must contain all 5 sections (see `01-file-formats.md`):

```markdown
# Hook
Starting to invest at 35 instead of 25 costs you more than HALF your wealth.

# Core Insight
[50 words max]

# Visual Vibe
[Mood, colors, style]

# Script Structure
**TRUTH:** [...]
**MISTAKE:** [...]
**FIX:** [...]

# Key Data
- Stat 1: value
- Stat 2: value
```

### chart.json on R2

If present, must follow schema in `02-chart-schema.md`:

```json
{
  "chartType": "bar",
  "background": { "color": "#00FF00" },
  "data": [...],
  "animation": {...}
}
```

---

## Comparison: Blog Posts vs Reels

| Aspect | Blog Posts (existing) | Reel Seeds (new) |
|--------|----------------------|------------------|
| Base path | `/content/posts/` | `/content/reels/` |
| Index file | `_indexes/featured.json` | `_indexes/ready.json` |
| Main content | `content.mdx` | `seed.md` |
| Metadata | In MDX frontmatter | `claim.json` |
| Data viz | N/A | `chart.json` |
| Created by | Arcanomy Studio (blog) | Arcanomy Studio (video) |
| Consumed by | arcanomy.com website | arcanomy-motion pipeline |

---

## Environment Setup for R2 Access

Arcanomy Studio needs these credentials [TODO: update with your actual bucket details]:

```bash
# Cloudflare R2 credentials
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=arcanomy-cdn

# Public CDN URL (read-only, no auth needed)
CDN_BASE_URL=https://cdn.arcanomydata.com
```

---

## Summary

1. **Arcanomy Studio generates** `claim.json`, `seed.md`, `chart.json`
2. **Uploads to R2** at `/content/reels/{identifier}/`
3. **Updates index** at `/content/reels/_indexes/ready.json`
4. **Arcanomy Motion fetches** from R2 and runs pipeline
5. **Output** goes to local `content/reels/{identifier}/` with generated assets

This creates a clean handoff where Arcanomy Studio produces the creative inputs and Arcanomy Motion produces the video assets.
