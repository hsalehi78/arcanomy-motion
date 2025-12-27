# Arcanomy Studio → Arcanomy Motion Integration Guide

**Version:** 1.0  
**Purpose:** Enable Arcanomy Studio to generate production-ready seed files for Arcanomy Motion  
**Audience:** AI Agents (Arcanomy Studio)

---

## Overview

Arcanomy Motion is a video production pipeline that generates **CapCut-ready assembly kits** for short-form video (Instagram Reels, TikTok, YouTube Shorts). It uses three input files:

1. **`claim.json`** - The machine-readable core claim
2. **`seed.md`** - The creative brief (human-readable)
3. **`chart.json`** - Chart configuration for data visualization (optional)

Your job as Arcanomy Studio is to generate these files from blog content or other sources **and upload them to R2**.

Arcanomy Motion’s job is to take those seeds and produce a **CapCut-ready kit** + **10-second assets**.

### What Motion Outputs (Locally)

After running the pipeline, Motion writes:
- `subsegments/subseg-XX.mp4` (10.0s each; background/base visuals)
- `charts/chart-subseg-XX-*.mp4` (10.0s each; green-screen overlays for CapCut chroma key)
- `voice/subseg-XX.wav` (10.0s each)
- `captions/captions.srt` (line-level; voice-aligned; never crosses 10-second boundaries)
- `guides/capcut_assembly_guide.md` and `guides/retention_checklist.md`
- `thumbnail/thumbnail.png`
- `meta/quality_gate.json` (pass/fail + reasons; enforces doctrine constraints)

### Pro Mode + Overrides (While Learning)

Motion can optionally generate “pro” visual assets (seed images + 10-second AI clips). When you’re learning, you can also **override** visuals:
- If `renders/videos/clip_XX.mp4` already exists locally, Motion should **use it** and skip regenerating that clip.
- Same concept for seed images under `renders/images/composites/`.

---

## ⚠️ IMPORTANT: R2 Storage

**All generated files must be uploaded to R2** for Arcanomy Motion to consume them.

### R2 Location
```
https://cdn.arcanomydata.com/content/reels/{reel-identifier}/
├── claim.json      ← Upload here
├── seed.md         ← Upload here
└── chart.json      ← Upload here (if data-driven)
```

### Reel Identifier Format
```
YYYY-MM-DD-{section}-{slug}
```
Example: `2025-12-26-knowledge-permission-trap`

See **[`07-r2-storage.md`](./07-r2-storage.md)** for complete R2 upload workflow.

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| [`01-file-formats.md`](./01-file-formats.md) | Complete specifications for seed.md, claim.json, chart.json |
| [`02-chart-schema.md`](./02-chart-schema.md) | Full chart.json schema with all chart types |
| [`03-chart-examples.md`](./03-chart-examples.md) | Copy-paste chart templates for each chart type |
| [`04-remotion-setup.md`](./04-remotion-setup.md) | How to install and configure Remotion |
| [`05-extraction-prompts.md`](./05-extraction-prompts.md) | LLM prompts for extracting content from blogs |
| [`06-validation-checklist.md`](./06-validation-checklist.md) | Pre-flight checklist for generated files |
| [`07-r2-storage.md`](./07-r2-storage.md) | **R2 upload workflow and folder structure** |

---

## Quick Reference

### R2 Folder Structure You Will Create

```
https://cdn.arcanomydata.com/content/reels/{reel-identifier}/
├── claim.json      ← You generate and upload this
├── seed.md         ← You generate and upload this
└── chart.json      ← You generate and upload this (if data-driven)
```

**Reel Identifier:** `YYYY-MM-DD-{section}-{slug}`  
**Example:** `2025-12-26-knowledge-permission-trap`

### Reel Length (10-second blocks)

A reel is typically **5–6 subsegments** = **50–60 seconds**.

### Minimal Valid Output

**claim.json:**
```json
{
  "claim_id": "my-reel-slug",
  "claim_text": "The single sentence claim that stops the scroll",
  "supporting_data_ref": "blog:source-identifier",
  "audit_level": "basic",
  "tags": ["money", "psychology"],
  "thumbnail_text": "Text for thumbnail"
}
```

**seed.md:**
```markdown
# Hook
The attention-grabbing opening line (max 15 words)

# Core Insight
The main lesson or data point being conveyed (max 50 words)

# Visual Vibe
Dark, moody, cinematic. Gold accents on black.

# Script Structure
**TRUTH:** The counter-intuitive truth
**MISTAKE:** The common mistake people make
**FIX:** The simple reframe or solution

# Key Data
- Stat 1: $600,000
- Stat 2: 10 years
```

---

## The Arcanomy Content Formula

Every reel follows **TRUTH → MISTAKE → FIX**:

1. **TRUTH** - A counter-intuitive or confrontational truth
2. **MISTAKE** - The common mistake people make
3. **FIX** - The simple reframe or solution

### Allowed Formats

| Format | Description | When to Use |
|--------|-------------|-------------|
| `contrarian_truth` | Challenge conventional wisdom | Provocative takes |
| `math_slap` | A shocking number that changes everything | Data-driven insights |
| `checklist` | "3 signs you're doing X wrong" | Listicles |
| `story_lesson` | Personal anecdote with universal truth | Human stories |
| `myth_bust` | Expose a popular misconception | Debunking |

### Chart Decision Tree

```
Does the content have specific numbers/statistics?
├── YES → Does comparing 2-4 values tell the story?
│         ├── YES → Generate bar chart (chart.json)
│         └── NO → Is it a single dramatic number?
│                  ├── YES → Generate number counter
│                  └── NO → Skip chart
└── NO → Skip chart (this is a text-only reel)
```

---

## Validation Before Handoff

Before sending files to Arcanomy Motion, verify:

- [ ] `claim.json` has all required fields
- [ ] `seed.md` has all 5 sections
- [ ] Hook is under 15 words
- [ ] Core Insight is under 50 words
- [ ] Script follows TRUTH → MISTAKE → FIX
- [ ] If chart: `chartType` is one of: bar, number, pie, line, horizontalBar, stackedBar, scatter, progress
- [ ] If chart: `data` array has 2-6 items max
- [ ] If chart: labels are short (max 10 characters)

---

## Next Steps

1. Read [`07-r2-storage.md`](./07-r2-storage.md) for **R2 upload workflow** (start here!)
2. Read [`01-file-formats.md`](./01-file-formats.md) for complete file specifications
3. Read [`02-chart-schema.md`](./02-chart-schema.md) for chart configuration details
4. Use [`03-chart-examples.md`](./03-chart-examples.md) as copy-paste templates
5. Follow [`06-validation-checklist.md`](./06-validation-checklist.md) before uploading
