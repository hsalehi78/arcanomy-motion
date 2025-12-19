#!/usr/bin/env python3
"""
Sound Effects Generator CLI for Arcanomy Motion
Uses ElevenLabs Sound Effects API to generate atmospheric audio.

Usage:
    python scripts/generate_sound_effects.py \
        --text "Continuous urban ambience with traffic, rain, footsteps" \
        --output "renders/sfx/clip_01_sfx.mp3"

    # With custom duration
    python scripts/generate_sound_effects.py \
        --text "Heavy rain with thunder" \
        --output "renders/sfx/rain.mp3" \
        --duration 10

    # With custom prompt influence
    python scripts/generate_sound_effects.py \
        --text "Office ambience with keyboard clicks" \
        --output "renders/sfx/office.mp3" \
        --prompt-influence 0.4

    # Dry run (save prompt, don't call API)
    python scripts/generate_sound_effects.py \
        --text "Forest sounds with birds" \
        --output "renders/sfx/forest.mp3" \
        --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import get_audio_sfx_model

# Load environment variables
load_dotenv()


def generate_sound_effect(
    text: str,
    output_path: str,
    duration_seconds: float = 10.0,
    prompt_influence: float = 0.3,
) -> bool:
    """Generate sound effect using ElevenLabs API."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("[ERROR] ELEVENLABS_API_KEY not set", file=sys.stderr)
        return False

    try:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=api_key)
        
        # Get model from config (currently "sound-generation" is the only available model)
        sfx_model = get_audio_sfx_model("elevenlabs")

        print(f"Generating sound effect ({sfx_model})...")
        print(f"   Prompt: {text[:80]}...")
        print(f"   Duration: {duration_seconds}s")
        print(f"   Prompt Influence: {prompt_influence}")

        audio = client.text_to_sound_effects.convert(
            text=text,
            duration_seconds=duration_seconds,
            prompt_influence=prompt_influence,
        )

        # Save audio
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        print(f"[OK] Sound effect saved: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Sound effect generation failed: {e}", file=sys.stderr)
        return False


def dry_run(text: str, output_path: str, duration_seconds: float, prompt_influence: float) -> bool:
    """Save prompt to text file without calling API."""
    try:
        prompt_path = Path(output_path).with_suffix(".prompt.txt")
        prompt_path.parent.mkdir(parents=True, exist_ok=True)

        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(f"# Sound Effect Prompt (Dry Run)\n\n")
            f.write(f"Output: {output_path}\n")
            f.write(f"Duration: {duration_seconds}s\n")
            f.write(f"Prompt Influence: {prompt_influence}\n\n")
            f.write(f"## Prompt:\n{text}\n")

        print(f"[DRY RUN] Prompt saved: {prompt_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Dry run failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Arcanomy Motion Sound Effects Generator - Create atmospheric audio with AI"
    )

    # Required arguments
    parser.add_argument("--text", required=True, help="Sound effect prompt text")
    parser.add_argument("--output", required=True, help="Output audio file path (.mp3)")

    # Optional arguments
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Sound effect duration in seconds (default: 10)"
    )
    parser.add_argument(
        "--prompt-influence",
        type=float,
        default=0.3,
        help="How closely to follow the prompt (0-1, default: 0.3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Save prompt to file without calling API"
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Arcanomy Motion - Sound Effects Generator")
    print(f"{'='*60}")
    print(f"Output:   {args.output}")
    print(f"Duration: {args.duration}s")
    print(f"Influence: {args.prompt_influence}")
    print(f"{'='*60}\n")

    if args.dry_run:
        print(f"Mode: Dry Run (no API call)")
        success = dry_run(
            text=args.text,
            output_path=args.output,
            duration_seconds=args.duration,
            prompt_influence=args.prompt_influence,
        )
    else:
        print(f"Mode: Generate (ElevenLabs Sound Effects)")
        success = generate_sound_effect(
            text=args.text,
            output_path=args.output,
            duration_seconds=args.duration,
            prompt_influence=args.prompt_influence,
        )

    print(f"\n{'='*60}\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

