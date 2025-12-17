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

    typer.echo(f"\n✓ Created new reel at: {reel_path}")
    typer.echo(f"  Source blog: {blog.title}")
    typer.echo(f"\n  Files created:")
    typer.echo(f"    - {reel_path}/00_seed.md")
    typer.echo(f"    - {reel_path}/00_reel.yaml")
    typer.echo(f"\n  Next steps:")
    typer.echo(f"    1. Review and edit the seed/config files")
    typer.echo(f"    2. Run: uv run arcanomy run {reel_path}")


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


# Standalone commit command entry point
_commit_app = typer.Typer()
_commit_app.command()(commit)


def run_commit():
    """Entry point for standalone 'uv run commit' command."""
    _commit_app()


if __name__ == "__main__":
    app()

