"""CLI commands for Arcanomy Motion."""

from pathlib import Path
from typing import Optional

import typer
import yaml

from src.domain import Objective
from src.services import (
    LLMService,
    fetch_featured_blogs,
    fetch_blog_mdx,
    extract_seed_and_config,
)
from src.stages import (
    run_research,
    run_script,
    run_visual_plan,
    run_vidprompt,
    run_asset_generation,
    run_assembly,
    run_delivery,
    run_voice_prompting,
    run_audio_generation,
    run_sfx_prompting,
    run_sfx_generation,
    run_music_selection,
    run_final_assembly,
)
from src.utils.logger import get_logger

app = typer.Typer(
    name="arcanomy",
    help="Arcanomy Motion - AI-powered short-form video production pipeline",
)

logger = get_logger()

# File to store current reel context
CURRENT_REEL_FILE = Path(".current_reel")


def _get_current_reel() -> Path:
    """Get the current reel path from context file."""
    if not CURRENT_REEL_FILE.exists():
        typer.echo("[ERROR] No reel selected. Run: uv run set <reel-path>", err=True)
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
    # Support short paths like "permission-trap" or full paths
    path = Path(reel_path)
    
    # If not a direct path, search in content/reels
    if not path.exists():
        reels_dir = Path("content/reels")
        if reels_dir.exists():
            # Find matching reel by partial name
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
    
    # Save to context file
    CURRENT_REEL_FILE.write_text(str(path.resolve()))
    
    typer.echo(f"[OK] Current reel set to: {path.name}")
    typer.echo(f"   Full path: {path.resolve()}")
    typer.echo(f"\n   Now you can run:")
    typer.echo(f"   uv run research    # Stage 1")
    typer.echo(f"   uv run script      # Stage 2")
    typer.echo(f"   uv run plan        # Stage 3")


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
    """Create a new reel from template."""
    from datetime import date

    reel_name = f"{date.today().isoformat()}-{slug}"
    reel_path = output_dir / reel_name

    if reel_path.exists():
        typer.echo(f"Error: Reel already exists at {reel_path}", err=True)
        raise typer.Exit(1)

    reel_path.mkdir(parents=True)
    (reel_path / "00_data").mkdir()

    # Create seed template
    seed_content = """# Hook
[Your attention-grabbing opening line]

# Core Insight
[The main point or data you want to convey]

# Visual Vibe
[Describe the mood, colors, and visual style]

# Data Sources
- 00_data/your_data.csv
"""
    (reel_path / "00_seed.md").write_text(seed_content)

    # Create config template
    config_content = f"""title: "{slug.replace('-', ' ').title()}"
type: "chart_explainer"
duration_blocks: 2

voice_id: "your_voice_id"
music_mood: "tense_resolution"

aspect_ratio: "9:16"
subtitles: "burned_in"

audit_level: "strict"
"""
    (reel_path / "00_reel.yaml").write_text(config_content)

    # Auto-set as current reel
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))

    typer.echo(f"[OK] Created new reel at: {reel_path}")
    typer.echo(f"   (Also set as current reel)")
    typer.echo(f"\n   Edit {reel_path}/00_seed.md and 00_reel.yaml to get started")


@app.command()
def run(
    reel_path: Path = typer.Argument(..., help="Path to the reel folder"),
    stage: Optional[int] = typer.Option(
        None,
        "--stage",
        "-s",
        help="Run specific stage only (1-7)",
    ),
    provider: str = typer.Option(
        "openai",
        "--provider",
        "-p",
        help="LLM provider (openai, anthropic, gemini)",
    ),
):
    """Run the pipeline for a reel."""
    from dotenv import load_dotenv

    load_dotenv()

    reel_path = Path(reel_path)
    if not reel_path.exists():
        typer.echo(f"Error: Reel not found at {reel_path}", err=True)
        raise typer.Exit(1)

    llm = LLMService(provider=provider)

    stages = {
        1: ("Research", lambda: run_research(reel_path, llm)),
        2: ("Script", lambda: run_script(reel_path, llm)),
        3: ("Visual Plan", lambda: run_visual_plan(reel_path, llm)),
        4: ("Assets", lambda: run_asset_generation(reel_path, provider="kie")),
        5: ("Assembly", lambda: run_assembly(reel_path)),
        6: ("Delivery", lambda: run_delivery(reel_path)),
    }

    if stage:
        if stage not in stages:
            typer.echo(f"Error: Invalid stage {stage}. Must be 1-6.", err=True)
            raise typer.Exit(1)
        name, func = stages[stage]
        logger.info(f"Running stage {stage}: {name}")
        func()
    else:
        for num, (name, func) in stages.items():
            logger.info(f"Running stage {num}: {name}")
            try:
                func()
                logger.info(f"  [OK] {name} complete")
            except Exception as e:
                logger.error(f"  ✗ {name} failed: {e}")
                raise typer.Exit(1)

    typer.echo("[OK] Pipeline complete")


