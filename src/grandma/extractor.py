import json
import os
import shutil
import subprocess
from typing import List, Optional, Union

from grandma.models import Mode, Verdict

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEEP_MODEL = "claude-sonnet-4-6"

# Provider default base URLs for OpenAI-compatible endpoints
_PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "ollama": "http://localhost:11434/v1",
}

_DEFAULT_PROMPT = """You are Grandma. You read verbose LLM output and refuse to waste anyone's afternoon.

Keep every important fact. Do not dumb it down. Extract only the bottom line.

{history_block}Return ONLY raw JSON with this shape:
{{
  "what_happened": "one short sentence — **bold** the most critical noun or verb",
  "net_gain": "the practical bottom line — **bold** the verdict word (e.g. **Fixed**, **Broken**, **Done**, **Risky**)",
  "action_items": ["specific next step", "specific next step"],
  "story_so_far": "one sentence on the overall arc so far (e.g. 'We are 3 turns into debugging an auth bug'), or null if this is the first turn"
}}

No markdown fences. No preamble. The text to summarise:

"""

_DEEP_PROMPT = """You are Grandma. You read verbose LLM output and refuse to waste anyone's afternoon.

Keep every important fact. Do not dumb it down. Turn the output into a structured verdict.

{history_block}Return ONLY raw JSON with this exact shape:
{{
  "what_happened": "one sentence — **bold** the most critical noun or verb",
  "what_changed": "specific observable changes — **bold** the key change",
  "impact": {{
    "positive": "what improved, or null",
    "negative": "what broke or regressed, or null",
    "neutral": "what shifted without clear valence, or null"
  }},
  "net_gain": "the bottom line: **bold** the verdict word (e.g. **Win**, **Risk**, **Blocked**, **Mixed**)",
  "action_items": ["specific next step", "specific next step"],
  "story_so_far": "one sentence on the overall conversation arc so far, or null if first turn"
}}

No markdown fences. No preamble. The text to summarise:

"""


def _build_history_block(history: Optional[List[str]]) -> str:
    if not history:
        return ""
    lines = ["Conversation arc so far (most recent first):"]
    for i, msg in enumerate(history[:4], 1):
        snippet = msg[:120].replace("\n", " ")
        lines.append(f"  Turn -{i}: {snippet}...")
    lines.append("")
    return "\n".join(lines) + "\n"


def _build_prompt(text: str, mode: Mode, history: Optional[List[str]]) -> str:
    history_block = _build_history_block(history)
    template = _DEFAULT_PROMPT if mode is Mode.DEFAULT else _DEEP_PROMPT
    return template.format(history_block=history_block) + text


def _resolve_backend() -> str:
    """Determine which backend to use based on env vars. Backward-compatible."""
    backend = os.getenv("GRANDMA_MODEL_BACKEND", "").strip().lower()
    if backend:
        return backend
    # Infer from available keys/urls
    if os.getenv("GRANDMA_MODEL") or os.getenv("GRANDMA_API_KEY") or os.getenv("GRANDMA_BASE_URL"):
        return "openai_compatible"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "claude_cli"


def _resolve_model(mode: Mode) -> str:
    if mode is Mode.DEEP:
        return (
            os.getenv("GRANDMA_DEEP_MODEL")
            or os.getenv("GRANDMA_MODEL")
            or DEEP_MODEL
        )
    return os.getenv("GRANDMA_MODEL") or DEFAULT_MODEL


def _resolve_api_key(backend: str) -> Optional[str]:
    """Return the API key for the given backend, checking provider-specific vars."""
    key = os.getenv("GRANDMA_API_KEY")
    if key:
        return key
    mapping = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "ollama": None,  # no key needed
    }
    env_var = mapping.get(backend)
    if env_var:
        return os.getenv(env_var)
    # Gemini fallback
    if backend == "gemini":
        return os.getenv("GOOGLE_API_KEY")
    return None


