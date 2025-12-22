"""Blog ingestion service for fetching and parsing Arcanomy blogs."""

import httpx
from dataclasses import dataclass
from typing import Optional

from src.config import get_default_voice_id, SEED_EXTRACTION
from src.services.llm import LLMService
from src.utils.logger import get_logger

logger = get_logger()

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


# =============================================================================
# 3-STEP SEED EXTRACTION PIPELINE
# =============================================================================
# Step 1: Anthropic (opus 4.5) - Creative extraction
# Step 2: OpenAI (gpt-5.2) - Verification against blog
# Step 3: Anthropic (opus 4.5) - Final refinement
# =============================================================================

STEP1_EXTRACT_SYSTEM = """You are an expert at extracting compelling video hooks from blog posts.

Your goal: Find the ONE most powerful insight from this blog that would stop someone scrolling.

## Arcanomy Script Format (MANDATORY)
Every hook must follow this structure:
1. TRUTH: A counter-intuitive or confrontational truth
2. MISTAKE: The common mistake people make  
3. FIX: The simple reframe or solution

## Allowed Formats (pick one)
1. Contrarian truth - Challenge conventional wisdom
2. Math slap - A shocking number that changes everything
3. Checklist - "3 signs you're doing X wrong"
4. Story → lesson - Personal anecdote with universal truth
5. Myth bust - Expose a popular misconception

## Output JSON format:
{
    "format_type": "contrarian_truth|math_slap|checklist|story_lesson|myth_bust",
    "hook": "The attention-grabbing opening (max 15 words)",
    "truth": "The counter-intuitive truth (1 sentence)",
    "mistake": "The common mistake (1 sentence)",
    "fix": "The simple solution/reframe (1 sentence)",
    "core_insight": "The main lesson (max 50 words)",
    "visual_vibe": "Mood, colors, style description",
    "key_stat": "The most powerful statistic from the blog (if any)"
}"""

STEP2_VERIFY_SYSTEM = """You are a fact-checker and compliance officer.

Your job: Verify the extracted content against the original blog and ensure it meets all requirements.

## Verification Checks:
1. ACCURACY: Is the hook/insight actually supported by the blog content?
2. STAT CHECK: If a statistic is claimed, does it appear in the blog?
3. FORMAT: Does it follow truth → mistake → fix structure?
4. LENGTH: Can the script be spoken in under 60 seconds (~150 words)?
5. NO MOTIVATION: Does it avoid vague motivational language?

## Output JSON format:
{
    "accuracy_pass": true/false,
    "accuracy_notes": "What needs correction if failed",
    "stat_verified": true/false/null,
    "stat_source_quote": "Exact quote from blog if stat exists",
    "format_pass": true/false,
    "format_notes": "What's missing from truth→mistake→fix",
    "length_pass": true/false,
    "motivation_free": true/false,
    "overall_pass": true/false,
    "corrections_needed": ["list of specific corrections"]
}"""

STEP3_REFINE_SYSTEM = """You are the final polish editor for Arcanomy video scripts.

Your job: Take the verified extraction and make it PUNCHY, SHARP, and COMPLIANT.

## Rules:
1. Hook must stop the scroll in 3 seconds
2. Must follow: TRUTH → MISTAKE → FIX
3. Use specific numbers, not vague statements
4. Tone: Confident, slightly provocative, NOT preachy
5. Total script must be under 150 words (60 seconds)

## Output the final seed.md content:
Return a markdown document with these exact sections:
- # Hook
- # Core Insight  
- # Visual Vibe
- # Script Structure (with Truth/Mistake/Fix)
- # Key Data

Make it ready for production."""


