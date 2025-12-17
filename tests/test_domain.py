"""Tests for domain models."""

import json
import tempfile
from pathlib import Path

import pytest

from src.domain import Objective, Segment, Manifest


class TestSegment:
    def test_to_dict(self):
        segment = Segment(
            id=1,
            duration=10,
            text="Test voiceover",
            visual_intent="Show a chart",
        )
        data = segment.to_dict()
        
        assert data["id"] == 1
        assert data["duration"] == 10
        assert data["text"] == "Test voiceover"
        assert data["visual_intent"] == "Show a chart"

    def test_from_dict(self):
        data = {
            "id": 2,
            "duration": 10,
            "text": "Another test",
            "visual_intent": "Show text",
        }
        segment = Segment.from_dict(data)
        
        assert segment.id == 2
        assert segment.text == "Another test"


class TestManifest:
    def test_from_segments(self):
        segments = [
            Segment(id=1, duration=10, text="Block 1", visual_intent=""),
            Segment(id=2, duration=10, text="Block 2", visual_intent=""),
        ]
        
        manifest = Manifest.from_segments(segments, fps=30)
        
        assert manifest.total_frames == 600  # 20 seconds at 30fps
        assert len(manifest.segments) == 2
        assert manifest.segments[0].start_frame == 0
        assert manifest.segments[1].start_frame == 300

    def test_to_dict(self):
        segments = [
            Segment(id=1, duration=10, text="Test", visual_intent=""),
        ]
        manifest = Manifest.from_segments(segments)
        data = manifest.to_dict()
        
        assert "fps" in data
        assert "segments" in data
        assert "colors" in data


class TestObjective:
    def test_from_reel_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reel_path = Path(tmpdir)
            
            # Create test files
            (reel_path / "00_reel.yaml").write_text("""
title: "Test Reel"
type: "chart_explainer"
duration_blocks: 2
voice_id: "test_voice"
music_mood: "dramatic"
""")
            
            (reel_path / "00_seed.md").write_text("""
# Hook
Test hook line

# Core Insight
Test insight

# Visual Vibe
Dark and moody

# Data Sources
- 00_data/test.csv
""")
            
            obj = Objective.from_reel_folder(reel_path)
            
            assert obj.title == "Test Reel"
            assert obj.type == "chart_explainer"
            assert obj.duration_blocks == 2
            assert obj.hook == "Test hook line"
            assert obj.core_insight == "Test insight"
            assert "00_data/test.csv" in obj.data_sources

    def test_duration_seconds(self):
        obj = Objective(
            title="Test",
            type="chart_explainer",
            duration_blocks=3,
            voice_id="",
            music_mood="",
        )
        
        assert obj.duration_seconds == 30

