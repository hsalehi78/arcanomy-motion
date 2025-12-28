"""CLI commands for Arcanomy Motion - CapCut Kit Pipeline."""

from pathlib import Path
from typing import Optional
import json

import typer

from src.utils.paths import (
    ensure_pipeline_layout,
    inputs_dir,
    seed_path,
)
from src.pipeline import (
    init as pipeline_init,
    generate_plan,
    generate_subsegments,
    generate_voice,
    generate_captions_srt,
    render_charts,
    generate_kit,
)
from src.pipeline.visual_plan import generate_visual_plan
from src.pipeline.assets import generate_assets
from src.pipeline.vidprompt import generate_video_prompts
from src.pipeline.videos import generate_videos
from src.services import LLMService
from src.utils.logger import get_logger

app = typer.Typer(
    name="arcanomy",
    help="Arcanomy Motion - CapCut kit pipeline for short-form video production",
)

logger = get_logger()

# File to store current reel context
CURRENT_REEL_FILE = Path(".current_reel")


def _get_current_reel(*, allow_missing: bool = False) -> Path | None:
    """Get the current reel path from context file.
    
    Args:
        allow_missing: If True, return None instead of raising when no valid reel.
                       If False (default), raise typer.Exit(1) on error.
    """
    if not CURRENT_REEL_FILE.exists():
        if allow_missing:
            return None
        typer.echo("[INFO] No reel selected.")
        typer.echo("")
        typer.echo("   Pick a reel:")
        typer.echo("     uv run arcanomy reels")
        typer.echo("")
        typer.echo("   Or create one:")
        typer.echo("     uv run arcanomy ingest-blog")
        typer.echo("     uv run arcanomy new <slug>")
        raise typer.Exit(0)  # Not an error, just informational
    
    reel_path = Path(CURRENT_REEL_FILE.read_text().strip())
    if not reel_path.exists():
        # Clean up stale reference - then behave as if no reel was selected
        try:
            CURRENT_REEL_FILE.unlink()
        except Exception:
            pass
        # Now behave as if no current reel was set
        if allow_missing:
            return None
        typer.echo("[INFO] No reel selected.")
        typer.echo("")
        typer.echo("   Pick a reel:")
        typer.echo("     uv run arcanomy reels")
        typer.echo("")
        typer.echo("   Or create one:")
        typer.echo("     uv run arcanomy ingest-blog")
        typer.echo("     uv run arcanomy new <slug>")
        raise typer.Exit(0)  # Not an error, just informational
    
    return reel_path


def _print_context(reel_path: Path, stage_name: str = None):
    """Print current reel context."""
    typer.echo(f"[Reel] {reel_path.name}")
    if stage_name:
        typer.echo(f"[Stage] {stage_name}")
    typer.echo("-" * 40)


@app.command("set")
def set_reel(
    reel_path: str = typer.Argument(..., help="Path to the reel folder (can be partial)"),
):
    """Set the current reel to work on."""
    path = Path(reel_path)
    
    # If not a direct path, search in content/reels
    if not path.exists():
        reels_dir = Path("content/reels")
        if reels_dir.exists():
            matches = [d for d in reels_dir.iterdir() if d.is_dir() and reel_path in d.name]
            if len(matches) == 1:
                path = matches[0]
            elif len(matches) > 1:
                typer.echo(f"[ERROR] Multiple matches found:", err=True)
                for m in matches:
                    typer.echo(f"   - {m.name}")
                raise typer.Exit(1)
            else:
                typer.echo(f"[ERROR] No reel found matching: {reel_path}", err=True)
                raise typer.Exit(1)
    
    if not path.exists():
        typer.echo(f"[ERROR] Reel folder not found: {path}", err=True)
        raise typer.Exit(1)
    
    CURRENT_REEL_FILE.write_text(str(path.resolve()))
    
    typer.echo(f"[OK] Current reel set to: {path.name}")
    typer.echo(f"   Full path: {path.resolve()}")
    typer.echo(f"\n   Now you can run:")
    typer.echo(f"   uv run arcanomy run {path}")


