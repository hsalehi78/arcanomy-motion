"""Blog ingestion service for fetching and parsing Arcanomy blogs."""

import httpx
from dataclasses import dataclass
from typing import Optional

from src.config import get_default_voice_id
from src.services.llm import LLMService

CDN_BASE_URL = "https://cdn.arcanomydata.com/content/posts"
FEATURED_INDEX_URL = f"{CDN_BASE_URL}/_indexes/featured.json"


@dataclass
class BlogPost:
    """Represents a blog post from the featured index."""

    identifier: str
    slug: str
    title: str
    description: str
    section: str
    category: str
    published_date: str
    reading_time: int
    tags: list[str]
    is_featured: bool
    image: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "BlogPost":
        """Create a BlogPost from a dictionary."""
        return cls(
            identifier=data["identifier"],
            slug=data["slug"],
            title=data["title"],
            description=data.get("description", ""),
            section=data.get("section", ""),
            category=data.get("category", ""),
            published_date=data.get("published_date", ""),
            reading_time=data.get("reading_time", 0),
            tags=data.get("tags", []),
            is_featured=data.get("is_featured", False),
            image=data.get("image"),
        )


def fetch_featured_blogs(limit: Optional[int] = None) -> list[BlogPost]:
    """Fetch the list of featured blogs from the CDN.

    Args:
        limit: Maximum number of blogs to return (most recent first)

    Returns:
        List of BlogPost objects sorted by published_date descending
    """
    response = httpx.get(FEATURED_INDEX_URL, timeout=30.0)
    response.raise_for_status()
    data = response.json()

    posts = [BlogPost.from_dict(p) for p in data.get("posts", [])]

    # Sort by published_date descending
    posts.sort(key=lambda p: p.published_date, reverse=True)

    if limit:
        posts = posts[:limit]

    return posts


def fetch_blog_mdx(identifier: str) -> str:
    """Fetch the raw MDX content for a blog post.

    Args:
        identifier: The blog identifier (e.g., "2025-08-10-knowledge-the-psychology-of-money")

    Returns:
        The raw MDX content as a string
    """
    url = f"{CDN_BASE_URL}/{identifier}/content.mdx"
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    return response.text


def extract_seed_and_config(
    mdx_content: str,
    blog: BlogPost,
    llm: LLMService,
) -> tuple[str, dict]:
    """Use LLM to extract seed.md content and reel.yaml config from blog MDX.

    Args:
        mdx_content: The raw MDX content
        blog: The BlogPost metadata
        llm: LLM service instance

    Returns:
        Tuple of (seed_markdown, config_dict)
    """
    system_prompt = """You are an expert at converting blog posts into short-form video briefs.

Given a blog post, extract:
1. A compelling hook (the attention-grabbing opening line for the video)
2. The core insight (the single main lesson or takeaway)
3. A visual vibe description (mood, colors, style for the video)

Respond with valid JSON in this exact format:
{
    "hook": "The attention-grabbing opening line",
    "core_insight": "The main lesson or data point being conveyed",
    "visual_vibe": "Description of mood, colors, and visual style",
    "reel_type": "chart_explainer|text_cinematic|story_essay",
    "duration_blocks": 2,
    "music_mood": "keyword for music mood"
}

Guidelines:
- Hook should be punchy, confrontational, or intriguing (max 15 words)
- Core insight should be a single, clear statement (max 50 words)
- Visual vibe should describe mood/colors (e.g., "Dark, moody, cinematic. Gold accents on black.")
- Choose reel_type based on content:
  - chart_explainer: if data/numbers are central
  - text_cinematic: if it's a powerful statement/quote
  - story_essay: if it's a narrative/psychological insight
- duration_blocks: 2 for most content, 3 for complex topics, 1 for simple statements
- music_mood: e.g., "tense_resolution", "contemplative", "uplifting", "dramatic"
"""

    user_prompt = f"""Convert this blog post into a video brief.

BLOG TITLE: {blog.title}
BLOG CATEGORY: {blog.category}
BLOG SECTION: {blog.section}

BLOG CONTENT:
{mdx_content[:8000]}  # Truncate to avoid token limits
"""

    result = llm.complete_json(user_prompt, system=system_prompt)

    # Build seed.md content
    seed_content = f"""# Hook
{result.get('hook', blog.title)}

# Core Insight
{result.get('core_insight', blog.description)}

# Visual Vibe
{result.get('visual_vibe', 'Dark, moody, cinematic. Gold accents on black.')}

# Data Sources
- (none - sourced from blog: {blog.identifier})
"""

    # Build reel.yaml config
    config = {
        "title": blog.title,
        "type": result.get("reel_type", "story_essay"),
        "duration_blocks": result.get("duration_blocks", 2),
        "voice_id": get_default_voice_id("elevenlabs"),
        "music_mood": result.get("music_mood", "contemplative"),
        "aspect_ratio": "9:16",
        "subtitles": "burned_in",
        "audit_level": "loose",  # Blogs don't have CSV data
        "source_blog": blog.identifier,
    }

    return seed_content, config