def _resolve_base_url(backend: str) -> Optional[str]:
    explicit = os.getenv("GRANDMA_BASE_URL")
    if explicit:
        return explicit
    return _PROVIDER_BASE_URLS.get(backend)


def _extract_via_openai_compat(
    text: str,
    mode: Mode,
    history: Optional[List[str]],
    backend: str,
) -> str:
    """Call any OpenAI-compatible /v1/chat/completions endpoint via httpx."""
    import httpx

    model = _resolve_model(mode)
    api_key = _resolve_api_key(backend) or "no-key"
    base_url = _resolve_base_url(backend) or "http://localhost:11434/v1"
    prompt = _build_prompt(text, mode, history)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600 if mode is Mode.DEFAULT else 1400,
        "temperature": 0.2,
    }

    response = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _extract_via_sdk(text: str, mode: Mode, client, history: Optional[List[str]]) -> str:
    """Use Anthropic SDK with an API key."""
    history_block = _build_history_block(history)
    template = _DEFAULT_PROMPT if mode is Mode.DEFAULT else _DEEP_PROMPT
    system = template.format(history_block=history_block).split("The text to summarise:")[0].strip()
    response = client.messages.create(
        model=_resolve_model(mode),
        max_tokens=600 if mode is Mode.DEFAULT else 1400,
        system=system,
        messages=[{"role": "user", "content": text}],
    )
    return response.content[0].text.strip()


def _extract_via_claude_code(text: str, mode: Mode, history: Optional[List[str]]) -> str:
    """Use `claude -p -` (Claude Code subscription) as the LLM backend, via stdin."""
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("claude CLI not found — install Claude Code or set ANTHROPIC_API_KEY / GRANDMA_MODEL_BACKEND")
    prompt = _build_prompt(text, mode, history)
    result = subprocess.run(
        [claude, "-p", "-", "--output-format", "text"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
    return result.stdout.strip()


def _extract_via_custom_command(text: str, mode: Mode, history: Optional[List[str]]) -> str:
    """Run GRANDMA_MODEL_COMMAND with prompt on stdin, response on stdout."""
    cmd = os.getenv("GRANDMA_MODEL_COMMAND") or os.getenv("GRANDMA_DEEP_MODEL_COMMAND")
    if not cmd:
        raise RuntimeError("GRANDMA_MODEL_COMMAND is not set")
    prompt = _build_prompt(text, mode, history)
    result = subprocess.run(
        cmd,
        shell=True,  # noqa: S602 — user controls this command via their own .env
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"custom command error: {result.stderr.strip()}")
    return result.stdout.strip()


def extract(
    text: str,
    mode: Mode = Mode.DEFAULT,
    client=None,
    history: Optional[List[str]] = None,
) -> Union[Verdict, str]:
    if not isinstance(mode, Mode):
        mode = Mode(mode)

    if mode is Mode.OFF:
        return text

    # Backend selection
    if client is not None:
        # Explicit Anthropic client passed in (legacy/programmatic usage)
        raw = _extract_via_sdk(text, mode, client, history)
    else:
        backend = _resolve_backend()
        if backend == "anthropic":
            from anthropic import Anthropic
            raw = _extract_via_sdk(text, mode, Anthropic(), history)
        elif backend == "claude_cli":
            raw = _extract_via_claude_code(text, mode, history)
        elif backend == "custom_command":
            raw = _extract_via_custom_command(text, mode, history)
        else:
            # openai / openai_compatible / ollama / groq / gemini / any future provider
            raw = _extract_via_openai_compat(text, mode, history, backend)

    raw = _strip_fences(raw)
    data = json.loads(raw)

    if mode is Mode.DEFAULT:
        return Verdict(
            what_happened=data.get("what_happened", ""),
            net_gain=data.get("net_gain", ""),
            action_items=data.get("action_items", []),
            story_so_far=data.get("story_so_far"),
        )

    data.setdefault("impact", {})
    return Verdict.model_validate(data)


def _strip_fences(raw: str) -> str:
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    return raw