@app.command()
def new(
    slug: str = typer.Argument(..., help="Unique identifier for the reel"),
    output_dir: Path = typer.Option(
        Path("content/reels"),
        "--output",
        "-o",
        help="Output directory for reels",
    ),
):
    """Create a new reel from template.
    
    Creates the reel folder with claim.json template.
    Add chart.json (optional) for chart-based reels.
    """
    from datetime import date

    reel_name = f"{date.today().isoformat()}-{slug}"
    reel_path = output_dir / reel_name

    if reel_path.exists():
        typer.echo(f"Error: Reel already exists at {reel_path}", err=True)
        raise typer.Exit(1)

    reel_path.mkdir(parents=True)
    ensure_pipeline_layout(reel_path)

    # Create claim.json template
    claim = {
        "claim_id": slug,
        "claim_text": "[Your main claim - the sacred sentence]",
        "supporting_data_ref": "ds-01",
        "audit_level": "basic",
        "tags": [],
        "thumbnail_text": "[Text for thumbnail]"
    }
    claim_path = inputs_dir(reel_path) / "claim.json"
    claim_path.write_text(json.dumps(claim, indent=2) + "\n", encoding="utf-8")

    # Create seed.md with required sections per documentation
    seed_content = """# Hook
[Your scroll-stopping opening line - max 15 words]

# Core Insight
[The single main lesson or takeaway - max 50 words. Use specific numbers.]

# Visual Vibe
Dark, moody, cinematic. Gold accents on black.

# Script Structure
**TRUTH:** [The counter-intuitive or confrontational truth]

**MISTAKE:** [The common mistake people make]

**FIX:** [The simple reframe or solution]

# Key Data
- Stat 1: [value]
- Stat 2: [value]
"""
    seed_path(reel_path).write_text(seed_content, encoding="utf-8")

    # Auto-set as current reel
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))

    typer.echo(f"[OK] Created new reel at: {reel_path}")
    typer.echo(f"   (Also set as current reel)")
    typer.echo(f"\n   Edit these files:")
    typer.echo(f"   - {claim_path} (required)")
    typer.echo(f"   - inputs/chart.json (optional, for chart reels)")
    typer.echo(f"\n   Then run: uv run arcanomy run {reel_path}")


@app.command()
def run(
    reel_path: Optional[Path] = typer.Argument(
        None, 
        help="Path to the reel folder (optional - uses current reel if not specified)",
    ),
    stage: str = typer.Option(
        "kit",
        "--stage",
        "-s",
        help="How far to run: init|plan|visual_plan|assets|vidprompt|videos|subsegments|voice|captions|charts|kit. Default: kit (full).",
    ),
    fresh: bool = typer.Option(
        False,
        "--fresh",
        help="Wipe and recreate outputs before running.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Allow overwriting immutable outputs (use sparingly).",
    ),
    no_ai: bool = typer.Option(
        False,
        "--no-ai",
        help="Disable AI/LLM and use placeholder scripts (for testing without API key).",
    ),
    ai_provider: Optional[str] = typer.Option(
        None,
        "--ai-provider",
        help="Override LLM provider (openai|anthropic|gemini).",
    ),
):
    """Run the pipeline for a reel.
    
    Generates a CapCut-ready assembly kit from claim.json + seed.md (+ optional chart.json).
    Uses AI (Opus 4.5 by default) to generate scripts from seed.md.
    Output: subsegments, charts, voice, captions, guides, thumbnail.
    
    If no reel path is provided, uses the current reel (set via 'arcanomy set' or 'arcanomy reels').
    Use --no-ai to disable AI and use placeholder scripts.
    """
    from dotenv import load_dotenv

    load_dotenv()

    # If no path provided, use current reel
    if reel_path is None:
        if not CURRENT_REEL_FILE.exists():
            typer.echo("[ERROR] No reel specified and no current reel set.", err=True)
            typer.echo("", err=True)
            typer.echo("   Either provide a path:", err=True)
            typer.echo("     uv run arcanomy run content/reels/my-reel", err=True)
            typer.echo("", err=True)
            typer.echo("   Or select a reel first:", err=True)
            typer.echo("     uv run arcanomy reels   # Interactive picker", err=True)
            typer.echo("     uv run arcanomy run     # Run the selected reel", err=True)
            raise typer.Exit(1)
        reel_path = _get_current_reel()
        typer.echo(f"[Reel] Using current reel: {reel_path.name}")
    else:
        reel_path = Path(reel_path)
        # Also try to find by partial name in content/reels
        if not reel_path.exists():
            reels_dir = Path("content/reels")
            if reels_dir.exists():
                matches = [d for d in reels_dir.iterdir() if d.is_dir() and str(reel_path) in d.name]
                if len(matches) == 1:
                    reel_path = matches[0]
                    typer.echo(f"[Reel] Found: {reel_path.name}")
                elif len(matches) > 1:
                    typer.echo(f"[ERROR] Multiple reels match '{reel_path}':", err=True)
                    for m in matches:
                        typer.echo(f"   - {m.name}")
                    raise typer.Exit(1)
    
    if not reel_path.exists():
        typer.echo(f"Error: Reel not found at {reel_path}", err=True)
        raise typer.Exit(1)
    
    # Auto-set as current reel for convenience
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))

    valid_stages = ("init", "plan", "visual_plan", "assets", "vidprompt", "videos", "subsegments", "voice", "captions", "charts", "kit")
    if stage not in valid_stages:
        typer.echo(f"[ERROR] --stage must be one of: {', '.join(valid_stages)}", err=True)
        raise typer.Exit(1)

    ai = not no_ai  # AI is default, --no-ai disables it
    if no_ai:
        typer.echo("[Mode] Using placeholder scripts (--no-ai)")
    else:
        typer.echo("[Mode] AI script generation enabled")

    prov_path = pipeline_init(reel_path, fresh=fresh, force=force)
    typer.echo("[OK] Init complete")
    typer.echo(f"   Provenance: {prov_path}")

    if stage == "init":
        return

    plan_file = generate_plan(reel_path, force=force, ai=ai, ai_provider=ai_provider)
    typer.echo("[OK] Plan complete")
    typer.echo(f"   Plan: {plan_file}")
    if stage == "plan":
        return

    # Visual plan (image/motion prompts)
    vp_file = generate_visual_plan(reel_path, force=force, ai=ai, provider_override=ai_provider)
    typer.echo("[OK] Visual plan complete")
    typer.echo(f"   Visual plan: {vp_file}")
    if stage == "visual_plan":
        return

    # Asset generation (images)
    assets = generate_assets(reel_path, force=force)
    typer.echo("[OK] Assets complete")
    success = len([a for a in assets if a.get("status") == "success"])
    typer.echo(f"   Generated: {success} images")
    if stage == "assets":
        return

    # Video prompt refinement
    vp_prompts = generate_video_prompts(reel_path, force=force, ai=ai, provider_override=ai_provider)
    typer.echo("[OK] Video prompts complete")
    typer.echo(f"   Prompts: {vp_prompts}")
    if stage == "vidprompt":
        return

    # Video generation
    videos = generate_videos(reel_path, force=force)
    typer.echo("[OK] Videos complete")
    success = len([v for v in videos if v.get("status") == "success"])
    typer.echo(f"   Generated: {success} clips")
    if stage == "videos":
        return

    outputs = generate_subsegments(reel_path, force=force)
    typer.echo("[OK] Subsegments complete")
    out_dir = str(Path(outputs[0]).parent) if outputs else "subsegments"
    typer.echo(f"   Wrote: {len(outputs)} clips -> {out_dir}")
    if stage == "subsegments":
        return

    wavs = generate_voice(reel_path, force=force)
    typer.echo("[OK] Voice complete")
    wav_dir = str(Path(wavs[0]).parent) if wavs else "voice"
    typer.echo(f"   Wrote: {len(wavs)} wavs -> {wav_dir}")
    if stage == "voice":
        return

    srt = generate_captions_srt(reel_path, force=force)
    typer.echo("[OK] Captions complete")
    typer.echo(f"   SRT: {srt}")
    if stage == "captions":
        return

    charts = render_charts(reel_path, force=force)
    typer.echo("[OK] Charts complete")
    if charts:
        typer.echo(f"   Wrote: {len(charts)} mp4 -> {Path(charts[0]).parent}")
    else:
        typer.echo("   Wrote: 0 (no chart jobs in plan.json)")
    if stage == "charts":
        return

    kit = generate_kit(reel_path, force=force)
    typer.echo("[OK] Kit complete")
    typer.echo(f"   Thumbnail: {kit['thumbnail']}")
    typer.echo(f"   Guide: {kit['capcut_guide']}")
    typer.echo(f"   Checklist: {kit['retention_checklist']}")
    typer.echo(f"   Quality gate: {kit['quality_gate']}")


