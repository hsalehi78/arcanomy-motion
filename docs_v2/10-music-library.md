# Music Library (local) + Index

## Goal

Music selection is deterministic and ledger-aware.

## Folder structure

```
content/libraries/music/
  tracks/
    track-0001.mp3
    track-0002.mp3
    ...
  index.json
```

## `index.json` schema (MVP)

- `id` (stable)
- `path` (relative)
- `duration_seconds`
- `bpm` (optional)
- `mood_tags[]` (e.g., `contemplative`, `tense_resolution`, `uplifting`, `dramatic`)
- `has_vocals` (bool)
- `intensity` (`low` | `medium` | `high`)

## Selection rules

- Exclude last 7 days (ledger).
- Vocals: allowed (confirmed). Still recommended to default to **no vocals** unless the mood tag explicitly asks for it.
- No drops by default.
- If the beat sheet includes a SOUND_RESET moment, allow a small “micro-rise” after it.

