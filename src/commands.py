"""CLI commands for Arcanomy Motion."""

from pathlib import Path
from typing import Optional

import typer
import yaml

from src.config import DEFAULT_PROVIDERS
from src.domain import Objective
from src.utils.paths import ensure_reel_layout, reel_yaml_path, seed_path
from src.utils.paths import inputs_dir, json_dir, prompts_dir, renders_dir
from src.services import (
    LLMService,
    fetch_featured_blogs,
    fetch_blog_mdx,
    extract_seed_and_config,
    regenerate_seed,
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
    run_captions,
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
    ensure_reel_layout(reel_path)

    # Create seed template
    seed_content = """# Hook
[Your attention-grabbing opening line]

# Core Insight
[The main point or data you want to convey]

# Visual Vibe
[Describe the mood, colors, and visual style]

# Data Sources
- inputs/data/your_data.csv
"""
    seed_path(reel_path).write_text(seed_content, encoding="utf-8")

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
    reel_yaml_path(reel_path).write_text(config_content, encoding="utf-8")

    # Auto-set as current reel
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))

    typer.echo(f"[OK] Created new reel at: {reel_path}")
    typer.echo(f"   (Also set as current reel)")
    typer.echo(f"\n   Edit {seed_path(reel_path)} and {reel_yaml_path(reel_path)} to get started")


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
        DEFAULT_PROVIDERS["research"],
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
        4: ("Assets", lambda: run_asset_generation(reel_path, provider=DEFAULT_PROVIDERS["assets"])),
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
                logger.error(f"  [FAIL] {name} failed: {e}")
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
        ("inputs/seed.md", "Seed"),
        ("inputs/reel.yaml", "Config"),
        ("prompts/01_research.output.md", "Research"),
        ("json/02_story_generator.output.json", "Script"),
        ("json/03_visual_plan.output.json", "Visual Plan"),
        ("json/03.5_asset_generation.output.json", "Images"),
        ("json/04_video_prompt.output.json", "Video Prompts"),
        ("json/04.5_video_generation.output.json", "Videos"),
        ("json/05_voice.output.json", "Voice Direction"),
        ("json/05.5_audio_generation.output.json", "Audio"),
        ("json/06_sound_effects.output.json", "SFX Prompts"),
        ("json/06.5_sound_effects_generation.output.json", "SFX"),
        ("final/final_raw.mp4", "Final (Raw)"),
        ("final/final.mp4", "Final Video (Captioned)"),
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
    ensure_reel_layout(reel_path)

    # Write seed file (explicit UTF-8 for Windows compatibility)
    seed_path(reel_path).write_text(seed_content, encoding="utf-8")

    # Write config file (explicit UTF-8 for Windows compatibility)
    config_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
    reel_yaml_path(reel_path).write_text(config_yaml, encoding="utf-8")

    # Auto-set as current reel
    CURRENT_REEL_FILE.write_text(str(reel_path.resolve()))

    typer.echo(f"\n[OK] Created new reel at: {reel_path}")
    typer.echo(f"   (Auto-set as current reel)")
    typer.echo(f"  Source blog: {blog.title}")
    typer.echo(f"\n  Files created:")
    typer.echo(f"    - {seed_path(reel_path)}")
    typer.echo(f"    - {reel_yaml_path(reel_path)}")
    typer.echo(f"\n  Next steps:")
    typer.echo(f"    1. Review and edit the seed/config files")
    typer.echo(f"    2. Run: uv run full")