@app.command()
def status(
    reel_path: Optional[Path] = typer.Argument(
        None, 
        help="Path to the reel folder (optional - uses current reel if not specified)",
    ),
):
    """Show pipeline status for a reel."""
    if reel_path is None:
        reel_path = _get_current_reel()
    else:
        reel_path = Path(reel_path)

    if not reel_path.exists():
        typer.echo(f"Error: Reel not found at {reel_path}", err=True)
        raise typer.Exit(1)

    stages = [
        ("inputs/claim.json", "Claim (input)"),
        ("inputs/chart.json", "Chart (optional)"),
        ("meta/provenance.json", "Provenance"),
        ("meta/plan.json", "Plan"),
        ("meta/visual_plan.json", "Visual Plan"),
        ("renders/images/composites", "Assets (images)"),
        ("meta/video_prompts.json", "Video Prompts"),
        ("renders/videos", "Videos"),
        ("subsegments/subseg-01.mp4", "Subsegments"),
        ("voice/subseg-01.wav", "Voice"),
        ("captions/captions.srt", "Captions"),
        ("thumbnail/thumbnail.png", "Thumbnail"),
        ("guides/capcut_assembly_guide.md", "CapCut Guide"),
        ("guides/retention_checklist.md", "Retention Checklist"),
        ("meta/quality_gate.json", "Quality Gate"),
    ]

    typer.echo(f"\nPipeline status for: {reel_path.name}\n")
    for filename, name in stages:
        exists = (reel_path / filename).exists()
        status_str = "[x]" if exists else "[ ]"
        typer.echo(f"  {status_str} {name}")

    # Check quality gate pass/fail
    qg_path = reel_path / "meta" / "quality_gate.json"
    if qg_path.exists():
        qg = json.loads(qg_path.read_text(encoding="utf-8"))
        passed = qg.get("pass", False)
        reasons = qg.get("reasons", [])
        if passed:
            typer.echo(f"\n  Quality Gate: PASS")
        else:
            typer.echo(f"\n  Quality Gate: FAIL ({len(reasons)} issues)")

        typer.echo()


@app.command()
def preview():
    """Start Remotion preview server."""
    from src.services import RemotionCLI

    remotion = RemotionCLI()
    typer.echo("Starting Remotion preview server...")
    process = remotion.preview()
    process.wait()


