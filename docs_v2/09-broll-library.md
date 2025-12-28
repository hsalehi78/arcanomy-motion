# B-roll Library (local) + Index

## Goal

No browsing. All b-roll is resolvable from a local library.

## Minimum viable library

- 200–400 clips
- all 9:16 (or safe-crop to 9:16)
- licensed/cleared sources only

## Folder structure

```
content/libraries/broll/
  clips/
    broll-0001.mp4
    broll-0002.mp4
    ...
  index.json
```

## `index.json` schema (MVP)

Each clip entry should contain:

- `id` (stable)
- `path` (relative to `content/libraries/broll/`)
- `duration_seconds`
- `orientation` (`9:16` | `16:9` | `1:1`)
- `tags[]` (topic + vibe)
- `composition` (`wide` | `medium` | `close` | `macro` | `abstract`)
- `has_faces` (bool)
- `has_logos` (bool)
- `motion` (`static` | `slow` | `medium` | `fast`)
- `notes` (optional)

### Clip ID generation (confirmed direction)

If you don’t have stable IDs already, generate `id` deterministically from:
- normalized relative path, plus
- file hash (recommended: sha256 of the file bytes or first N MB)

## Resolution rules

- No clip repeats inside one reel.
- Exclude clips used in last 14 days (ledger).
- Prefer strong composition match over “perfect tag match”.
- Keep category diversity (don’t pick 6 “shopping” clips).

## Transitions / fallback pack

You said you **don’t have a transitions pack yet**. v2 should start with a tiny “abstract” pack (10–30 clips) to prevent AI fallback from becoming the default failure mode.