@app.command("migrate-reel")
def migrate_reel(
    reel_path: Optional[str] = typer.Argument(
        None,
        help="Path or partial slug of reel to migrate (uses current reel if omitted)",
    ),
):
    """Migrate an existing reel from the legacy flat layout into the new folder layout.

    Legacy layout (root files): 00_seed.md, 00_reel.yaml, 00_data/, *.input.md, *.output.md, *.output.json,
    renders/{voice,sfx}/.

    New layout:
    - inputs/{seed.md,reel.yaml,data/}
    - prompts/*.md
    - json/*.json
    - renders/audio/{voice,sfx}/
    """
    import shutil

    # Resolve reel path (supports partial match like `uv run set`)
    if reel_path:
        path = Path(reel_path)
        if not path.exists():
            reels_dir = Path("content/reels")
            if reels_dir.exists():
                matches = [d for d in reels_dir.iterdir() if d.is_dir() and reel_path in d.name]
                if len(matches) == 1:
                    path = matches[0]
                elif len(matches) > 1:
                    typer.echo("[ERROR] Multiple matches found:", err=True)
                    for m in matches:
                        typer.echo(f"   - {m.name}")
                    raise typer.Exit(1)
                else:
                    typer.echo(f"[ERROR] No reel found matching: {reel_path}", err=True)
                    raise typer.Exit(1)
        reel = path
    else:
        reel = _get_current_reel()

    if not reel.exists():
        typer.echo(f"[ERROR] Reel not found: {reel}", err=True)
        raise typer.Exit(1)

    typer.echo(f"[Reel] {reel.name}")
    typer.echo("Migrating to new layout...")

    ensure_reel_layout(reel)

    moved = {"files": 0, "dirs": 0, "skipped": 0}

    def move_file(src: Path, dst: Path):
        if not src.exists():
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            moved["skipped"] += 1
            return
        shutil.move(str(src), str(dst))
        moved["files"] += 1

    def merge_dir(src: Path, dst: Path):
        if not src.exists() or not src.is_dir():
            return
        dst.mkdir(parents=True, exist_ok=True)
        moved_any = False
        for item in src.iterdir():
            target = dst / item.name
            if target.exists():
                moved["skipped"] += 1
                continue
            shutil.move(str(item), str(target))
            moved_any = True
        # remove old dir if empty
        try:
            if not any(src.iterdir()):
                src.rmdir()
        except Exception:
            pass
        if moved_any:
            moved["dirs"] += 1

    # Legacy root inputs -> inputs/
    move_file(reel / "00_seed.md", seed_path(reel))
    move_file(reel / "00_reel.yaml", reel_yaml_path(reel))
    merge_dir(reel / "00_data", inputs_dir(reel) / "data")

    # Root md prompts -> prompts/
    for md in reel.glob("*.input.md"):
        move_file(md, prompts_dir(reel) / md.name)
    for md in reel.glob("*.output.md"):
        move_file(md, prompts_dir(reel) / md.name)

    # Root json outputs -> json/
    for j in reel.glob("*.output.json"):
        move_file(j, json_dir(reel) / j.name)

    # Legacy renders audio folders -> renders/audio/
    merge_dir(renders_dir(reel) / "voice", renders_dir(reel) / "audio" / "voice")
    merge_dir(renders_dir(reel) / "sfx", renders_dir(reel) / "audio" / "sfx")

    typer.echo(f"[OK] Migration complete: {moved['files']} files moved, {moved['dirs']} dirs merged, {moved['skipped']} skipped")


# =============================================================================
# SHORTHAND STAGE COMMANDS (use after `uv run set <reel>`)
# =============================================================================


