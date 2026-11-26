"""Google Gemini client using the Google Gen AI SDK.

The API key is read from the GEMINI_API_KEY environment variable.
It is never logged, returned by the API, or sent to the browser.
"""
from __future__ import annotations

import logging
import time

from app.core.config import Settings
from app.core.errors import LLMError

logger = logging.getLogger("evidenceai.gemini")

MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_DELAYS_SECONDS = (1, 2)


def _get_http_status(exc: Exception) -> int | None:
    """Extract an HTTP status code from common SDK exception attributes."""
    for attribute in ("code", "status_code"):
        value = getattr(exc, attribute, None)

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.isdigit():
            return int(value)

    return None


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
            raise LLMError(
                "The Gemini API key is not configured.",
                status_code=503,
            )

        try:
            from google import genai
            from google.genai import types

            if self._client is None:
                self._client = genai.Client(api_key=self._api_key)

            last_exception = None

            for attempt in range(1, MAX_ATTEMPTS + 1):
                try:
                    response = self._client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.1,
                            max_output_tokens=1024,
                        ),
                    )
                    text = (response.text or "").strip()
                    break

                except Exception as exc:
                    last_exception = exc
                    status_code = _get_http_status(exc)

                    is_retryable = status_code in RETRYABLE_STATUS_CODES
                    has_retries_remaining = attempt < MAX_ATTEMPTS

                    if not is_retryable or not has_retries_remaining:
                        logger.error(
                            "Gemini request failed (%s, status=%s).",
                            type(exc).__name__,
                            status_code,
                        )
                        raise LLMError(
                            "The Gemini request failed."
                        ) from exc

                    delay = RETRY_DELAYS_SECONDS[attempt - 1]

                    logger.warning(
                        "Gemini transient failure (%s, status=%s). "
                        "Retrying attempt %s/%s in %s seconds.",
                        type(exc).__name__,
                        status_code,
                        attempt + 1,
                        MAX_ATTEMPTS,
                        delay,
                    )

                    time.sleep(delay)

            else:
                # Defensive fallback if the retry loop exits unexpectedly.
                raise LLMError("The Gemini request failed.") from last_exception

        except LLMError:
            raise

        except Exception as exc:
            # Technical detail goes to the server log only.
            logger.error("Gemini request failed: %s", type(exc).__name__)
            raise LLMError("The Gemini request failed.") from exc

        if not text:
            raise LLMError(
                "Gemini returned an empty response (it may have been blocked)."
            )

        return text
