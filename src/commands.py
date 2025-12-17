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
    run_asset_generation,
    run_assembly,
    run_delivery,
    run_voice_prompting,
    run_audio_generation,
    run_music_selection,
)
from src.utils.logger import get_logger

app = typer.Typer(
    name="arcanomy",
    help="Arcanomy Motion - AI-powered short-form video production pipeline",
)

logger = get_logger()


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

    typer.echo(f"✓ Created new reel at: {reel_path}")
    typer.echo(f"  Edit {reel_path}/00_seed.md and 00_reel.yaml to get started")


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
        4: ("Assets", lambda: run_asset_generation(reel_path, llm)),
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
                logger.info(f"  ✓ {name} complete")
            except Exception as e:
                logger.error(f"  ✗ {name} failed: {e}")
                raise typer.Exit(1)

    typer.echo("✓ Pipeline complete")


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
        ("03_character_generation.output.md", "Visual Plan"),
        ("03.5_generate_assets_agent.output.json", "Asset Prompts"),
        ("04.5_generate_videos_agent.output.json", "Videos"),
        ("05.5_generate_audio_agent.output.json", "Audio"),
        ("06_music.output.json", "Music"),
        ("07_assemble_final_agent.output.json", "Manifest"),
        ("final/final.mp4", "Final Video"),
    ]

    typer.echo(f"\nPipeline status for: {reel_path.name}\n")
    for filename, name in stages:
        exists = (reel_path / filename).exists()
        status = "✓" if exists else "○"
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
    identifier: str = typer.Argument(..., help="Blog identifier from list-blogs"),
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
):
    """Create a new reel from an Arcanomy blog post."""
    from dotenv import load_dotenv

    load_dotenv()

    # Fetch blog metadata to get title and other info
    typer.echo(f"Fetching blog list to find: {identifier}")
    try:
        blogs = fetch_featured_blogs()
        blog = next((b for b in blogs if b.identifier == identifier), None)
    except Exception as e:
        typer.echo(f"Error fetching blog list: {e}", err=True)
        raise typer.Exit(1)

    if not blog:
        typer.echo(f"Error: Blog not found with identifier: {identifier}", err=True)
        typer.echo("Run 'arcanomy list-blogs' to see available blogs.")
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

    typer.echo(f"\n✓ Created new reel at: {reel_path}")
    typer.echo(f"  Source blog: {blog.title}")
    typer.echo(f"\n  Files created:")
    typer.echo(f"    - {reel_path}/00_seed.md")
    typer.echo(f"    - {reel_path}/00_reel.yaml")
    typer.echo(f"\n  Next steps:")
    typer.echo(f"    1. Review and edit the seed/config files")
    typer.echo(f"    2. Run: uv run arcanomy run {reel_path}")


if __name__ == "__main__":
    app()

