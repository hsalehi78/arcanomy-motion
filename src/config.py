"""Centralized configuration for Arcanomy Motion.

Edit the dictionaries below to switch models across the pipeline.
"""

from dataclasses import dataclass
from typing import Optional


# =============================================================================
# LLM MODELS (for text generation: research, script, plan, voice, sfx)
# =============================================================================

MODELS = {
    "openai": {
        "default": "gpt-5.2",                 # Best model for coding and agentic tasks
        # Other options:
        # "default": "o3",                    # Best reasoning/thinking
        # "default": "o1",                    # Previous best reasoning
        # "default": "gpt-4o",                # Fast, high quality
        # "default": "gpt-4o-mini",           # Faster, cheaper
    },
    "anthropic": {
        "default": "claude-opus-4-5-20251101",  # Best Anthropic model (Opus 4.5)
        # Other options:
        # "default": "claude-sonnet-4-5-20251101",  # Sonnet 4.5
        # "default": "claude-opus-4-20250514",      # Opus 4
        # "default": "claude-sonnet-4-20250514",    # Sonnet 4
    },
    "gemini": {
        "default": "gemini-3-pro",            # Best Gemini model
        # Other options:
        # "default": "gemini-2.5-pro",        # Previous best
        # "default": "gemini-2.0-pro",        # Stable
        # "default": "gemini-1.5-flash",      # Faster, cheaper
    },
}


# =============================================================================
# IMAGE GENERATION MODELS (for assets stage)
# =============================================================================

IMAGE_MODELS = {
    "kie": {
        "default": "nano-banana-pro",         # Kie.ai best image gen
    },
    "openai": {
        "default": "gpt-image-1.5",           # GPT Image 1.5 (highest performance)
        # Other: "dall-e-3"
    },
    "gemini": {
        "default": "imagen-3",                # Google Imagen 3
    },
}


# =============================================================================
# VIDEO GENERATION MODELS (for videos stage)
# =============================================================================

VIDEO_MODELS = {
    "veo": {
        "default": "veo-3-1",                 # Google Veo 3.1 (best quality, 1080p, audio)
    },
    "kling": {
        "default": "kling/v2-5-turbo-image-to-video-pro",  # Kling 2.5 turbo (fast, 1080p)
    }
}


# =============================================================================
# AUDIO MODELS (for voice/sfx generation)
# =============================================================================

AUDIO_MODELS = {
    "elevenlabs": {
        "voice_model": "eleven_v3",                # ElevenLabs v3 (most expressive)
        "sfx_model": "sound-generation",           # ElevenLabs Sound Effects
       
    },
}


# =============================================================================
# DEFAULT PROVIDERS (what's used when you don't pass -p flag)
# =============================================================================

DEFAULT_PROVIDERS = {
    # LLM stages (text generation - these write prompts, not media)
    "research": "openai",       # → gpt-5.2
    "script": "anthropic",      # → claude-opus-4.5
    "plan": "anthropic",        # → claude-opus-4.5
    "vidprompt": "anthropic",   # → claude-opus-4.5
    "voice": "anthropic",       # → claude-opus-4.5  (writes narration TEXT)
    "sfx": "anthropic",         # → claude-opus-4.5  (writes SFX prompts)
    
    # Image generation
    "assets": "kie",            # → nano-banana-pro
    
    # Video generation
    "videos": "kling",          # → kling/v2-5-turbo-image-to-video-pro
    
    # Audio generation
    "audio": "elevenlabs",      # → eleven_v3
    "sfxgen": "elevenlabs",     # → sound-generation
}


# =============================================================================
# CURRENT DEFAULTS (what runs when you just type the command)
# =============================================================================
#
#   COMMAND              DOES WHAT                    PROVIDER      MODEL
#   ─────────────────────────────────────────────────────────────────────────────
#   uv run research   →  researches topic          →  openai     →  gpt-5.2
#   uv run script     →  writes script             →  anthropic  →  claude-opus-4.5
#   uv run plan       →  plans visuals             →  anthropic  →  claude-opus-4.5
#   uv run vidprompt  →  writes video prompts      →  anthropic  →  claude-opus-4.5
#   uv run voice      →  writes narration TEXT     →  anthropic  →  claude-opus-4.5
#   uv run sfx        →  writes SFX prompts        →  anthropic  →  claude-opus-4.5
#   uv run assets     →  generates IMAGES          →  kie        →  nano-banana-pro
#   uv run videos     →  generates VIDEOS          →  kling      →  kling/v2-5-turbo
#   uv run audio      →  generates VOICE AUDIO     →  elevenlabs →  eleven_v3
#   uv run sfxgen     →  generates SFX AUDIO       →  elevenlabs →  sound-generation
#


# =============================================================================
# STAGE-SPECIFIC OVERRIDES (Optional)
# =============================================================================
# If you want different stages to use different models, define them here.
# Leave as None to use the provider default.
# 
# Example:
#   STAGE_MODELS = {
#       "research": "gpt-4o-mini",      # Use cheaper model for research
#       "script": "claude-3-opus",      # Use best model for creative writing
#   }

STAGE_MODELS: dict[str, Optional[str]] = {
    # "research": None,
    # "script": None,
    # "plan": None,
    # "vidprompt": None,
    # "voice": None,
    # "sfx": None,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_model(provider: str, stage: Optional[str] = None) -> str:
    """Get LLM model for text generation stages.
    
    Args:
        provider: LLM provider name (openai, anthropic, gemini)
        stage: Optional stage name for stage-specific overrides
        
    Returns:
        Model name string
    """
    # Check for stage-specific override first
    if stage and stage in STAGE_MODELS and STAGE_MODELS[stage]:
        return STAGE_MODELS[stage]
    
    # Fall back to provider default
    if provider in MODELS:
        return MODELS[provider]["default"]
    
    # Fallback defaults if provider not configured
    fallbacks = {
        "openai": "gpt-5.2",
        "anthropic": "claude-opus-4-5-20251101",
        "gemini": "gemini-3-pro",
    }
    return fallbacks.get(provider, "gpt-4o")


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    provider: str
    temperature: float = 0.7
    max_tokens: int = 4096


def get_model_config(provider: str, stage: Optional[str] = None) -> ModelConfig:
    """Get full model configuration for a provider/stage."""
    model_name = get_model(provider, stage)
    return ModelConfig(
        name=model_name,
        provider=provider,
    )


def get_image_model(provider: str) -> str:
    """Get image generation model for a provider."""
    if provider in IMAGE_MODELS:
        return IMAGE_MODELS[provider]["default"]
    return IMAGE_MODELS.get("kie", {}).get("default", "nano-banana-pro")


def get_video_model(provider: str) -> str:
    """Get video generation model for a provider."""
    if provider in VIDEO_MODELS:
        return VIDEO_MODELS[provider]["default"]
    return VIDEO_MODELS.get("kling", {}).get("default", "kling/v2-5-turbo-image-to-video-pro")


def get_default_provider(stage: str) -> str:
    """Get the default provider for a stage."""
    return DEFAULT_PROVIDERS.get(stage, "openai")

