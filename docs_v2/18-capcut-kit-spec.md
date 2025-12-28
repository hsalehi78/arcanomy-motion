# CapCut Kit Spec (v2)

The kit is the only daily deliverable that matters.

## Folder contract

```
07_capcut_kit/
  imports/
    vo.wav
    captions.srt
    clips/
      clip-01.mp4
      ...
    music/
      selected.mp3
    overlays/
      chart.mp4                  # optional
      fallback_math_card.png     # optional
  edit_plan.md
```

## `edit_plan.md` required sections

- **Run header**
  - run_id, date, blog, day_n
  - total duration

- **Clip table**
  - beat_id
  - `t_start–t_end`
  - `clip file`
  - `source_in/source_out`

- **Events**
  - zoom timestamps
  - sound reset timestamp
  - overlay in/out if relevant

- **Captions**
  - emphasis words + timestamps
  - “fix only” notes (hook captions, numbers)

- **Music**
  - ducking target
  - fade-in/out instructions

## Track doctrine (keep this stable)

From your existing doctrine:

- V1: Background
- V2: Chart overlay (if any)
- V3: Captions/overlays
- A1: Voice
- A2: Music
- A3: Sound resets

