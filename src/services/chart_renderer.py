"""Chart rendering service using Remotion."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .remotion_cli import RemotionCLI


# =============================================================================
# DATA MODELS
# =============================================================================


class BarDataPoint(BaseModel):
    """Single data point for a bar chart."""
    
    label: str = Field(..., description="Category label shown below bar")
    value: float = Field(..., description="Numeric value determining bar height")
    color: Optional[str] = Field(None, description="Optional hex color override (e.g., '#FF3B30')")


class BarChartProps(BaseModel):
    """Props for rendering a bar chart."""
    
    title: str = Field("Chart", description="Chart title displayed at top")
    animationDuration: int = Field(45, description="Frames for animation (30 = 1 second)")
    data: list[BarDataPoint] = Field(..., description="List of data points to chart")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Monthly Revenue ($K)",
                "animationDuration": 45,
                "data": [
                    {"label": "Jan", "value": 120},
                    {"label": "Feb", "value": 85},
                    {"label": "Mar", "value": 200},
                    {"label": "Apr", "value": 150},
                    {"label": "May", "value": 280, "color": "#FFD700"},
                    {"label": "Jun", "value": 190},
                ]
            }
        }


# =============================================================================
# CHART RENDERER
# =============================================================================


class ChartRenderer:
    """Service for rendering charts to video using Remotion."""
    
    def __init__(self, remotion_dir: Optional[Path] = None):
        """Initialize chart renderer.
        
        Args:
            remotion_dir: Path to Remotion project directory.
                          Defaults to project's remotion/ folder.
        """
        self.cli = RemotionCLI(remotion_dir)
    
    def render_bar_chart(
        self,
        props: BarChartProps | dict,
        output_path: Path,
    ) -> Path:
        """Render a bar chart to video.
        
        Args:
            props: Chart properties (BarChartProps model or dict)
            output_path: Where to save the rendered video (e.g., "out/chart.mp4")
            
        Returns:
            Path to the rendered video file
        """
        # Convert Pydantic model to dict if needed
        if isinstance(props, BarChartProps):
            props_dict = props.model_dump()
        else:
            # Validate dict against schema
            validated = BarChartProps(**props)
            props_dict = validated.model_dump()
        
        return self.cli.render(
            composition_id="BarChartDemo",
            output_path=Path(output_path),
            props=props_dict,
        )
    
    def render_from_json(
        self,
        json_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Render a chart from a JSON props file.
        
        Args:
            json_path: Path to JSON file containing chart props
            output_path: Where to save video. If None, saves next to JSON file.
            
        Returns:
            Path to the rendered video file
        """
        json_path = Path(json_path)
        
        if not json_path.exists():
            raise FileNotFoundError(f"Chart props file not found: {json_path}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            props_dict = json.load(f)
        
        # Determine chart type from props or filename
        # For now, default to bar chart
        chart_type = props_dict.pop("chartType", "bar")
        
        # Default output path: same folder as JSON, same name but .mp4
        if output_path is None:
            output_path = json_path.parent / f"{json_path.stem}.mp4"
        
        if chart_type == "bar":
            return self.render_bar_chart(props_dict, output_path)
        else:
            raise ValueError(f"Unknown chart type: {chart_type}. Supported: bar")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def render_bar_chart(
    props: BarChartProps | dict,
    output_path: Path,
    remotion_dir: Optional[Path] = None,
) -> Path:
    """Convenience function to render a bar chart.
    
    Args:
        props: Chart properties
        output_path: Where to save the video
        remotion_dir: Optional Remotion project directory
        
    Returns:
        Path to rendered video
    """
    renderer = ChartRenderer(remotion_dir)
    return renderer.render_bar_chart(props, output_path)


def render_chart_from_json(
    json_path: Path,
    output_path: Optional[Path] = None,
    remotion_dir: Optional[Path] = None,
) -> Path:
    """Convenience function to render a chart from JSON file.
    
    Args:
        json_path: Path to JSON props file
        output_path: Where to save video (optional)
        remotion_dir: Optional Remotion project directory
        
    Returns:
        Path to rendered video
    """
    renderer = ChartRenderer(remotion_dir)
    return renderer.render_from_json(json_path, output_path)