@app.command()
def seed(
    focus: Optional[str] = typer.Argument(None, help="Focus prompt to guide seed generation (e.g., 'focus on money psychology')"),
    data: bool = typer.Option(False, "--data", "-d", help="Extract specific data points/statistics from the blog"),
    provider: str = typer.Option(DEFAULT_PROVIDERS["research"], "-p", "--provider", help="LLM provider"),
):
    """Create or regenerate seed.md for current reel.
    
    If the reel was created from a blog, regenerates seed from the source.
    If the reel was created manually, creates a template seed.md.
    
    Examples:
        uv run seed                           # Create template or regenerate
        uv run seed "focus on money"          # With focus prompt (blog reels only)
        uv run seed --data                    # Extract data points (blog reels only)
        uv run seed "emphasize urgency" -d    # Both focus and data
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    reel_path = _get_current_reel()
    _print_context(reel_path, "Seed")
    
    seed_file = seed_path(reel_path)
    config_path = reel_yaml_path(reel_path)
    
    # Check if we have a source blog to regenerate from
    source_blog = None
    if config_path.exists():
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        source_blog = config.get("source_blog")
    
    # CASE 1: Blog-based reel - regenerate from source
    if source_blog:
        blog_title = config.get("title", source_blog)
        
        typer.echo(f"Fetching blog: {source_blog}")
        try:
            from src.services import fetch_blog_mdx
            mdx_content = fetch_blog_mdx(source_blog)
        except Exception as e:
            typer.echo(f"[ERROR] Failed to fetch blog: {e}", err=True)
            raise typer.Exit(1)
        
        if focus:
            typer.echo(f"Focus: {focus}")
        if data:
            typer.echo("Extracting data points...")
        
        from src.config import DATA_EXTRACTION, get_model
        
        typer.echo("Regenerating seed with LLM...")
        typer.echo(f"[LLM] Extractor: {provider} ({get_model(provider)})")
        if data:
            verifier = DATA_EXTRACTION.get("verifier", "gemini")
            typer.echo(f"[LLM] Verifier: {verifier} ({get_model(verifier)})")
        
        llm = LLMService(provider=provider)
        
        try:
            new_seed, csv_content = regenerate_seed(
                mdx_content=mdx_content,
                blog_identifier=source_blog,
                blog_title=blog_title,
                llm=llm,
                focus=focus,
                extract_data=data,
                log_fn=typer.echo,
            )
        except Exception as e:
            typer.echo(f"[ERROR] Failed to generate seed: {e}", err=True)
            raise typer.Exit(1)
        
        seed_file.write_text(new_seed, encoding="utf-8")
        typer.echo(f"\n[OK] Seed regenerated from blog!")
        typer.echo(f"   File: {seed_file}")
        
        # Write CSV if data was extracted
        if csv_content:
            data_dir = reel_path / "inputs" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            csv_file = data_dir / "extracted_data.csv"
            csv_file.write_text(csv_content, encoding="utf-8")
            typer.echo(f"   CSV: {csv_file}")
        
        typer.echo(f"\n   Preview:")
        typer.echo("-" * 40)
        for line in new_seed.strip().split("\n")[:8]:
            typer.echo(f"   {line}")
        typer.echo("   ...")
        return
    
    # Warn about ignored flags for non-blog reels
    if focus:
        typer.echo(f"[WARN] --focus is only used for blog-ingested reels. Ignoring: '{focus}'")
    
    if data:
        typer.echo("[INFO] Manual reel detected (no source_blog).")
        typer.echo("       Creating empty templates for you to fill in.")
        typer.echo("       (LLM extraction only works with blog-ingested reels)")
    
    # CASE 2: Manual reel - create templates if they don't exist
    created_files = []
    
    # Handle --data flag: create sample CSV
    data_dir = reel_path / "inputs" / "data"
    sample_csv = data_dir / "sample.csv"
    if data and not sample_csv.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        sample_csv_content = """# Replace this file with your actual data
# Column 1: x-axis (dates, categories)
# Column 2+: y-axis values (numbers)
date,value
"""
        sample_csv.write_text(sample_csv_content, encoding="utf-8")
        created_files.append(("data/sample.csv", sample_csv))
    
    if not seed_file.exists():
        # Create template seed.md - include data section if --data flag
        if data:
            template_seed = """# Hook
Write your attention-grabbing opening line here.

# Core Insight
What's the main lesson or takeaway? This is the heart of your reel.

# Visual Vibe
Describe the mood, colors, and visual style. Examples:
- "Dark, moody, cinematic. Gold accents on black."
- "Bright, energetic, fast-paced. Neon colors."
- "Calm, minimalist, clean. Soft pastels."

# Data Sources
List your CSV files here. These will be visualized as charts in the reel.
- sample.csv (edit or replace with your data)

## Data Format
Each CSV should have columns that can be charted:
- First column: x-axis (dates, categories, labels)
- Other columns: y-axis values (numbers, percentages)

# Key Data Points
What story does your data tell? List the specific claims your reel will make.
These will be fact-checked against your CSV during research.

- 
- 
- 
"""
        else:
            template_seed = """# Hook
Write your attention-grabbing opening line here.

# Core Insight
What's the main lesson or takeaway? This is the heart of your reel.

# Visual Vibe
Describe the mood, colors, and visual style. Examples:
- "Dark, moody, cinematic. Gold accents on black."
- "Bright, energetic, fast-paced. Neon colors."
- "Calm, minimalist, clean. Soft pastels."