@app.command()
def preview():
    """Start Remotion preview server."""
    from src.services import RemotionCLI

    remotion = RemotionCLI()
    typer.echo("Starting Remotion preview server...")
    process = remotion.preview()
    process.wait()


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
        ("00_seed.md", "Seed"),
        ("00_reel.yaml", "Config"),
        ("01_research.output.md", "Research"),
        ("02_story_generator.output.json", "Script"),
        ("03_visual_plan.output.json", "Visual Plan"),
        ("03.5_asset_generation.output.json", "Images"),
        ("04.5_video_generation.output.json", "Videos"),
        ("05.5_generate_audio_agent.output.json", "Audio"),
        ("06_music.output.json", "Music"),
        ("07_assembly.output.json", "Manifest"),
        ("final/final.mp4", "Final Video"),
    ]

    typer.echo(f"\nPipeline status for: {reel_path.name}\n")
    for filename, name in stages:
        exists = (reel_path / filename).exists()
        status = "[x]" if exists else "[ ]"
        typer.echo(f"  {status} {name}")

    typer.echo()


@app.command("list-blogs")
def list_blogs(
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Maximum number of blogs to show",
    ),
):
    """List available blogs from Arcanomy CDN."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    try:
        blogs = fetch_featured_blogs(limit=limit)
    except Exception as e:
        typer.echo(f"Error fetching blogs: {e}", err=True)
        raise typer.Exit(1)

    if not blogs:
        typer.echo("No blogs found.")
        return

    table = Table(title=f"Available Blogs (showing {len(blogs)})")
    table.add_column("#", style="dim", width=3)
    table.add_column("Published", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Category", style="green")
    table.add_column("Identifier", style="dim")

    for i, blog in enumerate(blogs, 1):
        table.add_row(
            str(i),
            blog.published_date,
            blog.title[:40] + "..." if len(blog.title) > 40 else blog.title,
            blog.category,
            blog.identifier,
        )

    console.print(table)
    typer.echo("\nTo create a reel from a blog, run:")
    typer.echo("  uv run arcanomy ingest-blog <identifier>")


@app.command("ingest-blog")
def ingest_blog(
    identifier: Optional[str] = typer.Argument(
        None,
        help="Blog identifier (optional - will show interactive picker if omitted)",
    ),
    output_dir: Path = typer.Option(
        Path("content/reels"),
        "--output",
        "-o",
        help="Output directory for reels",
    ),
    provider: str = typer.Option(
        "openai",
        "--provider",
        "-p",
        help="LLM provider (openai, anthropic, gemini)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of blogs to show in interactive mode",
    ),
):
    """Create a new reel from an Arcanomy blog post.

    Run without arguments for interactive mode (pick by number).
    """
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table

    load_dotenv()
    console = Console()

    # Fetch blog list
    typer.echo("Fetching blog list...")
    try:
        blogs = fetch_featured_blogs(limit=limit if not identifier else None)
    except Exception as e:
        typer.echo(f"Error fetching blog list: {e}", err=True)
        raise typer.Exit(1)

    # Interactive mode: no identifier provided
    if not identifier:
        if not blogs:
            typer.echo("No blogs found.")
            raise typer.Exit(1)

        # Show numbered list
        table = Table(title=f"Pick a blog (1-{len(blogs)})")
        table.add_column("#", style="bold cyan", width=3)
        table.add_column("Published", style="dim")
        table.add_column("Title", style="bold")
        table.add_column("Category", style="green")

        for i, blog in enumerate(blogs, 1):
            table.add_row(
                str(i),
                blog.published_date,
                blog.title[:50] + "..." if len(blog.title) > 50 else blog.title,
                blog.category,
            )

        console.print(table)
        typer.echo()

        # Prompt for selection
        choice = typer.prompt("Enter number to select", type=int)

        if choice < 1 or choice > len(blogs):
            typer.echo(f"Invalid choice. Enter a number between 1 and {len(blogs)}.", err=True)
            raise typer.Exit(1)

        blog = blogs[choice - 1]
        identifier = blog.identifier
        typer.echo(f"\nSelected: {blog.title}")
    else:
        # Direct mode: find blog by identifier
        blog = next((b for b in blogs if b.identifier == identifier), None)

        if not blog:
            typer.echo(f"Error: Blog not found with identifier: {identifier}", err=True)
            typer.echo("Run 'arcanomy ingest-blog' without arguments to pick interactively.")
            raise typer.Exit(1)

    # Create reel folder using the blog identifier (already has date)
    reel_path = output_dir / identifier

    if reel_path.exists():
        typer.echo(f"Error: Reel already exists at {reel_path}", err=True)
        raise typer.Exit(1)

    # Fetch the MDX content
    typer.echo(f"Fetching MDX content for: {blog.title}")
    try:
        mdx_content = fetch_blog_mdx(identifier)
    except Exception as e:
        typer.echo(f"Error fetching blog content: {e}", err=True)
        raise typer.Exit(1)

    # Use LLM to extract seed and config
    typer.echo("Extracting seed and config using LLM...")
    llm = LLMService(provider=provider)

    try:
        seed_content, config = extract_seed_and_config(mdx_content, blog, llm)
    except Exception as e:
        typer.echo(f"Error extracting content: {e}", err=True)
        raise typer.Exit(1)

    # Create the reel folder structure
    reel_path.mkdir(parents=True)
    (reel_path / "00_data").mkdir()

    # Write seed file
    (reel_path / "00_seed.md").write_text(seed_content)

    # Write config file
    config_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
    (reel_path / "00_reel.yaml").write_text(config_yaml)

    typer.echo(f"\n[OK] Created new reel at: {reel_path}")
    typer.echo(f"  Source blog: {blog.title}")
    typer.echo(f"\n  Files created:")
    typer.echo(f"    - {reel_path}/00_seed.md")
    typer.echo(f"    - {reel_path}/00_reel.yaml")
    typer.echo(f"\n  Next steps:")
    typer.echo(f"    1. Review and edit the seed/config files")
    typer.echo(f"    2. Run: uv run arcanomy run {reel_path}")


# =============================================================================
# SHORTHAND STAGE COMMANDS (use after `uv run set <reel>`)
# =============================================================================


@app.command()
def research(
    provider: str = typer.Option("openai", "-p", "--provider", help="LLM provider"),
):
    """Run research stage (Stage 1) on current reel."""
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Research (Stage 1)")
    
    llm = LLMService(provider=provider)
    output_path = run_research(reel_path, llm)
    
    typer.echo(f"\n[OK] Research complete!")
    typer.echo(f"   Created: {output_path.name}")


@app.command()
def script(
    provider: str = typer.Option("openai", "-p", "--provider", help="LLM provider"),
):
    """Run script stage (Stage 2) on current reel."""
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Script (Stage 2)")
    
    llm = LLMService(provider=provider)
    segments = run_script(reel_path, llm)
    
    typer.echo(f"\n[OK] Script complete!")
    typer.echo(f"   Generated {len(segments)} segments")


@app.command()
def plan(
    provider: str = typer.Option("openai", "-p", "--provider", help="LLM provider"),
):
    """Run visual plan stage (Stage 3) on current reel."""
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Visual Plan (Stage 3)")
    
    llm = LLMService(provider=provider)
    run_visual_plan(reel_path, llm)
    
    typer.echo(f"\n[OK] Visual plan complete!")


@app.command()
def assets(
    provider: str = typer.Option("gemini", "-p", "--provider", help="Image generation provider (gemini, openai, kie)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Save prompts only, don't call API"),
):
    """Run asset generation stage (Stage 3.5) on current reel. Uses Gemini by default."""
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Assets (Stage 3.5)")
    
    results = run_asset_generation(reel_path, provider=provider, dry_run=dry_run)
    
    success = sum(1 for r in results if r.get("status") in ("success", "exists"))
    typer.echo(f"\n[OK] Asset generation complete! ({success}/{len(results)} successful)")


@app.command()
def vidprompt(
    provider: str = typer.Option("openai", "-p", "--provider", help="LLM provider"),
):
    """Run video prompt engineering stage (Stage 4) on current reel."""
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Video Prompts (Stage 4)")
    
    llm = LLMService(provider=provider)
    run_vidprompt(reel_path, llm)
    
    typer.echo(f"\n[OK] Video prompt engineering complete!")


@app.command()
def videos(
    provider: str = typer.Option("kling", "-p", "--provider", help="Video generation provider (kling, runway, veo)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Save prompts only, don't call API"),
):
    """Run video generation stage (Stage 4.5) on current reel."""
    from src.stages import run_video_generation
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Videos (Stage 4.5)")
    
    results = run_video_generation(reel_path, provider=provider, dry_run=dry_run)
    
    typer.echo(f"\n[OK] Video generation prepared! ({len(results)} clips)")


@app.command()
def voice(
    provider: str = typer.Option("openai", "-p", "--provider", help="LLM provider"),
):
    """Run voice prompting stage (Stage 5) on current reel."""
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Voice (Stage 5)")
    
    llm = LLMService(provider=provider)
    output_path = run_voice_prompting(reel_path, llm)
    
    typer.echo(f"\n[OK] Voice prompting complete!")
    typer.echo(f"   Created: {output_path.name}")


@app.command()
def audio(
    voice_id: str = typer.Option(None, "--voice", "-v", help="Override ElevenLabs voice ID"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Save config only, don't call API"),
    skip_duration: bool = typer.Option(False, "--skip-duration", help="Skip iterative duration targeting"),
):
    """Run audio generation stage (Stage 5.5) on current reel.
    
    Generates narrator audio using ElevenLabs TTS with documentary-style voice settings.
    Iteratively adjusts narration to hit 7.5-9 second target duration.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Audio (Stage 5.5)")
    
    results = run_audio_generation(
        reel_path, 
        voice_id=voice_id, 
        dry_run=dry_run,
        skip_duration_check=skip_duration,
    )
    
    success = sum(1 for r in results if r.get("status") in ("success", "success_no_duration_check", "dry_run"))
    typer.echo(f"\n[OK] Audio generation complete! ({success}/{len(results)} successful)")