@app.command()
def current():
    """Show the current reel context."""
    # _get_current_reel handles all error cases gracefully (no reel, deleted reel)
    reel_path = _get_current_reel(allow_missing=False)
    typer.echo(f"[Reel] {reel_path.name}")
    typer.echo(f"   Path: {reel_path}")
    
    # Show quick status
    typer.echo(f"\n   Status:")
    stages = [
        ("inputs/claim.json", "Claim"),
        ("meta/provenance.json", "Init"),
        ("meta/plan.json", "Plan"),
        ("subsegments/subseg-01.mp4", "Subsegments"),
        ("voice/subseg-01.wav", "Voice"),
        ("captions/captions.srt", "Captions"),
        ("thumbnail/thumbnail.png", "Thumbnail"),
        ("meta/quality_gate.json", "Quality Gate"),
    ]
    for filename, name in stages:
        exists = (reel_path / filename).exists()
        status_str = "[x]" if exists else "[ ]"
        typer.echo(f"   {status_str} {name}")


@app.command()
def reels():
    """List all available reels and optionally select one."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    reels_dir = Path("content/reels")
    
    if not reels_dir.exists():
        typer.echo("[ERROR] No reels directory found at content/reels")
        raise typer.Exit(1)
    
    reel_dirs = sorted([d for d in reels_dir.iterdir() if d.is_dir()], reverse=True)
    
    if not reel_dirs:
        typer.echo("No reels found. Create one with:")
        typer.echo("   uv run arcanomy new <slug>")
        return
    
    # Get current reel for highlighting
    current_reel = None
    if CURRENT_REEL_FILE.exists():
        try:
            current_reel = Path(CURRENT_REEL_FILE.read_text().strip())
        except Exception:
            pass
    
    table = Table(title=f"Available Reels ({len(reel_dirs)})")
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Reel", style="bold")
    table.add_column("Status", style="dim")
    table.add_column("", style="green", width=12)
    
    for i, reel in enumerate(reel_dirs, 1):
        has_claim = (reel / "inputs" / "claim.json").exists()
        has_kit = (reel / "meta" / "quality_gate.json").exists()
        
        if has_kit:
            qg_path = reel / "meta" / "quality_gate.json"
            qg = json.loads(qg_path.read_text(encoding="utf-8"))
            if qg.get("pass"):
                status = "[green]Ready[/green]"
            else:
                status = "[yellow]Kit (issues)[/yellow]"
        elif has_claim:
            status = "Inputs ready"
        else:
            status = "[dim]Empty[/dim]"
        
        is_current = current_reel and reel.resolve() == current_reel.resolve()
        current_marker = "[cyan]<< current[/cyan]" if is_current else ""
        
        table.add_row(str(i), reel.name, status, current_marker)
    
    console.print(table)
    console.print()
    
    choice = typer.prompt("Select reel # (or Enter to skip)", default="", show_default=False)
    
    if choice.strip():
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(reel_dirs):
                selected = reel_dirs[idx]
                CURRENT_REEL_FILE.write_text(str(selected.resolve()))
                typer.echo(f"\n[OK] Current reel set to: {selected.name}")
            else:
                typer.echo(f"[ERROR] Invalid selection. Enter 1-{len(reel_dirs)}", err=True)
        except ValueError:
            typer.echo("[ERROR] Enter a number", err=True)


@app.command("render-chart")
def render_chart(
    json_path: str = typer.Argument(..., help="Path to chart JSON props file"),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output video path (default: same folder as JSON, .mp4 extension)",
    ),
):
    """Render a chart to video from a JSON props file.
    
    Example:
        uv run arcanomy render-chart docs/charts/bar-chart-basic.json
        uv run arcanomy render-chart chart.json -o output/chart.mp4
    """
    from src.services import render_chart_from_json
    
    json_file = Path(json_path)
    if not json_file.exists():
        typer.echo(f"[ERROR] File not found: {json_file}", err=True)
        raise typer.Exit(1)
    
    output_path = Path(output) if output else None
    
    typer.echo(f"[Chart] Rendering from: {json_file}")
    
    try:
        result = render_chart_from_json(json_file, output_path)
        typer.echo(f"[OK] Chart rendered: {result}")
    except Exception as e:
        typer.echo(f"[ERROR] Render failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def commit(
    message: Optional[str] = typer.Option(
        None,
        "--message",
        "-m",
        help="Custom commit message (auto-generated if not provided)",
    ),
):
    """Stage, commit, and push all changes."""
    import subprocess

    # Check for changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    lines = [l for l in result.stdout.strip().split("\n") if l]

    if not lines:
        typer.echo("No changes to commit")
        return

    # Categorize changes
    new_files = []
    modified = []
    for line in lines:
        status = line[:2].strip()
        filepath = line[3:]
        if "?" in status:
            new_files.append(filepath)
        else:
            modified.append(filepath)

    # Build auto message if not provided
    if not message:
        parts = []
        if new_files:
            parts.append(f"add {len(new_files)} files")
        if modified:
            parts.append(f"update {len(modified)} files")
        message = ", ".join(parts) if parts else "update"

    # Git add
    typer.echo("Staging changes...")
    subprocess.run(["git", "add", "-A"], check=True)

    # Git commit
    typer.echo(f"Committing: {message}")
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if "nothing to commit" in result.stdout:
            typer.echo("Nothing to commit (working tree clean)")
            return
        typer.echo(f"Commit failed: {result.stderr}", err=True)
        raise typer.Exit(1)

    # Git push
    typer.echo("Pushing to remote...")
    result = subprocess.run(
        ["git", "push"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo(f"Push failed: {result.stderr}", err=True)
        raise typer.Exit(1)

    typer.echo("[OK] Committed and pushed successfully")


@app.command("list-reels")
def list_reels_cmd(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of reels to show"),
    source: str = typer.Option(
        "cdn",
        "--source",
        "-s",
        help="Source to list from: cdn (remote) or local",
    ),
):
    """List available reels from CDN or local folder."""
    from rich.console import Console
    from rich.table import Table
    from src.services import list_reels as fetch_cdn_reels, ReelEntry

    console = Console()

    if source == "cdn":
        try:
            reels = fetch_cdn_reels(limit=limit)
        except Exception as e:
            typer.echo(f"[ERROR] Failed to fetch reels from CDN: {e}", err=True)
            typer.echo("   (CDN index may not exist yet)")
            raise typer.Exit(1)

        if not reels:
            typer.echo("No reels found on CDN.")
            typer.echo("   The reels index may not exist yet.")
            return

        console.print(f"\n[bold]Available Reels on CDN ({len(reels)})[/bold]\n")
        
        for i, reel in enumerate(reels, 1):
            chart_info = " [cyan](chart)[/cyan]" if reel.has_chart else ""
            console.print(f"  {i}. [bold]{reel.identifier}[/bold]{chart_info}")
            console.print(f"     {reel.format_type} | {reel.created_date}")
        
        console.print()
        console.print("[dim]To fetch: uv run arcanomy fetch <identifier>[/dim]")

    else:
        # List local reels
        reels_dir = Path("content/reels")
        if not reels_dir.exists():
            typer.echo("No local reels directory found.")
            return

        local_reels = sorted([d for d in reels_dir.iterdir() if d.is_dir()], reverse=True)

        if not local_reels:
            typer.echo("No local reels found.")
            return

        table = Table(title=f"Local Reels ({len(local_reels)})")
        table.add_column("#", style="bold cyan", width=3)
        table.add_column("Identifier", style="bold")
        table.add_column("Status", style="dim")

        for i, reel in enumerate(local_reels[:limit], 1):
            has_claim = (reel / "inputs" / "claim.json").exists()
            has_seed = (reel / "inputs" / "seed.md").exists()
            has_kit = (reel / "meta" / "quality_gate.json").exists()

            if has_kit:
                status = "[green]Complete[/green]"
            elif has_claim and has_seed:
                status = "Ready"
            elif has_claim:
                status = "[yellow]Partial[/yellow]"
            else:
                status = "[dim]Empty[/dim]"

            table.add_row(str(i), reel.name, status)

        console.print(table)


@app.command("fetch")
def fetch_reel_cmd(
    identifier: str = typer.Argument(..., help="Reel identifier to fetch from CDN"),
    output_dir: Path = typer.Option(
        Path("content/reels"),
        "--output",
        "-o",
        help="Output directory for reels",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing local files",
    ),
    run_pipeline: bool = typer.Option(
        False,
        "--run",
        "-r",
        help="Immediately run the pipeline after fetching",
    ),
):
    """Fetch a reel's seed files from CDN.

    Downloads claim.json, seed.md, and chart.json (if present) to local folder.

    Example:
        uv run arcanomy fetch 2025-12-26-knowledge-permission-trap
        uv run arcanomy fetch 2025-12-26-knowledge-permission-trap --run
    """
    from src.services import fetch_reel

    typer.echo(f"[Fetch] Fetching reel: {identifier}")

    try:
        reel_path = fetch_reel(identifier, output_dir=output_dir, overwrite=force)
    except FileNotFoundError as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)
    except FileExistsError as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"[ERROR] Failed to fetch reel: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"[OK] Fetched to: {reel_path}")

    # List fetched files
    inputs = reel_path / "inputs"
    for f in ["claim.json", "seed.md", "chart.json"]:
        if (inputs / f).exists():
            typer.echo(f"   - {f}")

    # Set as current reel
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))
    typer.echo(f"   (Set as current reel)")

    if run_pipeline:
        typer.echo("\n" + "=" * 40)
        typer.echo("[Pipeline] Running...")

        prov_path = pipeline_init(reel_path, force=True)
        typer.echo("[OK] Init complete")

        plan_file = generate_plan(reel_path, force=True, ai=True)
        typer.echo("[OK] Plan complete")

        typer.echo(f"\n   Next: uv run arcanomy run")
    else:
        typer.echo(f"\n   Next: uv run arcanomy run")


@app.command("validate")
def validate_cmd(
    reel_path: Optional[Path] = typer.Argument(
        None,
        help="Path to the reel folder (optional - uses current reel if not specified)",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Attempt to auto-fix simple issues (not yet implemented)",
    ),
):
    """Validate reel seed files against the specification.

    Checks claim.json, seed.md, and chart.json (if present) for:
    - Required fields and sections
    - Word count limits (hook: 15, insight: 50, claim: 25)
    - Chart schema compliance
    - Content quality (vague language, em-dashes)

    Example:
        uv run arcanomy validate
        uv run arcanomy validate content/reels/2025-12-26-my-reel
    """
    from rich.console import Console
    from src.services import validate_reel

    console = Console()

    # Resolve reel path
    if reel_path is None:
        reel_path = _get_current_reel()
    else:
        reel_path = Path(reel_path)
        if not reel_path.exists():
            # Try to find by partial name
            reels_dir = Path("content/reels")
            if reels_dir.exists():
                matches = [d for d in reels_dir.iterdir() if d.is_dir() and str(reel_path) in d.name]
                if len(matches) == 1:
                    reel_path = matches[0]
                elif len(matches) > 1:
                    typer.echo(f"[ERROR] Multiple reels match '{reel_path}':", err=True)
                    for m in matches:
                        typer.echo(f"   - {m.name}")
                    raise typer.Exit(1)

    if not reel_path.exists():
        typer.echo(f"[ERROR] Reel not found: {reel_path}", err=True)
        raise typer.Exit(1)

    typer.echo(f"[Validate] {reel_path.name}")
    typer.echo("-" * 40)

    result = validate_reel(reel_path)

    # Display errors
    if result.errors:
        console.print(f"\n[red]Errors ({len(result.errors)}):[/red]")
        for err in result.errors:
            console.print(f"  [red]X[/red] {err}")

    # Display warnings
    if result.warnings:
        console.print(f"\n[yellow]Warnings ({len(result.warnings)}):[/yellow]")
        for warn in result.warnings:
            console.print(f"  [yellow]![/yellow] {warn}")

    # Summary
    if result.passed:
        console.print(f"\n[green][OK] Validation PASSED[/green]")
        if result.warnings:
            console.print(f"  ({len(result.warnings)} warnings)")
    else:
        console.print(f"\n[red][FAIL] Validation FAILED[/red]")
        console.print(f"  {len(result.errors)} errors, {len(result.warnings)} warnings")
        raise typer.Exit(1)


@app.command("list-blogs")
def list_blogs(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of blogs to show"),
):
    """List available blog posts from Arcanomy CDN."""
    from rich.console import Console
    from rich.table import Table
    from src.services import fetch_featured_blogs

    console = Console()
    
    try:
        blogs = fetch_featured_blogs(limit=limit)
    except Exception as e:
        typer.echo(f"[ERROR] Failed to fetch blogs: {e}", err=True)
        raise typer.Exit(1)
    
    if not blogs:
        typer.echo("No blogs found.")
        return
    
    table = Table(title=f"Available Blogs ({len(blogs)})")
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Published", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Category")
    
    for i, blog in enumerate(blogs, 1):
        table.add_row(
            str(i),
            blog.published_date[:10] if blog.published_date else "",
            blog.title[:40] + ("..." if len(blog.title) > 40 else ""),
            blog.category,
        )
    
    console.print(table)


@app.command("ingest-blog")
def ingest_blog(
    identifier: Optional[str] = typer.Argument(
        None,
        help="Blog identifier (optional - interactive picker if not provided)",
    ),
    output_dir: Path = typer.Option(
        Path("content/reels"),
        "--output",
        "-o",
        help="Output directory for reels",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider override (default: uses config)",
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of blogs to show in picker"),
    focus: Optional[str] = typer.Option(
        None,
        "--focus",
        "-f",
        help="Creative direction (e.g., 'focus on the psychological trap')",
    ),
    slug: Optional[str] = typer.Option(
        None,
        "--slug",
        "-s",
        help="Custom slug for reel folder (allows multiple reels from same blog)",
    ),
    run_pipeline: bool = typer.Option(
        False,
        "--run",
        "-r",
        help="Immediately run the pipeline after ingestion",
    ),
    no_ai: bool = typer.Option(
        False,
        "--no-ai",
        help="Disable AI and use placeholder scripts",
    ),
):
    """Create a reel from a blog post. Interactive picker if no identifier provided."""
    from rich.console import Console
    from rich.table import Table
    from dotenv import load_dotenv
    from src.services import fetch_featured_blogs, fetch_blog_mdx, extract_seed_and_config, LLMService
    
    load_dotenv()
    console = Console()
    
    # Fetch blogs
    try:
        blogs = fetch_featured_blogs(limit=limit)
    except Exception as e:
        typer.echo(f"[ERROR] Failed to fetch blogs: {e}", err=True)
        raise typer.Exit(1)
    
    if not blogs:
        typer.echo("No blogs found.")
        raise typer.Exit(1)
    
    # If no identifier, show interactive picker
    selected_blog = None
    if identifier is None:
        table = Table(title="Pick a blog")
        table.add_column("#", style="bold cyan", width=3)
        table.add_column("Published", style="dim")
        table.add_column("Title", style="bold")
        table.add_column("Category")
        
        for i, blog in enumerate(blogs, 1):
            table.add_row(
                str(i),
                blog.published_date[:10] if blog.published_date else "",
                blog.title[:50] + ("..." if len(blog.title) > 50 else ""),
                blog.category,
            )
        
        console.print(table)
        console.print()
        
        choice = typer.prompt("Enter number to select", default="1")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(blogs):
                selected_blog = blogs[idx]
            else:
                typer.echo(f"[ERROR] Invalid selection. Enter 1-{len(blogs)}", err=True)
                raise typer.Exit(1)
        except ValueError:
            typer.echo("[ERROR] Enter a number", err=True)
            raise typer.Exit(1)
    else:
        # Find by identifier
        selected_blog = next((b for b in blogs if b.identifier == identifier), None)
        if not selected_blog:
            # Try partial match
            matches = [b for b in blogs if identifier.lower() in b.identifier.lower()]
            if len(matches) == 1:
                selected_blog = matches[0]
            elif len(matches) > 1:
                typer.echo(f"[ERROR] Multiple blogs match '{identifier}':", err=True)
                for m in matches:
                    typer.echo(f"   - {m.identifier}")
                raise typer.Exit(1)
            else:
                typer.echo(f"[ERROR] No blog found matching: {identifier}", err=True)
                raise typer.Exit(1)
    
    typer.echo(f"\n[Blog] Selected: {selected_blog.title}")
    typer.echo(f"   Identifier: {selected_blog.identifier}")
    
    # Fetch MDX content
    typer.echo("[Blog] Fetching content...")
    try:
        mdx_content = fetch_blog_mdx(selected_blog.identifier)
    except Exception as e:
        typer.echo(f"[ERROR] Failed to fetch blog content: {e}", err=True)
        raise typer.Exit(1)
    
    # Extract seed using 3-step LLM pipeline
    # Anthropic (opus 4.5) → OpenAI (gpt-5.2) → Anthropic (opus 4.5)
    from src.services.blog_ingest import extract_seed_pipeline
    
    typer.echo("[LLM] Starting 3-step extraction pipeline...")
    typer.echo("   (Anthropic → OpenAI → Anthropic)")
    
    try:
        seed_content, config, chart_json = extract_seed_pipeline(
            mdx_content=mdx_content,
            blog=selected_blog,
            focus=focus,
            log_fn=typer.echo,
        )
    except Exception as e:
        typer.echo(f"[ERROR] Seed extraction failed: {e}", err=True)
        raise typer.Exit(1)
    
    # Create reel folder - use custom slug if provided, otherwise use blog identifier
    from datetime import date
    if slug:
        # Custom slug: prefix with date for sorting
        reel_name = f"{date.today().isoformat()}-{slug}"
    else:
        reel_name = selected_blog.identifier
    
    reel_path = output_dir / reel_name
    
    # Check if folder exists and warn if it will be overwritten
    if reel_path.exists():
        if slug:
            typer.echo(f"[WARN] Reel folder already exists, will update: {reel_name}")
        else:
            typer.echo(f"[INFO] Updating existing reel: {reel_name}")
            typer.echo(f"   (Use --slug to create a separate reel from same blog)")
    
    reel_path.mkdir(parents=True, exist_ok=True)
    ensure_pipeline_layout(reel_path)
    
    # Write claim.json (from extracted config)
    claim_id = slug or selected_blog.identifier
    claim = {
        "claim_id": claim_id,
        "claim_text": seed_content.split("# Hook\n")[1].split("\n\n")[0] if "# Hook\n" in seed_content else selected_blog.title,
        "supporting_data_ref": f"blog:{selected_blog.identifier}",
        "audit_level": "basic",
        "tags": selected_blog.tags,
        "thumbnail_text": selected_blog.title,
    }
    claim_path = inputs_dir(reel_path) / "claim.json"
    claim_path.write_text(json.dumps(claim, indent=2) + "\n", encoding="utf-8")
    
    # Write seed.md
    seed_file = seed_path(reel_path)
    seed_file.write_text(seed_content, encoding="utf-8")
    
    # Write chart.json if generated (for math_slap format)
    chart_file = None
    if chart_json:
        chart_file = inputs_dir(reel_path) / "chart.json"
        chart_file.write_text(json.dumps(chart_json, indent=2) + "\n", encoding="utf-8")
    
    # Set as current reel
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))
    
    typer.echo(f"\n[OK] Created reel: {reel_path.name}")
    typer.echo(f"   Claim: {claim_path}")
    typer.echo(f"   Seed: {seed_file}")
    if chart_file:
        typer.echo(f"   Chart: {chart_file}")
    typer.echo(f"   (Set as current reel)")
    
    # Optionally run pipeline
    if run_pipeline:
        typer.echo("\n" + "=" * 40)
        typer.echo("[Pipeline] Running...")
        
        prov_path = pipeline_init(reel_path, force=True)
        typer.echo("[OK] Init complete")
        
        ai = not no_ai
        plan_file = generate_plan(reel_path, force=True, ai=ai)
        typer.echo("[OK] Plan complete")
        
        typer.echo(f"\n   Next: uv run arcanomy run")
    else:
        typer.echo(f"\n   Next steps:")
        typer.echo(f"   1. Review: {claim_path}")
        typer.echo(f"   2. Run:    uv run arcanomy run")


@app.command()
def guide():
    """Show complete workflow guide."""
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Arcanomy Motion - CapCut Kit Pipeline[/bold cyan]\n"
        "[dim]Generate CapCut-ready assembly kits for short-form video[/dim]",
        border_style="cyan"
    ))
    
    workflow = """