# Data Sources
- (Add CSV files to inputs/data/ if using charts)
"""
        seed_file.parent.mkdir(parents=True, exist_ok=True)
        seed_file.write_text(template_seed, encoding="utf-8")
        created_files.append(("seed.md", seed_file))
    
    if not config_path.exists():
        # Create template reel.yaml
        # Extract slug from reel path for title
        slug = reel_path.name
        # Convert slug to title: "2025-12-15-my-reel" -> "My Reel"
        title_parts = slug.split("-")[3:] if len(slug.split("-")) > 3 else slug.split("-")
        title = " ".join(word.capitalize() for word in title_parts)
        
        # Use chart_explainer type if --data flag is set
        reel_type = "chart_explainer" if data else "story_essay"
        
        template_config = f"""title: "{title}"
type: {reel_type}
duration_blocks: 2
voice_id: eleven_labs_adam
music_mood: contemplative
aspect_ratio: "9:16"
subtitles: burned_in
audit_level: {"strict" if data else "loose"}
"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(template_config, encoding="utf-8")
        created_files.append(("reel.yaml", config_path))
    
    if created_files:
        typer.echo(f"\n[OK] Template files created!")
        for name, path in created_files:
            typer.echo(f"   - {name}: {path}")
        if data:
            typer.echo(f"\n   Data mode enabled:")
            typer.echo(f"   - Type set to 'chart_explainer'")
            typer.echo(f"   - Audit level set to 'strict'")
            typer.echo(f"   - Sample CSV created in inputs/data/")
        typer.echo(f"\n   Next steps:")
        typer.echo(f"   1. Edit seed.md with your creative brief")
        if data:
            typer.echo(f"   2. Replace sample.csv with your actual data")
            typer.echo(f"   3. Edit reel.yaml to adjust duration/voice")
            typer.echo(f"   4. Run: uv run research")
        else:
            typer.echo(f"   2. Edit reel.yaml to adjust duration/voice/type")
            typer.echo(f"   3. Run: uv run research")
        return
    
    # CASE 3: Manual reel with existing seed - show status
    if data:
        typer.echo(f"[INFO] Seed already exists. --data flag only applies when creating new templates.")
    
    typer.echo(f"\n[OK] Seed already exists!")
    typer.echo(f"   File: {seed_file}")
    typer.echo(f"\n   Preview:")
    typer.echo("-" * 40)
    content = seed_file.read_text(encoding="utf-8")
    for line in content.strip().split("\n")[:8]:
        typer.echo(f"   {line}")
    typer.echo("   ...")
    typer.echo(f"\n   To edit: open {seed_file}")
    typer.echo(f"   To proceed: uv run research")


