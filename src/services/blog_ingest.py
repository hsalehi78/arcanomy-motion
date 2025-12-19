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
    focus: Optional[str] = None,
    extract_data: bool = False,
) -> tuple[str, dict]:
    """Use LLM to extract seed.md content and reel.yaml config from blog MDX.

    Args:
        mdx_content: The raw MDX content
        blog: The BlogPost metadata
        llm: LLM service instance
        focus: Optional focus prompt to guide extraction (e.g., "focus on money psychology")
        extract_data: If True, extract specific data points/statistics from the blog

    Returns:
        Tuple of (seed_markdown, config_dict)
    """
    # Build data extraction instruction if requested
    data_instruction = ""
    data_json_field = ""
    if extract_data:
        data_instruction = """4. Key data points (specific numbers, statistics, or facts from the blog that should be visualized)
"""
        data_json_field = """    "data_points": [
        {"label": "Description of data point", "value": "The specific number or statistic"},
        ...
    ],
"""

    # Build focus instruction if provided
    focus_instruction = ""
    if focus:
        focus_instruction = f"""
CREATIVE DIRECTION:
{focus}
(Use this to guide what angle/aspect to emphasize in the hook and core insight)
"""

    system_prompt = f"""You are an expert at converting blog posts into short-form video briefs.

Given a blog post, extract:
1. A compelling hook (the attention-grabbing opening line for the video)
2. The core insight (the single main lesson or takeaway)
3. A visual vibe description (mood, colors, style for the video)
{data_instruction}
Respond with valid JSON in this exact format:
{{
    "hook": "The attention-grabbing opening line",
    "core_insight": "The main lesson or data point being conveyed",
    "visual_vibe": "Description of mood, colors, and visual style",
{data_json_field}    "reel_type": "chart_explainer|text_cinematic|story_essay",
    "duration_blocks": 2,
    "music_mood": "keyword for music mood"
}}

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
{focus_instruction}
BLOG CONTENT:
{mdx_content[:8000]}  # Truncate to avoid token limits
"""

    result = llm.complete_json(user_prompt, system=system_prompt, stage="research")

    # Build data sources section
    data_sources = f"- (sourced from blog: {blog.identifier})"
    if extract_data and result.get("data_points"):
        data_lines = [data_sources]
        for dp in result.get("data_points", []):
            data_lines.append(f"- {dp.get('label', 'Data')}: {dp.get('value', 'N/A')}")
        data_sources = "\n".join(data_lines)

    # Build seed.md content
    seed_content = f"""# Hook
{result.get('hook', blog.title)}

# Core Insight
{result.get('core_insight', blog.description)}

# Visual Vibe
{result.get('visual_vibe', 'Dark, moody, cinematic. Gold accents on black.')}

# Data Sources
{data_sources}
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


def _verify_data_points(
    data_points: list[dict],
    hook: str,
    core_insight: str,
    mdx_content: str,
    verifier_llm: LLMService,
) -> list[dict]:
    """Verify extracted data points using a second LLM.
    
    Checks each data point for:
    1. Accuracy - Is this data actually present in the blog?
    2. Relevance - Does this data support the hook/core insight?
    
    Returns only verified data points.
    """
    if not data_points:
        return []
    
    system_prompt = """You are a fact-checker verifying data claims against source material.

For each data point, you must verify:
1. ACCURACY: Is this exact number/statistic present in the blog text?
2. RELEVANCE: Does this data point directly support the hook or core insight?

A data point passes verification ONLY if:
- The number/value appears verbatim (or very close) in the blog
- It directly relates to the main message

Respond with valid JSON:
{
    "verified": [
        {"label": "...", "value": "...", "context": "...", "source_quote": "exact quote from blog"},
        ...
    ],
    "rejected": [
        {"label": "...", "value": "...", "reason": "why it failed"},
        ...
    ]
}
"""
    
    # Format data points for verification
    data_points_text = "\n".join([
        f"- {dp.get('label', 'Data')}: {dp.get('value', 'N/A')} ({dp.get('context', '')})"
        for dp in data_points
    ])
    
    user_prompt = f"""Verify these extracted data points.

HOOK: {hook}
CORE INSIGHT: {core_insight}

DATA POINTS TO VERIFY:
{data_points_text}

ORIGINAL BLOG CONTENT:
{mdx_content[:6000]}

