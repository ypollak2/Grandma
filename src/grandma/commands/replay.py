"""grandma replay — digest the last AI coding agent session."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from rich.console import Console

console = Console()

# Known session log locations, in priority order
_LOG_GLOBS = [
    ("claude", Path.home() / ".claude" / "projects", "**/*.jsonl"),
    ("codex", Path.home() / ".codex", "**/*.jsonl"),
    ("gemini", Path.home() / ".gemini" / "logs", "**/*.log"),
    ("aider", Path.cwd(), ".aider.chat.history.md"),
]


def _find_latest_log() -> Optional[tuple[str, Path]]:
    """Return (tool_name, path) for the most recently modified session log."""
    candidates: List[tuple[str, Path]] = []
    for tool, base, pattern in _LOG_GLOBS:
        if base.exists():
            for p in base.glob(pattern):
                if p.is_file() and p.stat().st_size > 0:
                    candidates.append((tool, p))
    if not candidates:
        return None
    return max(candidates, key=lambda t: t[1].stat().st_mtime)


def _extract_messages_jsonl(path: Path, n: int = 6) -> List[str]:
    """Parse Claude Code / Codex JSONL transcript and return last N assistant turns."""
    messages: List[str] = []
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Claude Code transcript format: {type: "assistant", message: {content: [...]}}
                role = obj.get("type") or obj.get("role") or ""
                if role != "assistant":
                    continue
                # Extract text content
                content = obj.get("message", {}).get("content") or obj.get("content") or ""
                if isinstance(content, list):
                    text = " ".join(
                        b.get("text", "")
                        for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                elif isinstance(content, str):
                    text = content
                else:
                    continue
                text = text.strip()
                if text:
                    messages.append(text)
    except OSError:
        pass
    return messages[-n:]


def _extract_messages_aider(path: Path, n: int = 6) -> List[str]:
    """Parse aider markdown history and return last N assistant blocks."""
    messages: List[str] = []
    current: List[str] = []
    in_assistant = False
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("#### "):
                    if in_assistant and current:
                        messages.append("".join(current).strip())
                        current = []
                    in_assistant = "ASSISTANT" in line.upper()
                elif in_assistant:
                    current.append(line)
        if in_assistant and current:
            messages.append("".join(current).strip())
    except OSError:
        pass
    return messages[-n:]


def _extract_messages_log(path: Path, n: int = 6) -> List[str]:
    """Fallback: return last N non-empty lines of any log file."""
    try:
        lines = [
            line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()
        ]
        return lines[-n:]
    except OSError:
        return []


def run(
    n: int = 6, mode_str: str = "default", verbose: bool = False, source: Optional[str] = None
) -> None:
    """Find the latest session log, extract messages, and print a grandma digest card."""
    if source:
        source_path = Path(source).expanduser()
        if not source_path.exists():
            console.print(f"[red]Error:[/red] path not found: {source_path}")
            return
        found = ("custom", source_path)
    else:
        found = _find_latest_log()

    if not found:
        console.print("[yellow]⚠️  No session logs found.[/yellow]")
        console.print(
            "grandma replay looks for logs in:\n"
            "  ~/.claude/projects/**/*.jsonl\n"
            "  ~/.codex/**/*.jsonl\n"
            "  ~/.gemini/logs/**/*.log\n"
            "  .aider.chat.history.md (current directory)"
        )
        return

    tool, path = found
    if verbose:
        console.print(f"[dim]Using {tool} log: {path}[/dim]")

    if path.suffix == ".jsonl":
        messages = _extract_messages_jsonl(path, n)
    elif path.suffix == ".md":
        messages = _extract_messages_aider(path, n)
    else:
        messages = _extract_messages_log(path, n)

    if not messages:
        console.print(f"[yellow]⚠️  No assistant messages found in {path.name}[/yellow]")
        return

    combined = "\n\n---\n\n".join(messages)
    summary_prompt = (
        f"Session digest from {tool} ({path.name}, last {len(messages)} turns):\n\n{combined}"
    )

    with console.status("[bold]Grandma is reading your session…[/bold]", spinner="dots"):
        from grandma.extractor import extract
        from grandma.models import Mode

        try:
            mode = Mode(mode_str)
        except ValueError:
            mode = Mode.DEFAULT
        result = extract(summary_prompt, mode=mode)

    from grandma.card import render

    render(result, mode=mode)
