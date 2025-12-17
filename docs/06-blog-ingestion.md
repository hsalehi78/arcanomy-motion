# 06 — Blog Ingestion

## Overview

Arcanomy Motion can automatically create reel projects from published Arcanomy blog posts. This workflow fetches blog content from the CDN, uses an LLM to extract the key elements (hook, core insight, visual vibe), and generates the required `00_seed.md` and `00_reel.yaml` files.

---

## Data Sources

Blog data is fetched from the public Arcanomy CDN:

| Resource | URL |
|----------|-----|
| Featured Index | `https://cdn.arcanomydata.com/content/posts/_indexes/featured.json` |
| Raw MDX | `https://cdn.arcanomydata.com/content/posts/{identifier}/content.mdx` |
| Hero Image | `https://cdn.arcanomydata.com/content/posts/{identifier}/assets/hero.webp` |

No authentication is required — all resources are publicly accessible.

---

## Commands

### `arcanomy list-blogs`

Lists available blog posts from the Arcanomy CDN.

```bash
# Show last 10 blogs (default)
uv run arcanomy list-blogs

# Show last 20 blogs
uv run arcanomy list-blogs --limit 20
```

**Output:**

```
┏━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Published  ┃ Title                      ┃ Category         ┃ Identifier                                 ┃
┡━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ 2025-08-10 │ The Psychology of Money    │ Wealth Psychology│ 2025-08-10-knowledge-the-psychology-of-money │
│ 2 │ ...        │ ...                        │ ...              │ ...                                        │
└───┴────────────┴────────────────────────────┴──────────────────┴────────────────────────────────────────────┘
```

### `arcanomy ingest-blog`

Creates a new reel from a blog post. Run without arguments for **interactive mode**.

```bash
# Interactive mode: pick by number
uv run arcanomy ingest-blog

# Direct mode: provide identifier
uv run arcanomy ingest-blog 2025-08-10-knowledge-the-psychology-of-money
```

**Interactive mode output:**

```
Pick a blog (1-10)
┏━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Published  ┃ Title                      ┃ Category         ┃
┡━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ 1 │ 2025-08-10 │ The Psychology of Money    │ Wealth Psychology│
│ 2 │ ...        │ ...                        │ ...              │
└───┴────────────┴────────────────────────────┴──────────────────┘

Enter number to select: 1

Selected: The Psychology of Money
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--output`, `-o` | `content/reels` | Output directory for the reel |
| `--provider`, `-p` | `openai` | LLM provider (openai, anthropic, gemini) |
| `--limit`, `-n` | `10` | Number of blogs to show in interactive mode |

**What it does:**

1. Fetches blog metadata from `featured.json`
2. Downloads the raw MDX content
3. Sends the content to an LLM to extract:
   - Hook (attention-grabbing opening line)
   - Core insight (main lesson/takeaway)
   - Visual vibe (mood, colors, style)
   - Reel type and duration
4. Creates `content/reels/{identifier}/` with:
   - `00_seed.md` — Creative brief
   - `00_reel.yaml` — Machine config
   - `00_data/` — Empty data folder

---

## Generated Files

### `00_seed.md`

```markdown
# Hook
Stop making these money mistakes.

# Core Insight
Smart people make bad financial decisions because they confuse
knowledge with wisdom. Understanding compound interest is useless
if you can't control your spending impulses.

# Visual Vibe
Dark, moody, cinematic. Gold accents on black. Premium, minimalist typography.

# Data Sources
- (none - sourced from blog: 2025-08-10-knowledge-the-psychology-of-money)
```

### `00_reel.yaml`

```yaml
title: The Psychology of Money
type: story_essay
duration_blocks: 2
voice_id: eleven_labs_adam
music_mood: contemplative
aspect_ratio: "9:16"
subtitles: burned_in
audit_level: loose
source_blog: 2025-08-10-knowledge-the-psychology-of-money
```

**Note:** `audit_level` is set to `loose` because blogs don't have CSV data sources. The `source_blog` field tracks provenance.

---

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        BLOG INGESTION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. arcanomy list-blogs                                         │
│     └─▶ Fetch featured.json from CDN                            │
│     └─▶ Display available blogs                                 │
│                                                                  │
│  2. arcanomy ingest-blog <identifier>                           │
│     └─▶ Fetch content.mdx from CDN                              │
│     └─▶ LLM extracts hook, insight, vibe                        │
│     └─▶ Create content/reels/{identifier}/                      │
│         ├── 00_seed.md                                          │
│         ├── 00_reel.yaml                                        │
│         └── 00_data/                                            │
│                                                                  │
│  3. Review & edit generated files                                │
│                                                                  │
│  4. arcanomy run content/reels/{identifier}/                    │
│     └─▶ Normal pipeline (research, script, visuals, etc.)      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

The blog ingestion commands require an LLM API key for content extraction:

```bash
# Required (one of these)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

No CDN authentication is required — blog content is publicly accessible.

---

## Tips

1. **Review before running:** Always review the generated `00_seed.md` and `00_reel.yaml` before running the full pipeline. The LLM's interpretation may need tweaking.

2. **Adjust duration:** If the blog is complex, consider increasing `duration_blocks` from 2 to 3.

3. **Add data:** If you want to include charts/data, add CSV files to `00_data/` and update `# Data Sources` in the seed file.

4. **Change reel type:** The LLM infers the reel type, but you can override it:
   - `chart_explainer` — For data-driven content
   - `text_cinematic` — For powerful statements
   - `story_essay` — For narrative insights

