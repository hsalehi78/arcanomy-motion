"""LLM service wrapper for OpenAI, Anthropic, and Google Gemini."""

import os
from typing import Literal, Optional

Provider = Literal["openai", "anthropic", "gemini"]


class LLMService:
    """Unified interface for LLM providers."""

    def __init__(self, provider: Provider = "openai"):
        self.provider = provider
        self._client = None

    def _get_client(self):
        """Lazy-load the appropriate client."""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            import openai

            self._client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif self.provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self._client = genai.GenerativeModel("gemini-1.5-pro")

        return self._client

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a completion from the LLM."""
        client = self._get_client()

        if self.provider == "openai":
            model = model or "gpt-4o"
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            model = model or "claude-sonnet-4-20250514"
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        elif self.provider == "gemini":
            response = client.generate_content(
                prompt if not system else f"{system}\n\n{prompt}"
            )
            return response.text

        raise ValueError(f"Unknown provider: {self.provider}")

    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict:
        """Generate a JSON response from the LLM."""
        import json

        system_with_json = (system or "") + "\n\nRespond with valid JSON only."
        response = self.complete(prompt, system=system_with_json, model=model)

        # Strip markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

