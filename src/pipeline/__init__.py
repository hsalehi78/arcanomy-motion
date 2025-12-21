"""Arcanomy pipeline - CapCut kit generation.

This is the canonical pipeline based on docs/principles/.
Output: CapCut-ready assembly kit (subsegments, charts, voice, captions, guides).
"""

from src.pipeline.runner import init, v2_init
from src.pipeline.planner import generate_plan, v2_generate_plan
from src.pipeline.visuals import generate_subsegments, v2_generate_subsegments
from src.pipeline.voice import generate_voice, v2_generate_voice
from src.pipeline.captions import generate_captions_srt, v2_generate_captions_srt
from src.pipeline.charts import render_charts, v2_render_charts
from src.pipeline.kit import generate_kit, v2_generate_kit

__all__ = [
    # Primary exports (new naming)
    "init",
    "generate_plan",
    "generate_subsegments",
    "generate_voice",
    "generate_captions_srt",
    "render_charts",
    "generate_kit",
    # Legacy aliases (for backwards compatibility)
    "v2_init",
    "v2_generate_plan",
    "v2_generate_subsegments",
    "v2_generate_voice",
    "v2_generate_captions_srt",
    "v2_render_charts",
    "v2_generate_kit",
]