@app.command()
def sfx(
    provider: str = typer.Option("openai", "-p", "--provider", help="LLM provider"),
):
    """Run sound effects prompting stage (Stage 6) on current reel.
    
    Creates sound effect prompts for each video segment based on the visual plan.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Sound Effects (Stage 6)")
    
    llm = LLMService(provider=provider)
    output_path = run_sfx_prompting(reel_path, llm)
    
    typer.echo(f"\n[OK] Sound effects prompting complete!")
    typer.echo(f"   Created: {output_path.name}")


@app.command()
def sfxgen(
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Save prompts only, don't call API"),
    prompt_influence: float = typer.Option(0.3, "--influence", "-i", help="Prompt influence (0-1)"),
):
    """Run sound effects generation stage (Stage 6.5) on current reel.
    
    Generates sound effect audio using ElevenLabs Sound Effects API.
    Each clip gets a 10-second atmospheric sound effect.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Sound Effects Generation (Stage 6.5)")
    
    results = run_sfx_generation(
        reel_path,
        dry_run=dry_run,
        prompt_influence=prompt_influence,
    )
    
    success = sum(1 for r in results if r.get("status") in ("success", "dry_run"))
    typer.echo(f"\n[OK] Sound effects generation complete! ({success}/{len(results)} successful)")


