import json
from unittest.mock import MagicMock

from grandma.extractor import extract
from grandma.models import Mode, Verdict


def _mock_client(response_json: dict):
    """Build a minimal Anthropic client mock."""
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(response_json))]
    client = MagicMock()
    client.messages.create.return_value = msg
    return client


_SAMPLE_VERDICT = {
    "what_happened": "Auth module was refactored to async/await",
    "what_changed": "3 files modified, 1 test added",
    "impact": {
        "positive": "50% faster response time",
        "negative": "Drops Python 3.8 support",
        "neutral": "No API surface change",
    },
    "net_gain": "Worth it — ship it",
    "action_items": ["Pin Python >=3.10 in pyproject.toml"],
}


def test_extract_returns_verdict():
    client = _mock_client(_SAMPLE_VERDICT)
    result = extract("some verbose output", mode=Mode.DEEP, client=client)
    assert isinstance(result, Verdict)
    assert result.what_happened == "Auth module was refactored to async/await"
    assert result.net_gain == "Worth it — ship it"
    assert len(result.action_items) == 1
    client.messages.create.assert_called_once()


def test_extract_respects_grandma_model_env(monkeypatch):
    """When GRANDMA_MODEL is set, the SDK call must use that model."""
    monkeypatch.setenv("GRANDMA_MODEL", "my-test-model")
    client = _mock_client(_SAMPLE_VERDICT)
    extract("some verbose output", mode=Mode.DEEP, client=client)
    assert client.messages.create.call_args.kwargs["model"] == "my-test-model"


def test_extract_no_model_kwarg_when_unset(monkeypatch):
    """When GRANDMA_MODEL is unset, the SDK call must not include a model kwarg."""
    monkeypatch.delenv("GRANDMA_MODEL", raising=False)
    monkeypatch.delenv("GRANDMA_DEEP_MODEL", raising=False)
    client = _mock_client(_SAMPLE_VERDICT)
    extract("some verbose output", mode=Mode.DEEP, client=client)
    assert "model" not in client.messages.create.call_args.kwargs


def test_extract_default_returns_compact_verdict():
    client = _mock_client(
        {
            "what_happened": "Auth module was refactored to async/await",
            "net_gain": "Worth it",
            "action_items": ["Document Python >=3.10"],
        }
    )
    result = extract("some verbose output", client=client)
    assert isinstance(result, Verdict)
    assert result.what_happened == "Auth module was refactored to async/await"
    assert result.what_changed == ""
    assert result.impact.positive is None
    assert result.net_gain == "Worth it"
    assert result.action_items == ["Document Python >=3.10"]


def test_extract_off_returns_original_text():
    text = "leave this alone"
    assert extract(text, mode=Mode.OFF, client=MagicMock()) == text


def test_extract_handles_markdown_fences():
    raw = "```json\n" + json.dumps(_SAMPLE_VERDICT) + "\n```"
    msg = MagicMock()
    msg.content = [MagicMock(text=raw)]
    client = MagicMock()
    client.messages.create.return_value = msg
    result = extract("some text", mode=Mode.DEEP, client=client)
    assert isinstance(result, Verdict)


def test_extract_raises_without_api_key_or_cli(monkeypatch):
    """With no API keys and no claude CLI, extract must raise RuntimeError."""
    for var in (
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY",
        "GEMINI_API_KEY", "GOOGLE_API_KEY",
        "GRANDMA_API_KEY", "GRANDMA_MODEL", "GRANDMA_BASE_URL",
        "GRANDMA_MODEL_BACKEND", "GRANDMA_MODEL_COMMAND",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr("grandma.extractor.shutil.which", lambda _: None)
    try:
        extract("some text")
        assert False, "should have raised"
    except RuntimeError as e:
        assert "claude CLI not found" in str(e)


def test_extract_raises_helpful_error_when_model_missing_for_openai(monkeypatch):
    """OpenAI backend without GRANDMA_MODEL must raise with a helpful message."""
    monkeypatch.setenv("GRANDMA_MODEL_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("GRANDMA_MODEL", raising=False)
    monkeypatch.delenv("GRANDMA_DEEP_MODEL", raising=False)
    try:
        extract("some text")
        assert False, "should have raised"
    except RuntimeError as e:
        assert "No model configured" in str(e)
        assert "GRANDMA_MODEL" in str(e)