@app.command()
def research(
    provider: str = typer.Option(DEFAULT_PROVIDERS["research"], "-p", "--provider", help="LLM provider"),
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
    provider: str = typer.Option(DEFAULT_PROVIDERS["script"], "-p", "--provider", help="LLM provider"),
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
    provider: str = typer.Option(DEFAULT_PROVIDERS["plan"], "-p", "--provider", help="LLM provider"),
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
    provider: str = typer.Option(DEFAULT_PROVIDERS["assets"], "-p", "--provider", help="Image generation provider (kie, openai, gemini)"),
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
    provider: str = typer.Option(DEFAULT_PROVIDERS["vidprompt"], "-p", "--provider", help="LLM provider"),
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
    provider: str = typer.Option(DEFAULT_PROVIDERS["videos"], "-p", "--provider", help="Video generation provider (veo, kling)"),
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
    provider: str = typer.Option(DEFAULT_PROVIDERS["voice"], "-p", "--provider", help="LLM provider"),
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
    provider: str = typer.Option(DEFAULT_PROVIDERS["sfx"], "-p", "--provider", help="LLM provider"),
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
    captions: bool = typer.Option(False, "--captions/--no-captions", help="Also run Stage 7.5 to burn captions (default: off)"),
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
        typer.echo(f"   Output (raw): {final_info.get('path', 'N/A')}")
        typer.echo(f"   Duration: {final_info.get('duration_seconds', 0):.1f}s")
        typer.echo(f"   Size: {final_info.get('size_mb', 0):.2f} MB")

        # Optional caption burn (Stage 7.5)
        try:
            objective = Objective.from_reel_folder(reel_path)
        except Exception:
            objective = None

        if not dry_run and captions and (objective is None or objective.subtitles == "burned_in"):
            _print_context(reel_path, "Captions (Stage 7.5)")
            caps = run_captions(reel_path)
            typer.echo(f"\n[OK] Captions complete!")
            typer.echo(f"   Output (captioned): {caps.get('captioned_video', 'N/A')}")
            typer.echo(f"   SRT: {caps.get('srt', 'N/A')}")
    elif result.get("status") == "dry_run":
        typer.echo(f"\n[DRY RUN] Would process {result.get('clips', 0)} clips")
    else:
        typer.echo(f"\n❌ Assembly failed: {result.get('error', 'Unknown error')}", err=True)
        raise typer.Exit(1)


@app.command()
def captions():
    """Run captions stage (Stage 7.5) on current reel.

    Requires Stage 7 output: final/final_raw.mp4.
    Produces:
    - json/07.5_captions.output.json
    - final/final.srt
    - final/final.mp4 (captioned)
    """
    reel_path = _get_current_reel()
    _print_context(reel_path, "Captions (Stage 7.5)")

    result = run_captions(reel_path)
    typer.echo(f"\n[OK] Captions complete!")
    typer.echo(f"   Output (captioned): {result.get('captioned_video', 'N/A')}")
    typer.echo(f"   SRT: {result.get('srt', 'N/A')}")


@app.command("full")
def full_pipeline(
    reel_path: Optional[str] = typer.Argument(None, help="Path to reel folder (uses current if not provided)"),
    resume: bool = typer.Option(True, "--resume/--fresh", help="Resume from last completed stage (default) or start fresh"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Run in dry-run mode (no API calls)"),
    skip_videos: bool = typer.Option(False, "--skip-videos", help="Skip video generation (uses images only)"),
    provider: Optional[str] = typer.Option(None, "-p", "--provider", help="Override LLM provider for all stages (openai, anthropic, gemini)"),
):
    """Run the COMPLETE pipeline from research to final video.
    
    This is the fully automated end-to-end workflow that:
    
    1. Research (Stage 1)     - Gathers facts and context
    2. Script (Stage 2)       - Writes voiceover and segments  
    3. Plan (Stage 3)         - Creates visual plan and prompts
    4. Assets (Stage 3.5)     - Generates images
    5. Vidprompt (Stage 4)    - Refines video motion prompts
    6. Videos (Stage 4.5)     - Generates video clips (2-5 min each)
    7. Voice (Stage 5)        - Creates voice direction
    8. Audio (Stage 5.5)      - Generates narrator audio
    9. SFX (Stage 6)          - Creates sound effects prompts
    10. SFXgen (Stage 6.5)    - Generates sound effects
    11. Final (Stage 7)       - Assembles final.mp4
    
    The pipeline automatically waits for API responses and resumes from
    the last completed stage if interrupted.
    
    Examples:
        uv run full                              # Run on current reel
        uv run full content/reels/my-reel        # Run on specific reel
        uv run full --fresh                      # Force restart from stage 1
        uv run full --skip-videos                # Skip video generation
    """
    import time
    from datetime import datetime
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    
    load_dotenv()
    console = Console()
    
    # Resolve reel path
    if reel_path:
        path = Path(reel_path)
        if not path.exists():
            # Try to find it in content/reels
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
            typer.echo(f"[ERROR] Reel not found: {path}", err=True)
            raise typer.Exit(1)
        
        # Set as current reel
        CURRENT_REEL_FILE.write_text(str(path.resolve()))
        reel = path
    else:
        reel = _get_current_reel()

    objective = Objective.from_reel_folder(reel)
    
    # Print header
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Full Pipeline Execution[/bold cyan]\n"
        f"[dim]Reel: {reel.name}[/dim]",
        border_style="cyan"
    ))
    console.print()
    
    # Helper to get LLM provider (use override if provided, otherwise default)
    def get_llm_provider(stage_key: str) -> str:
        return provider if provider else DEFAULT_PROVIDERS[stage_key]
    
    # Define all stages with their check files and runner functions
    stages = [
        {
            "name": "Research",
            "stage": "1",
            "check_file": "prompts/01_research.output.md",
            "run": lambda: run_research(reel, LLMService(provider=get_llm_provider("research"))),
        },
        {
            "name": "Script",
            "stage": "2", 
            "check_file": "json/02_story_generator.output.json",
            "run": lambda: run_script(reel, LLMService(provider=get_llm_provider("script"))),
        },
        {
            "name": "Visual Plan",
            "stage": "3",
            "check_file": "json/03_visual_plan.output.json",
            "run": lambda: run_visual_plan(reel, LLMService(provider=get_llm_provider("plan"))),
        },
        {
            "name": "Assets",
            "stage": "3.5",
            "check_file": "json/03.5_asset_generation.output.json",
            "run": lambda: run_asset_generation(reel, provider=DEFAULT_PROVIDERS["assets"], dry_run=dry_run),
        },
        {
            "name": "Video Prompts",
            "stage": "4",
            "check_file": "json/04_video_prompt.output.json",
            "run": lambda: run_vidprompt(reel, LLMService(provider=get_llm_provider("vidprompt"))),
        },
        {
            "name": "Videos",
            "stage": "4.5",
            "check_file": "json/04.5_video_generation.output.json",
            "run": lambda: run_video_generation(reel, provider=DEFAULT_PROVIDERS["videos"], dry_run=dry_run),
            "skip": skip_videos,
            "skip_reason": "--skip-videos",
        },
        {
            "name": "Voice Direction",
            "stage": "5",
            "check_file": "prompts/05_voice.output.md",
            "run": lambda: run_voice_prompting(reel, LLMService(provider=get_llm_provider("voice"))),
        },
        {
            "name": "Audio",
            "stage": "5.5",
            "check_file": "json/05.5_audio_generation.output.json",
            "run": lambda: run_audio_generation(reel, dry_run=dry_run),
        },
        {
            "name": "SFX Prompts",
            "stage": "6",
            "check_file": "json/06_sound_effects.output.json",
            "run": lambda: run_sfx_prompting(reel, LLMService(provider=get_llm_provider("sfx"))),
        },
        {
            "name": "SFX Generation",
            "stage": "6.5",
            "check_file": "json/06.5_sound_effects_generation.output.json",
            "run": lambda: run_sfx_generation(reel, dry_run=dry_run),
        },
        {
            "name": "Final Assembly",
            "stage": "7",
            "check_file": "final/final_raw.mp4",
            "run": lambda: run_final_assembly(reel, dry_run=dry_run),
        },
        {
            "name": "Captions",
            "stage": "7.5",
            "check_file": "final/final.mp4",
            "run": lambda: run_captions(reel),
            "skip": objective.subtitles != "burned_in" or dry_run,
            "skip_reason": "--dry-run" if dry_run else "subtitles disabled",
        },
    ]
    
    # Track timing
    start_time = time.time()
    stage_times = {}
    completed = 0
    skipped = 0
    failed = None
    
    # Import video generation function
    from src.stages import run_video_generation
    
    # Run stages
    for i, stage in enumerate(stages):
        stage_name = stage["name"]
        stage_num = stage["stage"]
        check_file = stage["check_file"]
        should_skip = stage.get("skip", False)
        
        # Check if stage should be skipped
        if should_skip:
            reason = stage.get("skip_reason")
            suffix = f" ({reason})" if reason else ""
            console.print(f"[dim]Stage {stage_num}: {stage_name} - SKIPPED{suffix}[/dim]")
            skipped += 1
            continue
        
        # Check if stage already complete (resume mode)
        if resume and (reel / check_file).exists():
            console.print(f"[dim]Stage {stage_num}: {stage_name} - EXISTS (skipping)[/dim]")
            skipped += 1
            continue
        
        # Run the stage
        console.print(f"\n[bold cyan]Stage {stage_num}: {stage_name}[/bold cyan]")
        console.print("-" * 50)
        
        stage_start = time.time()
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(f"Running {stage_name}...", total=None)
                
                # Execute the stage
                result = stage["run"]()
                
                progress.update(task, description=f"[green]{stage_name} complete!")
            
            stage_elapsed = time.time() - stage_start
            stage_times[stage_name] = stage_elapsed
            
            console.print(f"[green][OK][/green] {stage_name} complete ({stage_elapsed:.1f}s)")
            completed += 1
            
        except Exception as e:
            stage_elapsed = time.time() - stage_start
            console.print(f"[red][FAIL][/red] {stage_name} failed after {stage_elapsed:.1f}s: {e}")
            failed = {"stage": stage_name, "error": str(e)}
            break
    
    # Summary
    total_time = time.time() - start_time
    console.print()
    console.print("=" * 60)
    
    if failed:
        console.print(f"[bold red]Pipeline FAILED at Stage: {failed['stage']}[/bold red]")
        console.print(f"[red]Error: {failed['error']}[/red]")
        console.print(f"\n[dim]To resume, run: uv run full {reel.name}[/dim]")
        raise typer.Exit(1)
    
    # Check for final video
    final_path = reel / "final" / "final.mp4"
    if final_path.exists():
        file_size = final_path.stat().st_size / (1024 * 1024)
        console.print(Panel.fit(
            f"[bold green]Pipeline COMPLETE![/bold green]\n\n"
            f"[cyan]Final Video:[/cyan] {final_path}\n"
            f"[cyan]Size:[/cyan] {file_size:.2f} MB\n"
            f"[cyan]Total Time:[/cyan] {total_time/60:.1f} minutes\n"
            f"[cyan]Stages:[/cyan] {completed} completed, {skipped} skipped",
            border_style="green"
        ))
    else:
        console.print(f"[yellow]Pipeline finished but final.mp4 not found[/yellow]")
        console.print(f"   Stages completed: {completed}")
        console.print(f"   Stages skipped: {skipped}")
    
    # Print stage timing breakdown
    if stage_times:
        console.print("\n[bold]Stage Timing:[/bold]")
        for name, elapsed in stage_times.items():
            console.print(f"   {name}: {elapsed:.1f}s")
    
    console.print()


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
        typer.echo("   Or:  uv run reels  (to list available reels)")
        raise typer.Exit(1)
    
    reel_path = _get_current_reel()
    typer.echo(f"[Reel] {reel_path.name}")
    typer.echo(f"   Path: {reel_path}")
    
    # Show quick status
    typer.echo(f"\n   Status:")
    stages = [
        ("inputs/seed.md", "Seed"),
        ("prompts/01_research.output.md", "Research"),
        ("json/02_story_generator.output.json", "Script"),
        ("json/03_visual_plan.output.json", "Plan"),
        ("json/03.5_asset_generation.output.json", "Images"),
        ("json/04_video_prompt.output.json", "Vidprompt"),
        ("json/04.5_video_generation.output.json", "Videos"),
        ("prompts/05_voice.output.md", "Voice"),
        ("json/05.5_audio_generation.output.json", "Audio"),
        ("json/06_sound_effects.output.json", "SFX"),
        ("json/06.5_sound_effects_generation.output.json", "SFXGen"),
        ("final/final_raw.mp4", "Final Raw"),
        ("final/final.mp4", "Final (Captioned)"),
    ]
    for filename, name in stages:
        exists = (reel_path / filename).exists()
        status = "[x]" if exists else "[ ]"
        typer.echo(f"   {status} {name}")


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
    
    # Get all reel directories
    reel_dirs = sorted([d for d in reels_dir.iterdir() if d.is_dir()], reverse=True)
    
    if not reel_dirs:
        typer.echo("No reels found. Create one with:")
        typer.echo("   uv run arcanomy new <slug>")
        typer.echo("   uv run arcanomy ingest-blog")
        return
    
    # Get current reel for highlighting
    current_reel = None
    if CURRENT_REEL_FILE.exists():
        try:
            current_reel = Path(CURRENT_REEL_FILE.read_text().strip())
        except Exception:
            pass
    
    # Build table
    table = Table(title=f"Available Reels ({len(reel_dirs)})")
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Reel", style="bold")
    table.add_column("Status", style="dim")
    table.add_column("", style="green", width=8)
    
    for i, reel in enumerate(reel_dirs, 1):
        # Determine status
        has_seed = (reel / "inputs" / "seed.md").exists()
        has_final = (reel / "final" / "final.mp4").exists()
        
        if has_final:
            status = "[green]Complete[/green]"
        elif has_seed:
            # Count completed stages
            stage_files = [
                "prompts/01_research.output.md",
                "json/02_story_generator.output.json",
                "json/03_visual_plan.output.json",
                "json/05.5_audio_generation.output.json",
            ]
            done = sum(1 for f in stage_files if (reel / f).exists())
            status = f"Stage {done}/4"
        else:
            status = "[dim]Empty[/dim]"
        
        # Mark current reel
        is_current = current_reel and reel.resolve() == current_reel.resolve()
        current_marker = "[cyan]<< current[/cyan]" if is_current else ""
        
        table.add_row(str(i), reel.name, status, current_marker)
    
    console.print(table)
    console.print()
    
    # Prompt for selection
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


