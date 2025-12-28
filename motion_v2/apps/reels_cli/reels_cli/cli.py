from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(no_args_is_help=True, help="Arcanomy Reels v2 CLI (scaffold)")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RunContext:
    schema_version: str
    run_id: str
    created_at: str
    blog: dict
    ledger: dict
    libraries: dict


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@app.command()
def init(
    blog_identifier: str = typer.Option(..., help="Blog identifier, e.g. 2025-08-10-knowledge-the-psychology-of-money"),
    blog_slug: str = typer.Option(..., help="Blog slug, e.g. the-psychology-of-money"),
    day_n: int = typer.Option(1, min=1, help="Day number for this blog (scaffold default=1; later computed via ledger)."),
    date: Optional[str] = typer.Option(None, help="Override date (YYYY-MM-DD). Defaults to today (UTC)."),
    runs_dir: Path = typer.Option(Path("runs"), help="Runs base directory (default: ./runs)."),
    recent_days: int = typer.Option(60, min=1, max=365, help="Ledger lookback window for init context."),
) -> None:
    """
    Create a run folder and write run_context.json.

    This is a steel-thread scaffold for Day 1:
    - no Supabase query yet
    - no blog ingestion yet
    """
    run_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_folder = runs_dir / f"{run_date}_{blog_slug}_day{day_n}"
    _ensure_dir(run_folder)

    run_id = f"{run_date}:{blog_slug}:day{day_n}"
    ctx = RunContext(
        schema_version="1.0",
        run_id=run_id,
        created_at=_iso_now(),
        blog={
            "identifier": blog_identifier,
            "slug": blog_slug,
            # Scaffold: until blog.json exists, hash the identifier + slug.
            "hash": _sha256_text(f"{blog_identifier}:{blog_slug}")[:16],
            "version": "v1",
        },
        ledger={
            "source": "supabase",
            "query": {"blog_slug": blog_slug, "recent_days": recent_days},
        },
        libraries={
            # Scaffold: hashes will be computed from index.json files once libraries are in place.
            "broll_index_hash": "missing_broll_index",
            "music_index_hash": "missing_music_index",
        },
    )

    _write_json(run_folder / "run_context.json", asdict(ctx))

    typer.echo(f"[OK] Created run: {run_folder}")
    typer.echo(f"[OK] Wrote: {run_folder / 'run_context.json'}")

