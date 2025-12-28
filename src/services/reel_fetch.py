"""Reel fetching service for R2/CDN operations.

Fetches reel seed files from Arcanomy CDN for Arcanomy Motion to process.
"""

import httpx
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.utils.logger import get_logger
from src.utils.paths import inputs_dir, ensure_pipeline_layout

logger = get_logger()

# CDN base URL for reels
CDN_BASE_URL = "https://cdn.arcanomydata.com/content/reels"
REELS_INDEX_URL = f"{CDN_BASE_URL}/_indexes/ready.json"


@dataclass
class ReelEntry:
    """Represents a reel entry from the ready index."""

    identifier: str
    title: str
    created_at: str
    format_type: str
    has_chart: bool
    source_blog: Optional[str] = None
    status: str = "ready"

    @classmethod
    def from_dict(cls, data: dict) -> "ReelEntry":
        """Create a ReelEntry from a dictionary."""
        return cls(
            identifier=data["identifier"],
            title=data.get("title", ""),
            created_at=data.get("created_at", ""),
            format_type=data.get("format_type", "unknown"),
            has_chart=data.get("has_chart", False),
            source_blog=data.get("source_blog"),
            status=data.get("status", "ready"),
        )

    @property
    def created_date(self) -> str:
        """Return just the date portion of created_at."""
        if self.created_at:
            try:
                dt = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return self.created_at[:10]
        return ""


def list_reels(limit: Optional[int] = None, status: str = "ready") -> list[ReelEntry]:
    """Fetch the list of reels from the CDN index.

    Args:
        limit: Maximum number of reels to return (most recent first)
        status: Filter by status (default: "ready")

    Returns:
        List of ReelEntry objects sorted by created_at descending
    """
    try:
        response = httpx.get(REELS_INDEX_URL, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning("Reels index not found at CDN. No reels available yet.")
            return []
        raise
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch reels index: {e}")
        raise

    reels = [ReelEntry.from_dict(r) for r in data.get("reels", [])]

    # Filter by status
    if status:
        reels = [r for r in reels if r.status == status]

    # Sort by created_at descending
    reels.sort(key=lambda r: r.created_at, reverse=True)

    if limit:
        reels = reels[:limit]

    return reels


def fetch_reel(
    identifier: str,
    output_dir: Path = Path("content/reels"),
    overwrite: bool = False,
) -> Path:
    """Fetch reel seed files from CDN.

    Downloads claim.json, seed.md, and chart.json (if present) to local folder.

    Args:
        identifier: The reel identifier (folder name on CDN)
        output_dir: Base directory for reels (default: content/reels)
        overwrite: If True, overwrite existing files

    Returns:
        Path to the local reel folder

    Raises:
        FileNotFoundError: If the reel doesn't exist on CDN
        FileExistsError: If local folder exists and overwrite=False
    """
    reel_path = output_dir / identifier
    inputs = inputs_dir(reel_path)

    # Check if already exists
    if reel_path.exists() and not overwrite:
        claim_exists = (inputs / "claim.json").exists()
        seed_exists = (inputs / "seed.md").exists()
        if claim_exists and seed_exists:
            raise FileExistsError(
                f"Reel already exists at {reel_path}. Use --force to overwrite."
            )

    # Ensure directory structure
    ensure_pipeline_layout(reel_path)

    # Fetch required files
    base_url = f"{CDN_BASE_URL}/{identifier}"
    files_fetched = []

    # 1. Fetch claim.json (required)
    claim_url = f"{base_url}/claim.json"
    try:
        response = httpx.get(claim_url, timeout=30.0)
        response.raise_for_status()
        claim_path = inputs / "claim.json"
        claim_path.write_text(response.text, encoding="utf-8")
        files_fetched.append("claim.json")
        logger.info(f"Fetched: {claim_url}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise FileNotFoundError(f"Reel not found on CDN: {identifier}")
        raise

    # 2. Fetch seed.md (required)
    seed_url = f"{base_url}/seed.md"
    try:
        response = httpx.get(seed_url, timeout=30.0)
        response.raise_for_status()
        seed_path = inputs / "seed.md"
        seed_path.write_text(response.text, encoding="utf-8")
        files_fetched.append("seed.md")
        logger.info(f"Fetched: {seed_url}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise FileNotFoundError(
                f"seed.md not found for reel: {identifier}. "
                "This reel may be incomplete."
            )
        raise

    # 3. Fetch chart.json (optional)
    chart_url = f"{base_url}/chart.json"
    try:
        response = httpx.get(chart_url, timeout=30.0)
        response.raise_for_status()
        chart_path = inputs / "chart.json"
        chart_path.write_text(response.text, encoding="utf-8")
        files_fetched.append("chart.json")
        logger.info(f"Fetched: {chart_url}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.debug(f"No chart.json for reel: {identifier}")
        else:
            raise

    logger.info(f"Fetched reel '{identifier}': {', '.join(files_fetched)}")

    return reel_path


def get_reel_url(identifier: str) -> str:
    """Get the CDN URL for a reel folder."""
    return f"{CDN_BASE_URL}/{identifier}/"