@app.command("kie-credits")
def kie_credits():
    """Check remaining KIE.ai API credits."""
    import requests
    from dotenv import load_dotenv
    from src.config import get_media_api_key
    
    load_dotenv()
    
    try:
        api_key = get_media_api_key("kie")
    except RuntimeError as e:
        typer.echo(f"[ERROR] {e}", err=True)
        typer.echo("\nSet your KIE_API_KEY in .env file:", err=True)
        typer.echo("  KIE_API_KEY=your_api_key_here", err=True)
        raise typer.Exit(1)
    
    typer.echo("Checking KIE.ai credits...")
    
    try:
        response = requests.get(
            "https://api.kie.ai/api/v1/chat/credit",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") == 200:
            credits = data.get("data", 0)
            typer.echo(f"\n[OK] KIE.ai Credits Remaining: {credits}")
            
            # Color-code based on credit level
            if credits < 10:
                typer.echo("   [WARNING] Low credits! Consider topping up.")
            elif credits < 50:
                typer.echo("   [INFO] Credits are running low.")
            else:
                typer.echo("   [OK] Credit balance is healthy.")
        else:
            typer.echo(f"[ERROR] API returned code {data.get('code')}: {data.get('msg')}", err=True)
            raise typer.Exit(1)
            
    except requests.exceptions.RequestException as e:
        typer.echo(f"[ERROR] Failed to check credits: {e}", err=True)
        raise typer.Exit(1)


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
    table.add_row("uv run credits", "Check KIE.ai API credits")
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
    table2.add_row("uv run arcanomy kie-credits", "Check KIE.ai API credits")
    table2.add_row("uv run arcanomy guide", "Show this guide")
    
    console.print(table2)
    
    # Folder Structure
    console.print("\n[bold yellow]REEL FOLDER STRUCTURE[/bold yellow]")
    console.print("-" * 60)
    
    structure = """
[dim]content/reels/2025-12-15-my-reel/[/dim]
+-- [cyan]inputs/seed.md[/cyan]           [dim]<- Your creative brief (edit this)[/dim]
+-- [cyan]inputs/reel.yaml[/cyan]         [dim]<- Config: duration, voice, type[/dim]
+-- [cyan]inputs/data/[/cyan]             [dim]<- CSV files for charts[/dim]
+-- [green]prompts/01_research.output.md[/green]  [dim]<- Stage 1 output[/dim]
+-- [green]json/02_story_generator.output.json[/green]  [dim]<- Stage 2 segments[/dim]
+-- [green]prompts/03_visual_plan.output.md[/green]  [dim]<- Stage 3 plan[/dim]
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
        uv run arcanomy render-chart content/reels/my-reel/inputs/data/chart.json
        uv run arcanomy render-chart chart.json -o output/my-chart.mp4
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


# Seed
_seed_app = typer.Typer()
_seed_app.command()(seed)

def _run_seed():
    """Entry point for 'uv run seed'."""
    _seed_app()


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


# Captions
_captions_app = typer.Typer()
_captions_app.command()(captions)

def _run_captions():
    """Entry point for 'uv run captions'."""
    _captions_app()


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


# Migrate (shorthand)
_migrate_app = typer.Typer()
_migrate_app.command()(migrate_reel)

def _run_migrate():
    """Entry point for standalone 'uv run migrate' command."""
    _migrate_app()


# Reels
_reels_app = typer.Typer()
_reels_app.command()(reels)

def _run_reels():
    """Entry point for 'uv run reels'."""
    _reels_app()


# Full Pipeline
_full_app = typer.Typer()
_full_app.command()(full_pipeline)

def _run_full():
    """Entry point for 'uv run full'."""
    _full_app()


# KIE Credits
_credits_app = typer.Typer()
_credits_app.command()(kie_credits)

def _run_credits():
    """Entry point for 'uv run credits'."""
    _credits_app()


# Chart
_chart_app = typer.Typer()
_chart_app.command()(render_chart)

def _run_chart():
    """Entry point for 'uv run chart'."""
    _chart_app()


if __name__ == "__main__":
    app()