[bold]WORKFLOW A: From CDN (Studio-generated seeds)[/bold]

1. [cyan]List available reels:[/cyan]
   $ uv run arcanomy list-reels

2. [cyan]Fetch a reel:[/cyan]
   $ uv run arcanomy fetch 2025-12-26-my-reel-slug

3. [cyan]Validate (optional):[/cyan]
   $ uv run arcanomy validate

4. [cyan]Run the pipeline:[/cyan]
   $ uv run arcanomy run

5. [cyan]Assemble in CapCut:[/cyan]
   Follow guides/capcut_assembly_guide.md

[bold]WORKFLOW B: Manual creation[/bold]

1. [cyan]Create a reel:[/cyan]
   $ uv run arcanomy new my-reel-slug

2. [cyan]Edit the inputs:[/cyan]
   - inputs/claim.json  (your main claim)
   - inputs/seed.md     (Hook, Core Insight, Visual Vibe, Script Structure, Key Data)
   - inputs/chart.json  (optional, for chart-based reels)

3. [cyan]Validate:[/cyan]
   $ uv run arcanomy validate

4. [cyan]Run the pipeline:[/cyan]
   $ uv run arcanomy run

5. [cyan]Assemble in CapCut:[/cyan]
   Follow guides/capcut_assembly_guide.md