CHART_GENERATION_SYSTEM = """You are a data visualization expert for short-form video.

Given key data points, generate a chart configuration that will be rendered to MP4.

## Chart Types Available:
- bar: Vertical bar chart (best for comparing 2-5 values)
- number: Animated number counter (for single impressive stats like "$600,000")

## Rules:
1. Pick chart type that best tells the story
2. For bar charts: Use 2-4 data points max (mobile readability)
3. For number counters: Use for single dramatic stats
4. Highlight the "bad" option with red (#FF3B30), "good" with gold (#FFD700)
5. Keep labels SHORT (max 10 chars)

## Output JSON format for BAR CHART:
{
    "chartType": "bar",
    "data": [
        {"label": "Age 25", "value": 1140000, "color": "#FFD700"},
        {"label": "Age 35", "value": 540000, "color": "#FF3B30"}
    ],
    "narrative": "One sentence explaining what this chart proves"
}

## Output JSON format for NUMBER COUNTER:
{
    "chartType": "number",
    "value": 600000,
    "prefix": "$",
    "suffix": "",
    "title_text": "Cost of Waiting",
    "subtitle_text": "10 years of delay",
    "narrative": "Waiting cost her $600,000"
}

Return ONLY valid JSON."""


def extract_seed_pipeline(
    mdx_content: str,
    blog: BlogPost,
    focus: Optional[str] = None,
    log_fn=None,
) -> tuple[str, dict, Optional[dict]]:
    """3-step LLM pipeline for seed extraction.
    
    Pipeline:
    1. Anthropic (opus 4.5): Creative extraction
    2. OpenAI (gpt-5.2): Verification
    3. Anthropic (opus 4.5): Final refinement
    4. (Bonus) Generate chart.json if format is math_slap
    
    Args:
        mdx_content: Raw blog MDX content
        blog: BlogPost metadata
        focus: Optional creative direction
        log_fn: Optional logging function
        
    Returns:
        Tuple of (seed_markdown, config_dict, chart_json_or_none)
    """
    def log(msg: str):
        if log_fn:
            log_fn(msg)
        logger.info(msg)
    
    # Get providers from config
    extractor_provider = SEED_EXTRACTION.get("extractor", "anthropic")
    verifier_provider = SEED_EXTRACTION.get("verifier", "openai")
    refiner_provider = SEED_EXTRACTION.get("refiner", "anthropic")
    
    # Truncate content for token limits
    blog_excerpt = mdx_content[:8000]
    
    focus_instruction = ""
    if focus:
        focus_instruction = f"\n\nCREATIVE DIRECTION: {focus}\n"
    
    # =========================================================================
    # STEP 1: Creative Extraction (Anthropic)
    # =========================================================================
    log(f"[Step 1/3] Extracting with {extractor_provider}...")
    
    extractor = LLMService(provider=extractor_provider)
    
    step1_prompt = f"""Extract the most compelling video hook from this blog.

BLOG TITLE: {blog.title}
BLOG CATEGORY: {blog.category}
{focus_instruction}
BLOG CONTENT:
{blog_excerpt}

Remember: Follow truth → mistake → fix structure. Pick one of the 5 allowed formats."""

    extraction = extractor.complete_json(step1_prompt, system=STEP1_EXTRACT_SYSTEM, stage="research")
    
    log(f"   → Format: {extraction.get('format_type', 'unknown')}")
    log(f"   → Hook: {extraction.get('hook', '')[:50]}...")
    
    # =========================================================================
    # STEP 2: Verification (OpenAI)
    # =========================================================================
    log(f"[Step 2/3] Verifying with {verifier_provider}...")
    
    verifier = LLMService(provider=verifier_provider)
    
    step2_prompt = f"""Verify this extracted content against the original blog.

EXTRACTED CONTENT:
{extraction}

ORIGINAL BLOG CONTENT:
{blog_excerpt}

Check accuracy, verify any statistics, and ensure compliance with truth→mistake→fix format."""

    verification = verifier.complete_json(step2_prompt, system=STEP2_VERIFY_SYSTEM, stage="research")
    
    overall_pass = verification.get("overall_pass", False)
    corrections = verification.get("corrections_needed", [])
    
    log(f"   → Verification: {'PASS' if overall_pass else 'NEEDS CORRECTIONS'}")
    if corrections:
        for c in corrections[:3]:
            log(f"   → Correction: {c[:60]}...")
    
    # =========================================================================
    # STEP 3: Final Refinement (Anthropic)
    # =========================================================================
    log(f"[Step 3/3] Refining with {refiner_provider}...")
    
    refiner = LLMService(provider=refiner_provider)
    
    corrections_text = ""
    if corrections:
        corrections_text = f"\n\nCORRECTIONS TO APPLY:\n" + "\n".join(f"- {c}" for c in corrections)
    
    step3_prompt = f"""Create the final polished seed.md for this video.

EXTRACTED CONTENT:
Hook: {extraction.get('hook', '')}
Format: {extraction.get('format_type', '')}
Truth: {extraction.get('truth', '')}
Mistake: {extraction.get('mistake', '')}
Fix: {extraction.get('fix', '')}
Core Insight: {extraction.get('core_insight', '')}
Visual Vibe: {extraction.get('visual_vibe', '')}
Key Stat: {extraction.get('key_stat', 'None')}

VERIFICATION RESULT:
Stat Source: {verification.get('stat_source_quote', 'Not verified')}
{corrections_text}

BLOG TITLE: {blog.title}
SOURCE: {blog.identifier}

Generate the final seed.md content. Make it punchy and production-ready."""

    final_seed = refiner.complete(step3_prompt, system=STEP3_REFINE_SYSTEM, stage="script")
    
    # Build config
    format_type = extraction.get("format_type", "story_lesson")
    config = {
        "title": blog.title,
        "type": _format_to_reel_type(format_type),
        "duration_blocks": 5,  # Default 50s
        "voice_id": get_default_voice_id("elevenlabs"),
        "music_mood": "contemplative",
        "aspect_ratio": "9:16",
        "subtitles": "burned_in",
        "audit_level": "basic",
        "source_blog": blog.identifier,
        "extraction_format": format_type,
        "verification_passed": overall_pass,
    }
    
    # =========================================================================
    # STEP 4: Generate chart.json if format is math_slap (data-driven)
    # =========================================================================
    chart_json = None
    if format_type == "math_slap" and extraction.get("key_stat"):
        log("[Step 4/4] Generating chart.json...")
        
        # Extract key data from seed (parse the # Key Data section)
        key_data = extraction.get("key_stat", "")
        hook = extraction.get("hook", "")
        
        chart_json = generate_chart_json(key_data, hook, refiner)
        
        if chart_json:
            log(f"   → Chart type: {chart_json.get('chartType', 'unknown')}")
            log(f"   → Data points: {len(chart_json.get('data', []))}")
        else:
            log("   → No chart generated (data not suitable)")
    
    log(f"[Done] Seed extracted and refined")
    
    return final_seed, config, chart_json


