"""Stage 3.5: Asset Generation - Generate images from prompts."""

import json
from datetime import datetime
from pathlib import Path

from src.services import LLMService
from src.utils.io import read_file, write_file

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_system_prompt() -> str:
    """Load the asset generation system prompt from shared/prompts."""
    prompt_path = PROMPTS_DIR / "03.5_asset_generation_system.md"
    if prompt_path.exists():
        return read_file(prompt_path)
    return ""


def run_asset_generation(reel_path: Path, llm: LLMService = None) -> list[dict]:
    """Generate images from the visual plan prompts.

    This is the "dumb script" execution stage that:
    1. Reads 03_visual_plan.output.json
    2. Combines global_atmosphere + each asset's image_prompt
    3. Calls image generation API
    4. Saves images to renders/images/

    Args:
        reel_path: Path to the reel folder
        llm: LLM service (optional, for future API integration)

    Returns:
        List of generation results
    """
    # Load the visual plan JSON
    visual_plan_path = reel_path / "03_visual_plan.output.json"
    
    if not visual_plan_path.exists():
        raise FileNotFoundError(
            f"03_visual_plan.output.json not found. Run Stage 3 (uv run plan) first.\n"
            f"Expected: {visual_plan_path}"
        )
    
    with open(visual_plan_path, "r", encoding="utf-8") as f:
        visual_plan = json.load(f)
    
    global_atmosphere = visual_plan.get("global_atmosphere", "")
    assets = visual_plan.get("assets", [])
    
    if not assets:
        raise ValueError(
            "No assets found in 03_visual_plan.output.json. "
            "The visual plan may be incomplete or malformed."
        )
    
    # Create renders directory structure
    renders_dir = reel_path / "renders"
    images_dir = renders_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare execution log
    execution_log = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "reel_folder": reel_path.name,
        "global_atmosphere": global_atmosphere[:200] + "..." if len(global_atmosphere) > 200 else global_atmosphere,
        "total_assets": len(assets),
        "successful": 0,
        "failed": 0,
        "assets": [],
        "failures": []
    }
    
    # Save input/execution plan
    input_path = reel_path / "03.5_asset_generation.input.md"
    input_content = f"""# Asset Generation Stage Input

## Source File
`03_visual_plan.output.json`

## Global Atmosphere
```
{global_atmosphere}
```

## Assets to Generate ({len(assets)} total)

"""
    for asset in assets:
        input_content += f"""### {asset.get('id', 'unknown')}
- **Name:** {asset.get('name', 'Unknown')}
- **Type:** {asset.get('type', 'unknown')}
- **Segments:** {asset.get('used_in_segments', [])}
- **Filename:** {asset.get('suggested_filename', 'unknown.png')}

"""
    
    input_content += """---

## Execution Plan

For each asset:
1. Combine: global_atmosphere + image_prompt
2. Call image generation API (DALL-E / Midjourney / Gemini)
3. Save to: renders/images/{suggested_filename}
"""
    write_file(input_path, input_content)
    
    # Process each asset
    for asset in assets:
        asset_id = asset.get("id", "unknown")
        image_prompt = asset.get("image_prompt", "")
        suggested_filename = asset.get("suggested_filename", f"{asset_id}.png")
        output_path = images_dir / suggested_filename
        
        # Combine prompts
        full_prompt = f"{global_atmosphere}\n\n{image_prompt}"
        
        # TODO: Implement actual image generation API calls
        # For now, log what would be generated
        
        # Check if image already exists (for resume functionality)
        if output_path.exists():
            execution_log["assets"].append({
                "id": asset_id,
                "status": "exists",
                "path": str(output_path.relative_to(reel_path)),
                "message": "Image already exists, skipping"
            })
            execution_log["successful"] += 1
            continue
        
        # Placeholder: Mark as pending until actual API is implemented
        execution_log["assets"].append({
            "id": asset_id,
            "status": "pending",
            "path": str(output_path.relative_to(reel_path)),
            "prompt_length": len(full_prompt),
            "message": "Image generation API not yet implemented. Use prompts manually."
        })
        
        # Save the full prompt for manual generation
        prompt_file = images_dir / f"{asset_id}_prompt.txt"
        write_file(prompt_file, full_prompt)
    
    # Save output
    output_path = reel_path / "03.5_asset_generation.output.json"
    write_file(output_path, json.dumps(execution_log, indent=2))
    
    return execution_log["assets"]


def run_video_generation(reel_path: Path) -> list[dict]:
    """Generate video clips from images using motion prompts.

    This is Stage 4.5 - animates static images into 10-second video clips.

    Args:
        reel_path: Path to the reel folder

    Returns:
        List of video generation results
    """
    # Load the visual plan JSON for motion prompts
    visual_plan_path = reel_path / "03_visual_plan.output.json"
    
    if not visual_plan_path.exists():
        raise FileNotFoundError(
            f"03_visual_plan.output.json not found. Run Stage 3 first."
        )
    
    with open(visual_plan_path, "r", encoding="utf-8") as f:
        visual_plan = json.load(f)
    
    assets = visual_plan.get("assets", [])
    
    # Create renders directory structure
    renders_dir = reel_path / "renders"
    videos_dir = renders_dir / "videos"
    images_dir = renders_dir / "images"
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    execution_log = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "reel_folder": reel_path.name,
        "total_assets": len(assets),
        "videos": []
    }
    
    # Process each asset
    for asset in assets:
        asset_id = asset.get("id", "unknown")
        motion_prompt = asset.get("motion_prompt", "")
        suggested_filename = asset.get("suggested_filename", f"{asset_id}.png")
        
        # Source image path
        image_path = images_dir / suggested_filename
        
        # Output video path (same name, different extension)
        video_filename = suggested_filename.replace(".png", ".mp4")
        video_path = videos_dir / video_filename
        
        # Map to segment IDs for the old naming convention
        segments = asset.get("used_in_segments", [])
        for seg_id in segments:
            bg_video_path = videos_dir / f"bg_{seg_id:02d}.mp4"
            
            execution_log["videos"].append({
                "asset_id": asset_id,
                "segment_id": seg_id,
                "source_image": str(image_path.relative_to(reel_path)) if image_path.exists() else None,
                "output_path": str(bg_video_path.relative_to(reel_path)),
                "motion_prompt": motion_prompt[:200] + "..." if len(motion_prompt) > 200 else motion_prompt,
                "status": "pending",
                "message": "Video generation API not yet implemented"
            })
    
    # Save execution plan
    input_path = reel_path / "04.5_video_generation.input.md"
    input_content = f"""# Video Generation Stage Input

## Source
- Visual Plan: `03_visual_plan.output.json`
- Images: `renders/images/`

## Videos to Generate ({len(execution_log['videos'])} total)

"""
    for video in execution_log["videos"]:
        input_content += f"""### {video['asset_id']} → Segment {video['segment_id']}
- **Source:** {video.get('source_image', 'pending')}
- **Output:** {video['output_path']}
- **Motion:** {video['motion_prompt'][:100]}...

"""
    write_file(input_path, input_content)
    
    # Save output
    output_path = reel_path / "04.5_video_generation.output.json"
    write_file(output_path, json.dumps(execution_log, indent=2))
    
    return execution_log["videos"]
