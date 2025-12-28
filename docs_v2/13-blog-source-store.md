# Immutable Blog Source Store (v2)

Your daily workflow depends on proof anchors that don’t move.

## Existing blog CDN folder (current reality)

Your current blog objects live at:

- `content/posts/{blog-identifier}/`
  - `content.mdx`
  - `manifest.json`
  - `compiled.js`
  - `assets/` (e.g., hero image)

The v2 system can keep using `content.mdx` as the upstream source.

## Required files per blog

- `blog.md` — the human-readable cleaned source
- `blog.json` — structured representation including stable paragraph IDs

## Stable paragraph IDs

Paragraph IDs must be stable across time. Format:

- `p_001`, `p_002`, …

Rules:
- IDs are assigned once and never re-assigned.
- If you update the blog content, create a new version folder (or version field).

## `blog.json` (MVP)

```json
{
  "schema_version": "1.0",
  "blog_identifier": "2025-08-10-knowledge-the-psychology-of-money",
  "slug": "the-psychology-of-money",
  "title": "The Psychology of Money",
  "published_date": "2025-08-10",
  "sections": [
    {
      "heading": "…",
      "paragraphs": [
        { "id": "p_001", "text": "…", "source_offset": { "start": 0, "end": 120 } }
      ]
    }
  ],
  "tables": [],
  "figures": []
}
```

## How this integrates with existing CDN blog MDX

If your source of truth is still:
- `content/posts/{identifier}/content.mdx`

Then your blog ingestion step should:
- fetch MDX
- normalize it into `blog.md`
- segment into stable paragraphs → `blog.json`
- store it immutably (R2 or DB)