[bold]OUTPUT STRUCTURE[/bold]

content/reels/<reel>/
  inputs/
    claim.json       <- Your claim (required)
    chart.json       <- Chart props (optional)
  meta/
    provenance.json  <- Run metadata
    plan.json        <- Segment/subsegment plan
    quality_gate.json <- Pass/fail + issues
  subsegments/
    subseg-01.mp4    <- 10.0s video clips
    subseg-02.mp4
  voice/
    subseg-01.wav    <- Voice per subsegment
  captions/
    captions.srt     <- Line-level captions
  charts/
    chart-*.mp4      <- Rendered charts
  thumbnail/
    thumbnail.png    <- Generated thumbnail
  guides/
    capcut_assembly_guide.md
    retention_checklist.md

[bold]COMMANDS[/bold]

  [cyan]Reel Management:[/cyan]
  uv run arcanomy new <slug>        Create new reel
  uv run arcanomy reels             List/select local reels
  uv run arcanomy current           Show current reel
  uv run arcanomy set <path>        Set current reel

  [cyan]CDN Integration:[/cyan]
  uv run arcanomy list-reels        List reels from CDN
  uv run arcanomy fetch <id>        Fetch reel from CDN
  uv run arcanomy validate          Validate reel files

  [cyan]Pipeline:[/cyan]
  uv run arcanomy run <path>        Run pipeline (full)
  uv run arcanomy run <path> -s plan  Run to plan stage only
  uv run arcanomy status <path>     Show pipeline status

  [cyan]Blog Ingestion:[/cyan]
  uv run arcanomy list-blogs        List blogs from CDN
  uv run arcanomy ingest-blog       Create reel from blog

  [cyan]Tools:[/cyan]
  uv run arcanomy preview           Start Remotion preview
  uv run arcanomy render-chart <json>  Render standalone chart
