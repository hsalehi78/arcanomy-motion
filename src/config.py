"""Centralized configuration for Arcanomy Motion.

Edit the dictionaries below to switch models across the pipeline.
"""

import os
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
        "default": "gemini-3-pro-preview",     # Latest Gemini 3 Pro
        # Other options:
        # "default": "gemini-2.5-pro-preview", # Gemini 2.5 Pro
        # "default": "gemini-2.0-flash",       # Fast
    },
}

# OpenAI API parameter selection: newer model families use `max_completion_tokens`
OPENAI_MAX_COMPLETION_TOKENS_MODEL_PREFIXES: tuple[str, ...] = ("gpt-5", "o3", "o1")


# =============================================================================
# LLM API KEYS (centralize env var names here; no hard-coding elsewhere)
# =============================================================================

LLM_API_KEY_ENV_VARS: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    # Support both names to avoid confusion across docs/scripts
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
}


# =============================================================================
# MEDIA GENERATION API KEYS (for image, video, audio generation)
# =============================================================================

MEDIA_API_KEY_ENV_VARS: dict[str, tuple[str, ...]] = {
    "kie": ("KIE_API_KEY",),
    "elevenlabs": ("ELEVENLABS_API_KEY",),
}


def get_llm_api_key(provider: str) -> str:
    """Return the API key for an LLM provider from the environment.

    Raises:
        ValueError: unknown provider
        RuntimeError: key missing
    """
    env_names = LLM_API_KEY_ENV_VARS.get(provider)
    if not env_names:
        raise ValueError(f"Unknown LLM provider for API key lookup: {provider}")

    for env_name in env_names:
        value = os.getenv(env_name)
        if value:
            return value

    raise RuntimeError(
        f"Missing API key for provider '{provider}'. Set one of: {', '.join(env_names)}"
    )


def get_media_api_key(provider: str) -> str:
    """Return the API key for a media generation provider from the environment.

    Raises:
        ValueError: unknown provider
        RuntimeError: key missing
    """
    env_names = MEDIA_API_KEY_ENV_VARS.get(provider)
    if not env_names:
        raise ValueError(f"Unknown media provider for API key lookup: {provider}")

    for env_name in env_names:
        value = os.getenv(env_name)
        if value:
            return value

    raise RuntimeError(
        f"Missing API key for provider '{provider}'. Set one of: {', '.join(env_names)}"
    )


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
        "default": "gemini-3-pro-image-preview",  # Gemini 3 Pro Image Preview (native image gen)
        # Other: "gemini-2.0-flash-exp-image-generation", "imagen-3"
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
        "default_voice_id": "21m00Tcm4TlvDq8ikWAM",  # "Rachel" - professional narrator voice
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
    "videos": "veo",            # → veo-3-1
    
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
# DATA EXTRACTION & VERIFICATION (for --data flag on blog reels)
# =============================================================================
# When extracting data points from blogs, use two different LLMs:
# 1. Extractor: Pulls data points from the blog
# 2. Verifier: Checks each data point against the original blog text
# Only data points that pass verification are included.

DATA_EXTRACTION = {
    "extractor": "openai",      # Primary LLM that extracts data points
    "verifier": "gemini",       # Secondary LLM that verifies claims (different from extractor)
    "require_verification": True,  # If False, skip verification step
}


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

    raise ValueError(
        f"Unknown LLM provider: {provider}. Expected one of: {', '.join(sorted(MODELS.keys()))}"
    )


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
    if provider not in IMAGE_MODELS:
        raise ValueError(
            f"Unknown image provider: {provider}. Expected one of: {', '.join(sorted(IMAGE_MODELS.keys()))}"
        )
    return IMAGE_MODELS[provider]["default"]


def get_video_model(provider: str) -> str:
    """Get video generation model for a provider."""
    if provider not in VIDEO_MODELS:
        raise ValueError(
            f"Unknown video provider: {provider}. Expected one of: {', '.join(sorted(VIDEO_MODELS.keys()))}"
        )
    return VIDEO_MODELS[provider]["default"]


def get_audio_voice_model(provider: str = "elevenlabs") -> str:
    """Get audio (TTS) model ID for a provider."""
    if provider not in AUDIO_MODELS or "voice_model" not in AUDIO_MODELS[provider]:
        raise ValueError(
            f"Unknown/unsupported audio provider for voice model: {provider}. "
            f"Expected one of: {', '.join(sorted(AUDIO_MODELS.keys()))}"
        )
    return AUDIO_MODELS[provider]["voice_model"]


def get_audio_sfx_model(provider: str = "elevenlabs") -> str:
    """Get audio (SFX) model ID for a provider."""
    if provider not in AUDIO_MODELS or "sfx_model" not in AUDIO_MODELS[provider]:
        raise ValueError(
            f"Unknown/unsupported audio provider for sfx model: {provider}. "
            f"Expected one of: {', '.join(sorted(AUDIO_MODELS.keys()))}"
        )
    return AUDIO_MODELS[provider]["sfx_model"]


def get_default_voice_id(provider: str = "elevenlabs") -> str:
    """Get default voice ID for a provider."""
    if provider not in AUDIO_MODELS or "default_voice_id" not in AUDIO_MODELS[provider]:
        raise ValueError(
            f"Unknown/unsupported audio provider for voice id: {provider}. "
            f"Expected one of: {', '.join(sorted(AUDIO_MODELS.keys()))}"
        )
    return AUDIO_MODELS[provider]["default_voice_id"]


def get_default_provider(stage: str) -> str:
    """Get the default provider for a stage."""
    return DEFAULT_PROVIDERS.get(stage, "openai")