def _format_to_reel_type(format_type: str) -> str:
    """Map extraction format to reel type."""
    mapping = {
        "contrarian_truth": "text_cinematic",
        "math_slap": "chart_explainer",
        "checklist": "text_cinematic",
        "story_lesson": "story_essay",
        "myth_bust": "text_cinematic",
    }
    return mapping.get(format_type, "story_essay")


def generate_chart_json(
    key_data: str,
    hook: str,
    llm: LLMService,
) -> Optional[dict]:
    """Generate chart.json directly from extracted key data.
    
    Args:
        key_data: The Key Data section from seed.md
        hook: The hook for context
        llm: LLM service instance
        
    Returns:
        Chart configuration dict ready for rendering, or None if no chart needed
    """
    prompt = f"""Generate a chart configuration for this data.

HOOK: {hook}

KEY DATA:
{key_data}

Pick the best chart type to visualize this comparison. Make it punchy and mobile-friendly."""

    try:
        chart_spec = llm.complete_json(prompt, system=CHART_GENERATION_SYSTEM, stage="plan")
        
        if not chart_spec or "chartType" not in chart_spec:
            return None
            
        # Build full chart config from template
        return _build_chart_config(chart_spec)
    except Exception as e:
        logger.warning(f"Chart generation failed: {e}")
        return None


