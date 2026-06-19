#!/usr/bin/env python3
"""Codex CLI Stop hook — same Stop event shape as Claude Code."""
import json
import os
import subprocess
import sys

GRANDMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".venv", "bin", "grandma")
MIN_WORDS = 80


def last_assistant_text(data: dict) -> str:
    # Codex CLI Stop event provides last_assistant_message directly
    msg = data.get("last_assistant_message", "")
    if isinstance(msg, list):
        parts = [c.get("text", "") for c in msg if isinstance(c, dict) and c.get("type") == "text"]
        return " ".join(parts).strip()
    return str(msg).strip()


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    text = last_assistant_text(data)
    if len(text.split()) < MIN_WORDS:
        sys.exit(0)

    try:
        result = subprocess.run(
            [GRANDMA],
            input=text,
            capture_output=True,
            text=True,
            timeout=130,
            env=os.environ.copy(),
        )
        if result.returncode == 0 and result.stdout.strip():
            print(json.dumps({"systemMessage": result.stdout.strip()}))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


if __name__ == "__main__":
    main()