@app.command("final")
def final(
    sfx_volume: float = typer.Option(0.25, "--sfx", "-s", help="SFX volume (0-1, default 0.25)"),
    voice_volume: float = typer.Option(1.0, "--voice", "-v", help="Voice volume (0-1, default 1.0)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Validate files only, don't process"),
    keep_files: bool = typer.Option(False, "--keep", "-k", help="Keep intermediate files"),
):
    """Run final assembly stage (Stage 7) on current reel.
    
    Assembles the final video using FFmpeg:
    1. Mixes voice (centered) + sound effects for each clip
    2. Combines mixed audio with video clips
    3. Concatenates all clips into final.mp4
    
    Requires FFmpeg to be installed.
    """
    reel_path = _get_current_reel()
    _print_context(reel_path, "Final Assembly (Stage 7)")
    
    result = run_final_assembly(
        reel_path,
        sfx_volume=sfx_volume,
        voice_volume=voice_volume,
        dry_run=dry_run,
        cleanup=not keep_files,
    )
    
    if result.get("status") == "success":
        final_info = result.get("final_video", {})
        typer.echo(f"\n[OK] Final assembly complete!")
        typer.echo(f"   Output: {final_info.get('path', 'N/A')}")
        typer.echo(f"   Duration: {final_info.get('duration_seconds', 0):.1f}s")
        typer.echo(f"   Size: {final_info.get('size_mb', 0):.2f} MB")
    elif result.get("status") == "dry_run":
        typer.echo(f"\n[DRY RUN] Would process {result.get('clips', 0)} clips")
    else:
        typer.echo(f"\n❌ Assembly failed: {result.get('error', 'Unknown error')}", err=True)
        raise typer.Exit(1)


