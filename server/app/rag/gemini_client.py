"""Google Gemini client using the Google Gen AI SDK (`google-genai`) (Member 4).

The API key is read from the GEMINI_API_KEY environment variable (see core/config.py).
It is never logged, never returned by the API and never sent to the browser.
"""
from __future__ import annotations

import logging

from app.core.config import Settings
from app.core.errors import LLMError

logger = logging.getLogger("evidenceai.gemini")


class GeminiLLM:
    def __init__(self, settings: Settings):
        self._api_key = settings.gemini_api_key.strip()
        self._model = settings.gemini_model
        self._configured = settings.llm_configured
        self._client = None

    @property
    def is_configured(self) -> bool:
        return self._configured

    def generate(self, system_instruction: str, prompt: str) -> str:
        if not self._configured:
            raise LLMError("The Gemini API key is not configured.", status_code=503)
        try:
            from google import genai
            from google.genai import types

            if self._client is None:
                self._client = genai.Client(api_key=self._api_key)
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,  # low = more faithful to the evidence
                    max_output_tokens=1024,
                ),
            )
            text = (response.text or "").strip()
        except Exception as exc:
            # Technical detail goes to the server log only (never the browser).
            logger.error("Gemini request failed: %s", type(exc).__name__)
            raise LLMError("The Gemini request failed.") from exc
        if not text:
            raise LLMError("Gemini returned an empty response (it may have been blocked).")
        return text
