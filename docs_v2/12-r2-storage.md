# R2 / CDN Storage (v2)

This doc captures existing conventions and extends them for v2.

## Current known conventions (from existing system)

- **Keep CDN base URL**: `https://cdn.arcanomydata.com` (confirmed)

- **R2 bucket + prefix (from your console screenshots)**:
  - Bucket: `arcanomy`
  - Prefix: `content/`

- **Reel seeds** live under:
  - `https://cdn.arcanomydata.com/content/reels/{reel-identifier}/`
  - Files: `claim.json`, `seed.md`, `chart.json?`
  - Index: `https://cdn.arcanomydata.com/content/reels/_indexes/ready.json`

- **Blogs** live under:
  - `https://cdn.arcanomydata.com/content/posts/{identifier}/content.mdx`
  - Index: `https://cdn.arcanomydata.com/content/posts/_indexes/featured.json`

## v2 recommendation: add v2-ready immutable blog store

Store the immutable parsed blog bundle at:

`TODO(V2): decide final location (recommended: same bucket/prefix under /content/blogs/)`

Option A (recommended): keep it on R2:

```
content/blogs/{blog-identifier}/
  blog.md
  blog.json
  meta.json
```

Option B: store in Supabase storage (works, but harder to CDN-cache).

## v2 recommendation: keep seeds + runs separate

- **Seeds** should remain small, human-readable, and CDN-friendly.
- **Runs** are local build artifacts; do not upload everything by default.

If you must upload run outputs, publish only the final kit:

```
content/kits/{run-id}/
  capcut_kit.zip
  manifest.json
```

