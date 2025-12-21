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
    
    # Optional fields matching TypeScript BarChartProps interface
    width: Optional[int] = Field(None, description="Chart width in pixels")
    height: Optional[int] = Field(None, description="Chart height in pixels")
    barGap: Optional[int] = Field(None, description="Gap between bars in pixels")
    showLabels: Optional[bool] = Field(None, description="Show x-axis labels")
    showValues: Optional[bool] = Field(None, description="Show value labels above bars")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Monthly Revenue ($K)",
                "animationDuration": 45,
                "width": 1080,
                "height": 1920,
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


def _strip_comment_fields(obj):
    """Recursively remove all keys starting with '_' (comment/metadata fields).
    
    This allows JSON files to include documentation like:
        "_desc": "This field controls..."
        "_width_desc": "Width in pixels"
    
    These are stripped before passing to Remotion.
    """
    if isinstance(obj, dict):
        return {
            k: _strip_comment_fields(v) 
            for k, v in obj.items() 
            if not k.startswith("_")
        }
    elif isinstance(obj, list):
        return [_strip_comment_fields(item) for item in obj]
    else:
        return obj


# #region agent log
LOG_PATH = r"c:\Dev\arcanomy-motion\.cursor\debug.log"
def _debug_log(location: str, message: str, data: dict):
    import time
    entry = {"location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000), "sessionId": "debug-session"}
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        import json as json_mod
        f.write(json_mod.dumps(entry) + "\n")
# #endregion


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
            props_dict = props.model_dump(exclude_none=True)
        else:
            # Validate dict against schema
            validated = BarChartProps(**props)
            props_dict = validated.model_dump(exclude_none=True)
        
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
        
        # Strip all comment/documentation fields (keys starting with _)
        props_dict = _strip_comment_fields(props_dict)
        
        # Determine chart type from props or filename
        chart_type = props_dict.pop("chartType", "bar")
        
        # #region agent log
        _debug_log("render_from_json", "Props after strip", {
            "keys": list(props_dict.keys()),
            "title_font_size": props_dict.get("title", {}).get("font", {}).get("size") if isinstance(props_dict.get("title"), dict) else "N/A",
            "yAxis_font_size": props_dict.get("yAxis", {}).get("label", {}).get("font", {}).get("size") if isinstance(props_dict.get("yAxis"), dict) else "N/A",
            "xAxis_font_size": props_dict.get("xAxis", {}).get("label", {}).get("font", {}).get("size") if isinstance(props_dict.get("xAxis"), dict) else "N/A",
        })
        # #endregion
        
        # Default output path: same folder as JSON, same name but .mp4
        if output_path is None:
            output_path = json_path.parent / f"{json_path.stem}.mp4"
        
        if chart_type == "bar":
            # Pass comprehensive props directly to Remotion
            # The TypeScript BarChart component handles all nested props
            # #region agent log
            _debug_log("render_from_json", "Passing to Remotion", {"props_sample": str(props_dict)[:500]})
            # #endregion
            return self.cli.render(
                composition_id="BarChartDemo",
                output_path=Path(output_path),
                props=props_dict,
            )
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

