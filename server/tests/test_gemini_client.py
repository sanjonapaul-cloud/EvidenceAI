"""Offline tests for Gemini retry behavior."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.errors import LLMError
from app.rag import gemini_client


@pytest.fixture
def settings():
    return SimpleNamespace(
        gemini_api_key="fake-test-key",
        gemini_model="test-model",
        llm_configured=True,
    )


@pytest.fixture
def mocked_gemini(monkeypatch):
    from google import genai

    client = Mock()
    client.models.generate_content = Mock()

    monkeypatch.setattr(genai, "Client", lambda **kwargs: client)

    sleep_calls = []
    monkeypatch.setattr(
        gemini_client.time,
        "sleep",
        lambda seconds: sleep_calls.append(seconds),
    )

    return client, sleep_calls


class FakeHTTPError(Exception):
    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


def test_503_then_success_retries_and_returns_answer(settings, mocked_gemini):
    client, sleep_calls = mocked_gemini
    client.models.generate_content.side_effect = [
        FakeHTTPError(503),
        SimpleNamespace(text="Successful answer"),
    ]

    llm = gemini_client.GeminiLLM(settings)
    result = llm.generate("system", "prompt")

    assert result == "Successful answer"
    assert client.models.generate_content.call_count == 2
    assert sleep_calls == [1]


def test_repeated_503_stops_after_max_attempts(settings, mocked_gemini):
    client, sleep_calls = mocked_gemini
    client.models.generate_content.side_effect = [
        FakeHTTPError(503),
        FakeHTTPError(503),
        FakeHTTPError(503),
    ]

    llm = gemini_client.GeminiLLM(settings)

    with pytest.raises(LLMError):
        llm.generate("system", "prompt")

    assert client.models.generate_content.call_count == 3
    assert sleep_calls == [1, 2]


def test_permanent_error_does_not_retry(settings, mocked_gemini):
    client, sleep_calls = mocked_gemini
    client.models.generate_content.side_effect = FakeHTTPError(400)

    llm = gemini_client.GeminiLLM(settings)

    with pytest.raises(LLMError):
        llm.generate("system", "prompt")

    assert client.models.generate_content.call_count == 1
    assert sleep_calls == []


def test_empty_response_raises_llm_error(settings, mocked_gemini):
    client, sleep_calls = mocked_gemini
    client.models.generate_content.return_value = SimpleNamespace(text="")

    llm = gemini_client.GeminiLLM(settings)

    with pytest.raises(LLMError, match="empty response"):
        llm.generate("system", "prompt")

    assert client.models.generate_content.call_count == 1
    assert sleep_calls == []


def test_unconfigured_client_does_not_call_gemini():
    settings = SimpleNamespace(
        gemini_api_key="",
        gemini_model="test-model",
        llm_configured=False,
    )

    llm = gemini_client.GeminiLLM(settings)

    with pytest.raises(LLMError, match="not configured"):
        llm.generate("system", "prompt")


@pytest.mark.parametrize(
    ("exception", "expected_status"),
    [
        (FakeHTTPError(503), 503),
        (FakeHTTPError(429), 429),
        (FakeHTTPError(400), 400),
        (Exception("no status"), None),
    ],
)
def test_http_status_extraction(exception, expected_status):
    assert gemini_client._get_http_status(exception) == expected_status

def test_http_status_extraction_from_code_attribute():
    exception = Exception("service unavailable")
    exception.code = 503

    assert gemini_client._get_http_status(exception) == 503
