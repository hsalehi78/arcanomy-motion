"""LLM service wrapper for OpenAI, Anthropic, and Google Gemini."""

import os
from dataclasses import dataclass
from typing import Literal, Optional

import typer

from src.config import OPENAI_MAX_COMPLETION_TOKENS_MODEL_PREFIXES, get_model

Provider = Literal["openai", "anthropic", "gemini"]


@dataclass
class TokenUsage:
    """Token usage stats from LLM call."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    provider: str

    def print(self):
        """Print token usage to console."""
        typer.echo(f"   [Tokens] {self.input_tokens:,} in -> {self.output_tokens:,} out ({self.total_tokens:,} total) [{self.model}]")


class LLMService:
    """Unified interface for LLM providers."""

    def __init__(self, provider: Provider = "openai"):
        self.provider = provider
        self._client = None
        self.last_usage: Optional[TokenUsage] = None

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
            # Store module reference only; model instantiated per-call in complete()
            self._client = genai

        return self._client

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stage: Optional[str] = None,
    ) -> str:
        """Generate a completion from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            model: Optional model override (uses config default if not provided)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            stage: Optional stage name for stage-specific model selection
        """
        client = self._get_client()

        if self.provider == "openai":
            model = model or get_model(self.provider, stage)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Newer model families use max_completion_tokens instead of max_tokens
            use_new_param = any(
                model.startswith(prefix) for prefix in OPENAI_MAX_COMPLETION_TOKENS_MODEL_PREFIXES
            )
            
            token_params = {}
            if use_new_param:
                token_params["max_completion_tokens"] = max_tokens
            else:
                token_params["max_tokens"] = max_tokens

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                **token_params,
            )
            
            # Track token usage
            usage = response.usage
            self.last_usage = TokenUsage(
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                model=model,
                provider=self.provider,
            )
            self.last_usage.print()
            
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            model = model or get_model(self.provider, stage)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Track token usage
            usage = response.usage
            self.last_usage = TokenUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.input_tokens + usage.output_tokens,
                model=model,
                provider=self.provider,
            )
            self.last_usage.print()
            
            return response.content[0].text

        elif self.provider == "gemini":
            # Resolve model from config (supports stage-specific overrides)
            target_model = model or get_model(self.provider, stage)
            
            # Instantiate GenerativeModel per-call to allow model switching
            generative_model = client.GenerativeModel(target_model)
            
            response = generative_model.generate_content(
                prompt if not system else f"{system}\n\n{prompt}"
            )
            
            # Gemini token counting (approximate from metadata if available)
            try:
                usage_meta = response.usage_metadata
                self.last_usage = TokenUsage(
                    input_tokens=usage_meta.prompt_token_count,
                    output_tokens=usage_meta.candidates_token_count,
                    total_tokens=usage_meta.total_token_count,
                    model=target_model,
                    provider=self.provider,
                )
                self.last_usage.print()
            except Exception:
                pass  # Gemini may not always return usage
            
            return response.text

        raise ValueError(f"Unknown provider: {self.provider}")

    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> dict:
        """Generate a JSON response from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            model: Optional model override
            stage: Optional stage name for stage-specific model selection
        """
        import json

        system_with_json = (system or "") + "\n\nRespond with valid JSON only."
        response = self.complete(prompt, system=system_with_json, model=model, stage=stage)

        # Strip markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

