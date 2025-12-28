<!--
This file is a template for the generated edit plan.
The generator should output a concrete plan per run with real filenames and timestamps.
-->

## Run

- **run_id**: {{run_id}}
- **date**: {{date}}
- **blog**: {{blog_identifier}}
- **day_n**: {{day_n}}
- **duration**: {{duration_seconds}}s

## CapCut Presets

- **caption preset name**: {{caption_preset_name}}
- **grade preset name (optional)**: {{grade_preset_name}}

## Clip Plan (V1)

| beat_id | t_start–t_end | clip_file | source_in–source_out | notes |
|--------:|---------------|-----------|----------------------|------|
| {{beat_id}} | {{t_start}}–{{t_end}} | {{clip_file}} | {{source_in}}–{{source_out}} | {{notes}} |

## Overlays (V2)

- **chart**: {{chart_file_or_none}}
- **placement**: {{placement_notes}}
- **overlay in/out**: {{overlay_timestamps}}

## Captions (V3)

- **SRT**: `imports/captions.srt`
- **hook caption must be perfect**: {{hook_caption_notes}}
- **emphasis**:
  - {{t}}s → **{{word}}**

## Sound Reset (A3)

- **timestamp**: {{sound_reset_t}}s
- **instruction**: place sound reset SFX and micro-rise music after

## Music (A2)

- **track**: {{music_track}}
- **ducking**:
  - **CapCut target (%)**: {{ducking_target_percent}}
  - **Alt (dB, if you prefer)**: {{ducking_target_db}}
- **fade**: {{fade_in_out}}

## Events (zoom/overlay)

- **zoom events** (from beat sheet):
  - {{t}}s → scale={{zoom_scale}} direction={{zoom_direction}}
