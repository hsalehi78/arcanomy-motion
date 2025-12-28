# Suggested Repo Layout (new repo)

This is a clean layout for a rebuild. Keep it boring and explicit.

```
arcanomy-reels/
  apps/
    reels_cli/                 # The daily runner CLI (Python or Node)
    remotion_charts/           # Remotion project (charts-only)
    web_admin/                 # Optional: internal UI (later)

  packages/
    domain/                    # Shared types + schemas (JSON Schema / Pydantic)
    asset_index/               # B-roll/music index loaders + query/scoring

  content/
    blogs/                     # Immutable blog source store (versioned)
    libraries/
      broll/                   # Local b-roll clips + index.json
      music/                   # Local music tracks + index.json

  runs/                        # Daily run outputs (one folder per reel run)

  infra/
    supabase/                  # SQL migrations, policies, seed data
    r2/                        # bucket notes, CLI scripts, index file specs

  docs/                        # Copy `docs_v2/` here as the canonical docs folder

  .env.example
  README.md
```

## Key rule

`runs/` contains **generated artifacts**. Everything else is either:
- immutable inputs, or
- reusable libraries, or
- code.

