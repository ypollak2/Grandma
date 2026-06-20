import json
import os
import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars still work without it

# Load ~/.grandma.env (user config file) — lower priority than shell env vars
from grandma.commands.config import CONFIG_FILE as _CONFIG_FILE

if _CONFIG_FILE.exists():
    try:
        from dotenv import load_dotenv as _lde

        _lde(_CONFIG_FILE, override=False)
    except ImportError:
        # Manual fallback: read KEY=VALUE lines without python-dotenv
        for _line in _CONFIG_FILE.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

from grandma.card import THEMES, render
from grandma.extractor import extract
from grandma.models import Impact, Mode, Verdict

app = typer.Typer(help="Explain it like you'd tell grandma.")
err = Console(stderr=True)

_DEMO_DEFAULT = Verdict(
    what_happened="**Auth module** refactored from sync to async/await.",
    net_gain="**74% faster** login. Drop Python 3.8 support first.",
    action_items=[
        "Raise min Python to 3.11 in pyproject.toml",
        "Update deployment docs before merge",
    ],
    story_so_far="We are reviewing a PR that refactors the authentication layer.",
)

_DEMO_DEEP = Verdict(
    what_happened="**Auth module** refactored from sync to async/await.",
    what_changed="3 files modified (382 lines), 1 regression test added.",
    impact=Impact(
        positive="Login latency: 340ms → 87ms (**74% faster**). Token refresh: 290ms → 61ms.",
        negative="Requires Python 3.11+ due to asyncio.TaskGroup. **Breaks** 3.9/3.10 users.",
        neutral="No API surface change. All existing tests pass.",
    ),
    net_gain="**Win** on performance. Needs runtime floor bump before shipping.",
    action_items=[
        "Raise min Python to 3.11 in pyproject.toml",
        "Update deployment docs with async-first pattern note",
        "Update contributing guide",
    ],
    story_so_far="We are 2 turns into reviewing a performance-focused PR on the auth module.",
)


def _read_clipboard() -> str:
    """Read text from the system clipboard. Tries pyperclip, then platform tools."""
    try:
        import pyperclip  # type: ignore[import-untyped]

        return pyperclip.paste()
    except ImportError:
        pass

    if sys.platform == "darwin":
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        return result.stdout
    # Linux (xclip / xsel)
    for cmd in (["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"]):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
        except FileNotFoundError:
            continue
    raise RuntimeError(
        "Clipboard read failed. Install pyperclip (`pip install pyperclip`) or xclip/xsel."
    )


@app.command()
def main(
    text: Optional[str] = typer.Argument(None, help="LLM output to process, or pipe via stdin"),
    mode: Mode = typer.Option(
        os.getenv("GRANDMA_MODE", Mode.DEFAULT.value),
        "--mode",
        case_sensitive=False,
        help="Extraction mode: default, deep, or off",
    ),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output raw JSON instead of a card"),
    demo: bool = typer.Option(False, "--demo", help="Show example output without calling the API"),
    paste: bool = typer.Option(False, "--paste", "-p", help="Read input from the system clipboard"),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        "-t",
        help=f"Card theme: {', '.join(THEMES)}",
    ),
) -> None:
    if demo:
        verdict = _DEMO_DEEP if mode is Mode.DEEP else _DEMO_DEFAULT
        if json_out:
            typer.echo(verdict.model_dump_json(indent=2))
        else:
            render(verdict, mode=mode, theme=theme)
        return

    if paste:
        try:
            text = _read_clipboard()
        except RuntimeError as exc:
            err.print(f"[red]Clipboard error:[/red] {exc}")
            raise typer.Exit(1)
    elif text is None:
        if sys.stdin.isatty():
            err.print("[red]Error:[/red] give grandma some text, pipe it in, or use --paste")
            raise typer.Exit(1)
        text = sys.stdin.read()

    if not text or not text.strip():
        err.print("[red]Error:[/red] empty input")
        raise typer.Exit(1)

    # Pick up conversation history injected by the Stop hook
    history = None
    raw_history = os.getenv("GRANDMA_HISTORY", "")
    if raw_history:
        try:
            history = json.loads(raw_history)
        except (json.JSONDecodeError, ValueError):
            pass

    try:
        result = extract(text, mode=mode, history=history)
    except ValueError as exc:
        err.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)
    except Exception as exc:
        err.print(f"[red]Extraction failed:[/red] {exc}")
        raise typer.Exit(1)

    if isinstance(result, str):
        typer.echo(result)
    elif json_out:
        typer.echo(result.model_dump_json(indent=2))
    else:
        render(result, mode=mode, theme=theme)


@app.command()
def serve() -> None:
    """Start grandma as an MCP server (for Cursor, Cline, Continue, Windsurf, Zed, Goose)."""
    from grandma.mcp_server import serve as _serve

    _serve()


@app.command()
def doctor(
    json_out: bool = typer.Option(False, "--json", "-j", help="Output diagnostics as JSON"),
) -> None:
    """Check backend config, API keys, model setup, and connectivity."""
    from grandma.commands.doctor import run

    run(json_out=json_out)


@app.command()
def replay(
    n: int = typer.Option(6, "--turns", "-n", help="Number of last assistant turns to digest"),
    mode: str = typer.Option("default", "--mode", "-m", help="Extraction mode: default or deep"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show log path being used"),
    source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Path to a specific log file instead of auto-detecting"
    ),
) -> None:
    """Digest the last Claude Code / Codex / aider / Gemini CLI session."""
    from grandma.commands.replay import run

    run(n=n, mode_str=mode, verbose=verbose, source=source)


@app.command()
def config(
    action: str = typer.Argument(..., help="Action: set, get, unset, list"),
    key: Optional[str] = typer.Argument(None, help="Config key (e.g. backend, model, theme)"),
    value: Optional[str] = typer.Argument(None, help="Value to set"),
) -> None:
    """Get, set, or list persistent grandma configuration (~/.grandma.env)."""
    from grandma.commands.config import cmd_get, cmd_list, cmd_set, cmd_unset

    if action == "list":
        cmd_list()
    elif action == "set":
        if not key or value is None:
            err.print("[red]Usage:[/red] grandma config set <key> <value>")
            raise typer.Exit(1)
        cmd_set(key, value)
    elif action == "get":
        if not key:
            err.print("[red]Usage:[/red] grandma config get <key>")
            raise typer.Exit(1)
        cmd_get(key)
    elif action == "unset":
        if not key:
            err.print("[red]Usage:[/red] grandma config unset <key>")
            raise typer.Exit(1)
        cmd_unset(key)
    else:
        err.print(f"[red]Unknown action:[/red] {action}. Use set, get, unset, or list.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
