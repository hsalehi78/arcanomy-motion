"""ElevenLabs voice synthesis service."""

import os
from pathlib import Path
from typing import Optional


class ElevenLabsService:
    """Wrapper for ElevenLabs Text-to-Speech API."""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self._client = None

    def _get_client(self):
        """Lazy-load the ElevenLabs client."""
        if self._client is not None:
            return self._client

        from elevenlabs import ElevenLabs

        self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def generate_speech(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.40,
        similarity_boost: float = 0.75,
        style: float = 0.12,
    ) -> Path:
        """Generate speech audio from text.

        Args:
            text: The text to synthesize
            voice_id: ElevenLabs voice ID
            output_path: Where to save the audio file
            model_id: ElevenLabs model to use
            stability: Voice stability (0-1). Lower = more natural variation. Documentary style: 0.35-0.45
            similarity_boost: Voice similarity boost (0-1). Documentary style: 0.75
            style: Style exaggeration (0-1). Adds theatrical weight. Documentary style: 0.10-0.15

        Returns:
            Path to the generated audio file
        """
        client = self._get_client()

        # Build voice settings - include style if supported
        voice_settings = {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
        }

        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            voice_settings=voice_settings,
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        return output_path

    def get_voices(self) -> list[dict]:
        """List available voices."""
        client = self._get_client()
        response = client.voices.get_all()
        return [{"id": v.voice_id, "name": v.name} for v in response.voices]

    def get_voice_id(self, name: str) -> Optional[str]:
        """Look up voice ID by name."""
        voices = self.get_voices()
        for voice in voices:
            if voice["name"].lower() == name.lower():
                return voice["id"]
        return None

