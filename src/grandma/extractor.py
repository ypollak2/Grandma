import json
import os
import shutil
import subprocess
from typing import List, Optional, Union

from grandma.models import Mode, Verdict

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEEP_MODEL = "claude-sonnet-4-6"

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


def _extract_via_claude_code(text: str, mode: Mode, history: Optional[List[str]] = None) -> str:
    """Use `claude -p -` (Claude Code subscription) as the LLM backend, via stdin."""
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("claude CLI not found — install Claude Code or set ANTHROPIC_API_KEY")
    history_block = _build_history_block(history)
    template = _DEFAULT_PROMPT if mode is Mode.DEFAULT else _DEEP_PROMPT
    prompt = template.format(history_block=history_block) + text
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


def _extract_via_sdk(text: str, mode: Mode, client, history: Optional[List[str]] = None) -> str:
    """Use Anthropic SDK with an API key."""
    history_block = _build_history_block(history)
    template = _DEFAULT_PROMPT if mode is Mode.DEFAULT else _DEEP_PROMPT
    system = template.format(history_block=history_block).split("The text to summarise:")[0].strip()
    response = client.messages.create(
        model=DEFAULT_MODEL if mode is Mode.DEFAULT else DEEP_MODEL,
        max_tokens=600 if mode is Mode.DEFAULT else 1400,
        system=system,
        messages=[{"role": "user", "content": text}],
    )
    return response.content[0].text.strip()


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

    # Backend selection: explicit client > ANTHROPIC_API_KEY > claude CLI subscription
    if client is not None:
        raw = _extract_via_sdk(text, mode, client, history)
    elif os.getenv("ANTHROPIC_API_KEY"):
        from anthropic import Anthropic
        raw = _extract_via_sdk(text, mode, Anthropic(), history)
    else:
        raw = _extract_via_claude_code(text, mode, history)

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
