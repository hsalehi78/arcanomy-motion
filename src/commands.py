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
from src.services import LLMService
from src.utils.logger import get_logger

app = typer.Typer(
    name="arcanomy",
    help="Arcanomy Motion - CapCut kit pipeline for short-form video production",
)

logger = get_logger()

# File to store current reel context
CURRENT_REEL_FILE = Path(".current_reel")


def _get_current_reel() -> Path:
    """Get the current reel path from context file."""
    if not CURRENT_REEL_FILE.exists():
        typer.echo("[ERROR] No reel selected. Run: uv run arcanomy set <reel-path>", err=True)
        raise typer.Exit(1)
    
    reel_path = Path(CURRENT_REEL_FILE.read_text().strip())
    if not reel_path.exists():
        typer.echo(f"[ERROR] Reel folder no longer exists: {reel_path}", err=True)
        raise typer.Exit(1)
    
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
    
    Creates the reel folder with claim.json and data.json templates.
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

    # Create data.json template
    data = {
        "type": "none",
        "datasets": [],
        "charts": []
    }
    data_path = inputs_dir(reel_path) / "data.json"
    data_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # Create optional seed.md for notes
    seed_content = """# Notes (Optional)

This file is for your personal notes and ideas. It is NOT processed by the pipeline.
The canonical inputs are claim.json and data.json.

## Idea
[Your concept here]

## Visual Style
[Describe the mood and look]
"""
    seed_path(reel_path).write_text(seed_content, encoding="utf-8")

    # Auto-set as current reel
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))

    typer.echo(f"[OK] Created new reel at: {reel_path}")
    typer.echo(f"   (Also set as current reel)")
    typer.echo(f"\n   Edit these files:")
    typer.echo(f"   - {claim_path} (required)")
    typer.echo(f"   - {data_path} (required)")
    typer.echo(f"\n   Then run: uv run arcanomy run {reel_path}")


@app.command()
def run(
    reel_path: Path = typer.Argument(..., help="Path to the reel folder"),
    stage: str = typer.Option(
        "kit",
        "--stage",
        "-s",
        help="How far to run: init|plan|subsegments|voice|captions|charts|kit. Default: kit (full).",
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
):
    """Run the pipeline for a reel.
    
    Generates a CapCut-ready assembly kit from claim.json + data.json inputs.
    Output: subsegments, charts, voice, captions, guides, thumbnail.
    """
    from dotenv import load_dotenv

    load_dotenv()

    reel_path = Path(reel_path)
    if not reel_path.exists():
        typer.echo(f"Error: Reel not found at {reel_path}", err=True)
        raise typer.Exit(1)

    valid_stages = ("init", "plan", "subsegments", "voice", "captions", "charts", "kit")
    if stage not in valid_stages:
        typer.echo(f"[ERROR] --stage must be one of: {', '.join(valid_stages)}", err=True)
        raise typer.Exit(1)

    prov_path = pipeline_init(reel_path, fresh=fresh, force=force)
    typer.echo("[OK] Init complete")
    typer.echo(f"   Provenance: {prov_path}")

    if stage == "init":
        return

    plan_file = generate_plan(reel_path, force=force)
    typer.echo("[OK] Plan complete")
    typer.echo(f"   Plan: {plan_file}")
    if stage == "plan":
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
    reel_path: Path = typer.Argument(..., help="Path to the reel folder"),
):
    """Show pipeline status for a reel."""
    reel_path = Path(reel_path)

    if not reel_path.exists():
        typer.echo(f"Error: Reel not found at {reel_path}", err=True)
        raise typer.Exit(1)

    stages = [
        ("inputs/claim.json", "Claim (input)"),
        ("inputs/data.json", "Data (input)"),
        ("meta/provenance.json", "Provenance"),
        ("meta/plan.json", "Plan"),
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
    if not CURRENT_REEL_FILE.exists():
        typer.echo("[ERROR] No reel selected.")
        typer.echo("   Run: uv run arcanomy set <reel-path>")
        typer.echo("   Or:  uv run arcanomy reels  (to list available reels)")
        raise typer.Exit(1)
    
    reel_path = _get_current_reel()
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
[bold]WORKFLOW[/bold]

1. [cyan]Create a reel:[/cyan]
   $ uv run arcanomy new my-reel-slug

2. [cyan]Edit the inputs:[/cyan]
   - inputs/claim.json  (your main claim)
   - inputs/data.json   (chart data if any)

3. [cyan]Run the pipeline:[/cyan]
   $ uv run arcanomy run content/reels/YYYY-MM-DD-my-reel-slug

4. [cyan]Assemble in CapCut:[/cyan]
   Follow guides/capcut_assembly_guide.md

[bold]OUTPUT STRUCTURE[/bold]

content/reels/<reel>/
  inputs/
    claim.json       <- Your claim (required)
    data.json        <- Chart data (required)
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

  uv run arcanomy new <slug>        Create new reel
  uv run arcanomy run <path>        Run pipeline (full)
  uv run arcanomy run <path> -s plan  Run to plan stage only
  uv run arcanomy status <path>     Show pipeline status
  uv run arcanomy reels             List/select reels
  uv run arcanomy current           Show current reel
  uv run arcanomy set <path>        Set current reel
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