"""
    console.print(workflow)
    
    if CURRENT_REEL_FILE.exists():
        try:
            reel_path = Path(CURRENT_REEL_FILE.read_text().strip())
            if reel_path.exists():
                console.print(f"\n[bold green]Current reel:[/bold green] {reel_path.name}")
        except Exception:
            pass
    
    console.print()


# Shorthand entry points for `uv run <cmd>` without the arcanomy prefix
# These are thin wrappers that invoke the same typer commands.

_set_app = typer.Typer()
_set_app.command()(set_reel)

def _run_set():
    """Entry point for 'uv run set'."""
    _set_app()


_current_app = typer.Typer()
_current_app.command()(current)

def _run_current():
    """Entry point for 'uv run current'."""
    _current_app()


_guide_app = typer.Typer()
_guide_app.command()(guide)

def _run_guide():
    """Entry point for 'uv run guide'."""
    _guide_app()


_reels_app = typer.Typer()
_reels_app.command()(reels)

def _run_reels():
    """Entry point for 'uv run reels'."""
    _reels_app()


_chart_app = typer.Typer()
_chart_app.command()(render_chart)

def _run_chart():
    """Entry point for 'uv run chart'."""
    _chart_app()


_commit_app = typer.Typer()
_commit_app.command()(commit)

def run_commit():
    """Entry point for 'uv run commit'."""
    _commit_app()


if __name__ == "__main__":
    app()
