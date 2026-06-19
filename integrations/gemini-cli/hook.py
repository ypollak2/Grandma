#!/usr/bin/env python3
"""Gemini CLI AfterAgent hook — fires after each agent turn."""

import json
import os
import subprocess
import sys

GRANDMA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", ".venv", "bin", "grandma"
)
MIN_WORDS = 80


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Gemini CLI AfterAgent event shape
    text = data.get("agent_response", "") or data.get("response", "") or data.get("content", "")
    if isinstance(text, list):
        text = " ".join(
            part.get("text", "")
            for part in text
            if isinstance(part, dict) and part.get("type") == "text"
        )
    text = str(text).strip()

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
            print(json.dumps({"message": result.stdout.strip()}))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


if __name__ == "__main__":
    main()