For each data point, check if it appears in the blog AND supports the hook/insight.
"""
    
    result = verifier_llm.complete_json(user_prompt, system=system_prompt, stage="research")
    
    return result.get("verified", [])


def regenerate_seed(
    mdx_content: str,
    blog_identifier: str,
    blog_title: str,
    llm: LLMService,
    focus: Optional[str] = None,
    extract_data: bool = False,
    log_fn=None,
) -> str:
    """Regenerate just the seed.md content (without config) for an existing reel.

    Args:
        mdx_content: The raw MDX content
        blog_identifier: The blog identifier
        blog_title: The blog title
        llm: LLM service instance
        focus: Optional focus prompt to guide extraction
        extract_data: If True, extract specific data points from the blog
        log_fn: Optional logging function (e.g., typer.echo)

    Returns:
        The seed markdown content
    """
    from src.config import DATA_EXTRACTION, get_model
    
    def log(msg: str):
        if log_fn:
            log_fn(msg)
    
    # Build data extraction instruction if requested
    data_instruction = ""
    data_json_field = ""
    if extract_data:
        data_instruction = """4. Key data points (specific numbers, statistics, percentages from the blog that support your hook/insight)
"""
        data_json_field = """    "data_points": [
        {"label": "Description", "value": "The exact number/stat from the blog", "context": "How it supports the hook"},
        ...
    ],
"""

    # Build focus instruction if provided
    focus_instruction = ""
    if focus:
        focus_instruction = f"""
CREATIVE DIRECTION:
{focus}
(Use this to guide what angle/aspect to emphasize. Be bold and specific based on this direction.)
"""

    system_prompt = f"""You are an expert at converting blog posts into punchy short-form video briefs.

Given a blog post, extract:
1. A compelling hook (the attention-grabbing opening line for the video)
2. The core insight (the single main lesson or takeaway)
3. A visual vibe description (mood, colors, style for the video)
{data_instruction}
Respond with valid JSON in this exact format:
{{
    "hook": "The attention-grabbing opening line",
    "core_insight": "The main lesson or data point being conveyed",
    "visual_vibe": "Description of mood, colors, and visual style"{"," if extract_data else ""}
{data_json_field}}}

Guidelines:
- Hook should be punchy, confrontational, or intriguing (max 15 words)
- Core insight should be a single, clear statement (max 50 words)  
- Visual vibe should describe mood/colors (e.g., "Dark, moody, cinematic. Gold accents on black.")
{"- Data points MUST be exact numbers from the blog that directly support your hook/insight" if extract_data else ""}
{"- Only include data that appears verbatim in the blog - no calculations or inferences" if extract_data else ""}
"""

    user_prompt = f"""Convert this blog post into a video brief.

BLOG TITLE: {blog_title}
{focus_instruction}
BLOG CONTENT:
{mdx_content[:8000]}
"""

    # Log extraction LLM call
    extractor_model = get_model(llm.provider)
    log(f"[LLM] Extraction: {llm.provider} ({extractor_model})")
    
    result = llm.complete_json(user_prompt, system=system_prompt, stage="research")
    
    hook = result.get('hook', blog_title)
    core_insight = result.get('core_insight', '')
    
    log(f"   -> Hook: {hook[:50]}...")
    log(f"   -> Insight: {core_insight[:50]}...")

    # Build data sources section
    data_sources = f"- (sourced from blog: {blog_identifier})"
    
    if extract_data and result.get("data_points"):
        extracted_points = result.get("data_points", [])
        log(f"   -> Extracted {len(extracted_points)} data points")
        
        # Verify data points with second LLM if configured
        if DATA_EXTRACTION.get("require_verification", True):
            verifier_provider = DATA_EXTRACTION.get("verifier", "gemini")
            verifier_model = get_model(verifier_provider)
            log(f"[LLM] Verification: {verifier_provider} ({verifier_model})")
            
            verifier_llm = LLMService(provider=verifier_provider)
            
            verified_points = _verify_data_points(
                data_points=extracted_points,
                hook=hook,
                core_insight=core_insight,
                mdx_content=mdx_content,
                verifier_llm=verifier_llm,
            )
            log(f"   -> Verified: {len(verified_points)}/{len(extracted_points)} passed")
        else:
            log(f"   -> Verification skipped (require_verification=False)")
            verified_points = extracted_points
        
        if verified_points:
            data_lines = [data_sources]
            for dp in verified_points:
                label = dp.get("label", "Data")
                value = dp.get("value", "N/A")
                context = dp.get("context", "")
                source_quote = dp.get("source_quote", "")
                
                if source_quote:
                    data_lines.append(f"- {label}: {value}")
                    data_lines.append(f"  > \"{source_quote[:100]}...\"")
                elif context:
                    data_lines.append(f"- {label}: {value} ({context})")
                else:
                    data_lines.append(f"- {label}: {value}")
            data_sources = "\n".join(data_lines)

    # Build seed.md content
    seed_content = f"""# Hook
{hook}

# Core Insight
{core_insight}

# Visual Vibe
{result.get('visual_vibe', 'Dark, moody, cinematic. Gold accents on black.')}

# Data Sources
{data_sources}
"""

    return seed_content