@app.command()
def assemble():
    """Run assembly stage (Stage 5) on current reel."""
    reel_path = _get_current_reel()
    _print_context(reel_path, "Assembly (Stage 5)")
    
    run_assembly(reel_path)
    
    typer.echo(f"\n[OK] Assembly complete!")


@app.command()
def deliver():
    """Run delivery stage (Stage 6) on current reel."""
    reel_path = _get_current_reel()
    _print_context(reel_path, "Delivery (Stage 6)")
    
    run_delivery(reel_path)
    
    typer.echo(f"\n[OK] Delivery complete!")


@app.command()
def current():
    """Show the current reel context."""
    if not CURRENT_REEL_FILE.exists():
        typer.echo("[ERROR] No reel selected.")
        typer.echo("   Run: uv run set <reel-path>")
        raise typer.Exit(1)
    
    reel_path = _get_current_reel()
    typer.echo(f"[Reel] {reel_path.name}")
    typer.echo(f"   Path: {reel_path}")
    
    # Show quick status
    typer.echo(f"\n   Status:")
    stages = [
        ("00_seed.md", "Seed"),
        ("01_research.output.md", "Research"),
        ("02_story_generator.output.json", "Script"),
        ("03_visual_plan.output.json", "Plan"),
        ("03.5_asset_generation.output.json", "Images"),
    ]
    for filename, name in stages:
        exists = (reel_path / filename).exists()
        status = "[x]" if exists else "[ ]"
        typer.echo(f"   {status} {name}")


@app.command()
def guide():
    """Show complete workflow guide and all available commands."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
    console = Console()
    
    # Header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Arcanomy Motion[/bold cyan]\n"
        "[dim]AI-powered short-form video production pipeline[/dim]",
        border_style="cyan"
    ))
    
    # Workflow Overview
    console.print("\n[bold yellow]WORKFLOW OVERVIEW[/bold yellow]")
    console.print("-" * 60)
    
    workflow = """
[bold]1. CREATE OR SELECT A REEL[/bold]
   
   [cyan]Option A:[/cyan] Create from scratch
   [dim]$[/dim] uv run arcanomy new my-reel-slug
   
   [cyan]Option B:[/cyan] Import from Arcanomy blog (interactive)
   [dim]$[/dim] uv run arcanomy ingest-blog
   
   [cyan]Option C:[/cyan] Select existing reel
   [dim]$[/dim] uv run set permission-trap