def _build_chart_config(spec: dict) -> dict:
    """Build a complete Remotion-ready chart.json from a minimal spec."""
    chart_type = spec.get("chartType", "bar")
    
    if chart_type == "number":
        # Number counter config (from number-counter-basic.json template)
        return {
            "chartType": "number",
            "value": spec.get("value", 0),
            "startValue": 0,
            "prefix": spec.get("prefix", ""),
            "suffix": spec.get("suffix", ""),
            "decimals": 0,
            "useLocale": True,
            "dimensions": {
                "width": 1080,
                "height": 1080
            },
            "background": {
                "color": "#00FF00"  # Green screen for CapCut chroma key
            },
            "title": {
                "show": True,
                "text": spec.get("title_text", ""),
                "position": "above",
                "font": {
                    "family": "Inter, sans-serif",
                    "size": 48,
                    "weight": 500
                },
                "color": "#FFFFFF"
            },
            "subtitle": {
                "show": bool(spec.get("subtitle_text")),
                "text": spec.get("subtitle_text", ""),
                "font": {
                    "family": "Inter, sans-serif",
                    "size": 36,
                    "weight": 400
                },
                "color": "#888888"
            },
            "number": {
                "font": {
                    "family": "Montserrat, sans-serif",
                    "size": 160,
                    "weight": 700
                },
                "color": "#FF3B30"  # Red for dramatic "cost" numbers
            },
            "animation": {
                "duration": 60,
                "easing": "ease-out",
                "delay": 15
            },
            "_narrative": spec.get("narrative", ""),
        }
    
    # Bar chart config (from bar-chart-comparison.json template)
    return {
        "chartType": "bar",
        "dimensions": {
            "width": 1080,
            "height": 1080,
            "margin": {"top": 200, "right": 60, "bottom": 140, "left": 100}
        },
        "background": {
            "color": "#00FF00"  # Green screen for CapCut chroma key
        },
        "title": {
            "show": False,
            "text": "",
            "y": 60,
            "font": {
                "family": "Montserrat",
                "size": 64,
                "weight": 700
            },
            "color": "#FFFFFF"
        },
        "subtitle": {
            "show": False,
            "text": "",
            "y": 130,
            "font": {
                "family": "Inter",
                "size": 42,
                "weight": 400
            },
            "color": "#888888"
        },
        "xAxis": {
            "show": True,
            "label": {
                "font": {
                    "family": "Inter",
                    "size": 42,
                    "weight": 500
                },
                "color": "#FFFFFF"
            }
        },
        "yAxis": {
            "show": False,
            "label": {
                "font": {
                    "family": "Inter",
                    "size": 36,
                    "weight": 400
                },
                "color": "#666666"
            },
            "gridLines": {
                "show": True,
                "color": "#333333"
            }
        },
        "bars": {
            "gap": 20,
            "cornerRadius": 8,
            "defaultColor": "#FFD700"
        },
        "dataLabels": {
            "show": True,
            "position": "above",
            "font": {
                "family": "Montserrat",
                "size": 48,
                "weight": 700
            },
            "color": "#FFFFFF"
        },
        "animation": {
            "duration": 30,
            "style": "wave",
            "velocityMode": True,
            "staggerDelay": 10,
            "direction": "left-to-right"
        },
        "data": spec.get("data", []),
        "_narrative": spec.get("narrative", ""),
    }


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

    # Build CSV content from verified data points
    csv_content = None
    if extract_data and 'verified_points' in dir() and verified_points:
        csv_lines = ["label,value,source_quote"]
        for dp in verified_points:
            label = dp.get("label", "").replace(",", ";").replace('"', "'")
            value = dp.get("value", "").replace(",", ";").replace('"', "'")
            quote = dp.get("source_quote", "")[:80].replace(",", ";").replace('"', "'").replace("\n", " ")
            csv_lines.append(f'"{label}","{value}","{quote}"')
        csv_content = "\n".join(csv_lines)

    return seed_content, csv_content

