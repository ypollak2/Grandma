#!/usr/bin/env python3
"""Claude Code Stop hook — pipes the last assistant response through grandma."""

import json
import os
import subprocess
import sys

GRANDMA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", ".venv", "bin", "grandma"
)
MIN_WORDS = 80
MAX_HISTORY = 3


def collect_messages(transcript_path):
    messages = []
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "")
                        if isinstance(content, list):
                            parts = [
                                c.get("text", "")
                                for c in content
                                if isinstance(c, dict) and c.get("type") == "text"
                            ]
                            text = " ".join(parts).strip()
                        else:
                            text = str(content).strip()
                        if text:
                            messages.append(text)
                except (json.JSONDecodeError, KeyError):
                    continue
    except (IOError, OSError):
        pass
    if not messages:
        return "", []
    last = messages[-1]
    history = list(reversed(messages[-(MAX_HISTORY + 1) : -1]))
    return last, history


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    transcript_path = data.get("transcript_path", "")
    if not transcript_path:
        sys.exit(0)

    last_text, history = collect_messages(transcript_path)
    if len(last_text.split()) < MIN_WORDS:
        sys.exit(0)

    env_extra = {"GRANDMA_HISTORY": json.dumps(history)} if history else {}
    try:
        result = subprocess.run(
            [GRANDMA],
            input=last_text,
            capture_output=True,
            text=True,
            timeout=130,
            env={**os.environ, **env_extra},
        )
        if result.returncode == 0 and result.stdout.strip():
            print(json.dumps({"systemMessage": result.stdout.strip()}))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


if __name__ == "__main__":
    main()