[bold]2. RUN THE PIPELINE (6 stages)[/bold]
   
   [green]Stage 1:[/green] Research     -> Gathers facts, stats, psychology
   [dim]$[/dim] uv run research
   
   [green]Stage 2:[/green] Script       -> Writes voiceover + segments
   [dim]$[/dim] uv run script
   
   [green]Stage 3:[/green] Visual Plan  -> Defines characters, style, mood
   [dim]$[/dim] uv run plan
   
   [green]Stage 4:[/green] Assets       -> Generates image/video prompts
   [dim]$[/dim] uv run assets
   
   [green]Stage 7:[/green] Final        -> Assembles video with FFmpeg
   [dim]$[/dim] uv run final

[bold]3. PREVIEW & EXPORT[/bold]
   
   [dim]$[/dim] uv run arcanomy preview   [dim]# Start Remotion preview[/dim]
   [dim]$[/dim] uv run arcanomy status <path>  [dim]# Check reel status[/dim]
"""
    console.print(workflow)
    
    # Quick Commands Table
    console.print("\n[bold yellow]QUICK COMMANDS[/bold yellow]")
    console.print("-" * 60)
    
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Command", style="cyan", width=30)
    table.add_column("Description", style="white")
    
    table.add_row("uv run current", "Show current reel + status")
    table.add_row("uv run set <slug>", "Set working reel (partial match OK)")
    table.add_row("uv run research", "Run Stage 1 on current reel")
    table.add_row("uv run script", "Run Stage 2 on current reel")
    table.add_row("uv run plan", "Run Stage 3 on current reel")
    table.add_row("uv run assets", "Run Stage 3.5 on current reel")
    table.add_row("uv run vidprompt", "Run Stage 4 on current reel")
    table.add_row("uv run videos", "Run Stage 4.5 on current reel")
    table.add_row("uv run voice", "Run Stage 5 on current reel")
    table.add_row("uv run audio", "Run Stage 5.5 on current reel")
    table.add_row("uv run sfx", "Run Stage 6 on current reel")
    table.add_row("uv run sfxgen", "Run Stage 6.5 on current reel")
    table.add_row("uv run final", "Run Stage 7 (final assembly)")
    table.add_row("uv run commit", "Git add + commit + push")
    
    console.print(table)
    
    # Full Commands Table
    console.print("\n[bold yellow]FULL COMMANDS (arcanomy CLI)[/bold yellow]")
    console.print("-" * 60)
    
    table2 = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table2.add_column("Command", style="cyan", width=40)
    table2.add_column("Description", style="white")
    
    table2.add_row("uv run arcanomy new <slug>", "Create new reel from template")
    table2.add_row("uv run arcanomy ingest-blog", "Import blog (interactive)")
    table2.add_row("uv run arcanomy ingest-blog <id>", "Import specific blog")
    table2.add_row("uv run arcanomy list-blogs", "Show available blogs")
    table2.add_row("uv run arcanomy run <path>", "Run full pipeline")
    table2.add_row("uv run arcanomy run <path> -s 2", "Run specific stage only")
    table2.add_row("uv run arcanomy status <path>", "Show pipeline status")
    table2.add_row("uv run arcanomy preview", "Start Remotion dev server")
    table2.add_row("uv run arcanomy guide", "Show this guide")
    
    console.print(table2)
    
    # Folder Structure
    console.print("\n[bold yellow]REEL FOLDER STRUCTURE[/bold yellow]")
    console.print("-" * 60)
    
    structure = """
[dim]content/reels/2025-12-15-my-reel/[/dim]
+-- [cyan]00_seed.md[/cyan]           [dim]<- Your creative brief (edit this)[/dim]
+-- [cyan]00_reel.yaml[/cyan]         [dim]<- Config: duration, voice, type[/dim]
+-- [cyan]00_data/[/cyan]             [dim]<- CSV files for charts[/dim]
+-- [green]01_research.output.md[/green]  [dim]<- Stage 1 output[/dim]
+-- [green]02_story_generator.output.json[/green]  [dim]<- Stage 2 segments[/dim]
+-- [green]03_visual_plan.output.md[/green]  [dim]<- Stage 3 plan[/dim]
+-- [blue]renders/[/blue]             [dim]<- Generated media assets[/dim]
+-- [yellow]final/[/yellow]
    +-- final.mp4         [dim]<- The output video[/dim]
    +-- final.srt         [dim]<- Subtitle file[/dim]
    +-- metadata.json     [dim]<- Audit trail[/dim]
"""
    console.print(structure)
    
    # Tips
    console.print("\n[bold yellow]TIPS[/bold yellow]")
    console.print("-" * 60)
    
    tips = """
* [bold]Partial matching:[/bold] [dim]uv run set permission[/dim] finds [dim]2025-12-15-permission-trap[/dim]
* [bold]Resume pipeline:[/bold] Just re-run a stage; it reads previous outputs
* [bold]Retry a stage:[/bold] Delete its [dim].output.*[/dim] files, then re-run
* [bold]Switch LLM:[/bold] Add [dim]-p anthropic[/dim] or [dim]-p gemini[/dim] to any stage
* [bold]Debug prompts:[/bold] Check [dim]*.input.md[/dim] files to see what was sent
"""
    console.print(tips)
    
    # Current Context
    if CURRENT_REEL_FILE.exists():
        try:
            reel_path = Path(CURRENT_REEL_FILE.read_text().strip())
            if reel_path.exists():
                console.print(f"\n[bold green]Current reel:[/bold green] {reel_path.name}")
        except Exception:
            pass
    
    console.print()


# =============================================================================
# GIT COMMANDS
# =============================================================================


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
    modified, added, deleted, untracked = [], [], [], []
    for line in lines:
        status = line[:2]
        file = line[3:]
        if "M" in status:
            modified.append(file)
        elif "A" in status:
            added.append(file)
        elif "D" in status:
            deleted.append(file)
        elif status == "??":
            untracked.append(file)

    total = len(modified) + len(added) + len(deleted) + len(untracked)
    typer.echo(f"Found {total} changed file(s)")
    if modified:
        typer.echo(f"  Modified: {len(modified)}")
    if added:
        typer.echo(f"  Added: {len(added)}")
    if deleted:
        typer.echo(f"  Deleted: {len(deleted)}")
    if untracked:
        typer.echo(f"  Untracked: {len(untracked)}")

    # Stage all changes
    typer.echo("\nStaging all changes...")
    subprocess.run(["git", "add", "-A"], check=True)
    typer.echo("[OK] All changes staged")

    # Generate commit message if not provided
    if not message:
        all_files = modified + added + deleted + untracked
        message = _generate_commit_message(all_files, added, deleted)

    typer.echo(f'\nCommit message: "{message}"')

    # Commit
    typer.echo("\nCommitting...")
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo(f"Commit failed: {result.stderr}", err=True)
        raise typer.Exit(1)
    typer.echo("[OK] Changes committed")

    # Push
    typer.echo("\nPushing to remote...")
    result = subprocess.run(["git", "push"], capture_output=True, text=True)
    if result.returncode != 0:
        typer.echo(f"Push failed: {result.stderr}", err=True)
        typer.echo("You may need to pull first.")
        raise typer.Exit(1)
    typer.echo("[OK] Pushed to remote")

    typer.echo("\n[OK] All done!")


def _generate_commit_message(
    all_files: list[str],
    added: list[str],
    deleted: list[str],
) -> str:
    """Generate a commit message based on changed files."""
    # Categorize
    components = [f for f in all_files if "components/" in f]
    stages = [f for f in all_files if "stages/" in f]
    services = [f for f in all_files if "services/" in f]
    domain = [f for f in all_files if "domain/" in f]
    docs = [f for f in all_files if f.endswith(".md")]
    configs = [f for f in all_files if f.endswith((".yaml", ".toml", ".json"))]
    scripts = [f for f in all_files if "scripts/" in f]
    remotion = [f for f in all_files if "remotion/" in f]

    # Determine message based on primary changes
    if len(added) > len(all_files) // 2 and added:
        primary = added[0]
        name = primary.split("/")[-1]
        return f"Add {name}"

    if len(deleted) > len(all_files) // 2 and deleted:
        if len(deleted) == 1:
            return f"Remove {deleted[0].split('/')[-1]}"
        return f"Remove {len(deleted)} files"

    if stages:
        if len(stages) == 1:
            name = stages[0].split("/")[-1].replace(".py", "")
            return f"Update {name} stage"
        return f"Update {len(stages)} stages"

    if services:
        if len(services) == 1:
            name = services[0].split("/")[-1].replace(".py", "")
            return f"Update {name} service"
        return f"Update {len(services)} services"

    if domain:
        return "Update domain models"

    if components:
        if len(components) == 1:
            name = components[0].split("/")[-1].replace(".tsx", "")
            return f"Update {name} component"
        return f"Update {len(components)} components"

    if remotion:
        return "Update Remotion config"

    if scripts:
        if len(scripts) == 1:
            name = scripts[0].split("/")[-1]
            return f"Update {name}"
        return "Update scripts"

    if configs:
        return "Update configuration"

    if docs:
        return "Update documentation"

    return f"Update {len(all_files)} file{'s' if len(all_files) != 1 else ''}"


# =============================================================================
# STANDALONE ENTRY POINTS (for `uv run <command>`)
# =============================================================================

# Commit
_commit_app = typer.Typer()
_commit_app.command()(commit)

def run_commit():
    """Entry point for standalone 'uv run commit' command."""
    _commit_app()


# Set
_set_app = typer.Typer()
_set_app.command()(set_reel)

def _run_set():
    """Entry point for 'uv run set'."""
    _set_app()


# Research
_research_app = typer.Typer()
_research_app.command()(research)

def _run_research():
    """Entry point for 'uv run research'."""
    _research_app()


# Script
_script_app = typer.Typer()
_script_app.command()(script)

def _run_script():
    """Entry point for 'uv run script'."""
    _script_app()


# Plan
_plan_app = typer.Typer()
_plan_app.command()(plan)

def _run_plan():
    """Entry point for 'uv run plan'."""
    _plan_app()


# Assets
_assets_app = typer.Typer()
_assets_app.command()(assets)

def _run_assets():
    """Entry point for 'uv run assets'."""
    _assets_app()


# Vidprompt
_vidprompt_app = typer.Typer()
_vidprompt_app.command()(vidprompt)

def _run_vidprompt():
    """Entry point for 'uv run vidprompt'."""
    _vidprompt_app()


# Videos
_videos_app = typer.Typer()
_videos_app.command()(videos)

def _run_videos():
    """Entry point for 'uv run videos'."""
    _videos_app()


# Voice
_voice_app = typer.Typer()
_voice_app.command()(voice)

def _run_voice():
    """Entry point for 'uv run voice'."""
    _voice_app()


# Audio
_audio_app = typer.Typer()
_audio_app.command()(audio)

def _run_audio():
    """Entry point for 'uv run audio'."""
    _audio_app()


# SFX
_sfx_app = typer.Typer()
_sfx_app.command()(sfx)

def _run_sfx():
    """Entry point for 'uv run sfx'."""
    _sfx_app()


# SFX Gen
_sfxgen_app = typer.Typer()
_sfxgen_app.command()(sfxgen)

def _run_sfxgen():
    """Entry point for 'uv run sfxgen'."""
    _sfxgen_app()


# Final
_final_app = typer.Typer()
_final_app.command()(final)

def _run_final():
    """Entry point for 'uv run final'."""
    _final_app()


# Assemble
_assemble_app = typer.Typer()
_assemble_app.command()(assemble)

def _run_assemble():
    """Entry point for 'uv run assemble'."""
    _assemble_app()


# Deliver
_deliver_app = typer.Typer()
_deliver_app.command()(deliver)

def _run_deliver():
    """Entry point for 'uv run deliver'."""
    _deliver_app()


# Current
_current_app = typer.Typer()
_current_app.command()(current)

def _run_current():
    """Entry point for 'uv run current'."""
    _current_app()


# Guide
_guide_app = typer.Typer()
_guide_app.command()(guide)

def _run_guide():
    """Entry point for 'uv run guide'."""
    _guide_app()


if __name__ == "__main__":
    app()

