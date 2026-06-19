"""grandma doctor — checks backend, env vars, model config, and connectivity."""
import os
import shutil
from typing import Tuple

from rich.console import Console
from rich.table import Table

from grandma.extractor import _resolve_backend, _resolve_model, _resolve_base_url

console = Console()

_OK = "[bold green]✅[/bold green]"
_WARN = "[bold yellow]⚠️ [/bold yellow]"
_FAIL = "[bold red]❌[/bold red]"


def _row(status: str, check: str, detail: str) -> Tuple[str, str, str]:
    return status, check, detail


def run() -> None:
    """Run all diagnostic checks and print a Rich table."""
    backend = _resolve_backend()
    table = Table(title="👵 grandma doctor", show_lines=False, expand=False)
    table.add_column("Check", style="bold", min_width=24)
    table.add_column("Status", justify="center", min_width=4)
    table.add_column("Detail", min_width=48)

    # ── Backend ──────────────────────────────────────────────────────────────
    table.add_row("Active backend", _OK, f"[cyan]{backend}[/cyan]")

    # ── claude CLI ───────────────────────────────────────────────────────────
    claude_path = shutil.which("claude")
    if backend == "claude_cli":
        if claude_path:
            table.add_row("claude CLI", _OK, f"Found at [dim]{claude_path}[/dim]")
        else:
            table.add_row(
                "claude CLI", _FAIL,
                "`claude` not in PATH — install Claude Code or set GRANDMA_MODEL_BACKEND"
            )

    # ── Model config ─────────────────────────────────────────────────────────
    model = _resolve_model(__import__("grandma.models", fromlist=["Mode"]).Mode.DEFAULT)
    deep_model = _resolve_model(__import__("grandma.models", fromlist=["Mode"]).Mode.DEEP)

    if model:
        table.add_row("GRANDMA_MODEL", _OK, f"[cyan]{model}[/cyan]")
    else:
        if backend in ("openai", "openai_compatible", "ollama", "groq", "gemini"):
            table.add_row(
                "GRANDMA_MODEL", _FAIL,
                f"Required for backend '{backend}' — set GRANDMA_MODEL=<model-name>"
            )
        else:
            table.add_row("GRANDMA_MODEL", _WARN, "Not set — backend will use its own default")

    if deep_model and deep_model != model:
        table.add_row("GRANDMA_DEEP_MODEL", _OK, f"[cyan]{deep_model}[/cyan]")

    # ── API keys ─────────────────────────────────────────────────────────────
    key_checks = [
        ("GRANDMA_API_KEY", "GRANDMA_API_KEY"),
        ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
        ("OPENAI_API_KEY", "OPENAI_API_KEY"),
        ("GROQ_API_KEY", "GROQ_API_KEY"),
        ("GEMINI_API_KEY", "GEMINI_API_KEY"),
        ("GOOGLE_API_KEY", "GOOGLE_API_KEY"),
    ]
    any_key = False
    for label, var in key_checks:
        val = os.getenv(var)
        if val:
            masked = val[:6] + "..." + val[-3:] if len(val) > 12 else "***"
            table.add_row(label, _OK, f"Set ([dim]{masked}[/dim])")
            any_key = True

    if not any_key and backend == "claude_cli":
        table.add_row("API keys", _WARN, "None set — using Claude Code subscription (OK)")
    elif not any_key:
        table.add_row("API keys", _WARN, "No API keys found — check .env or export them")

    # ── Base URL ─────────────────────────────────────────────────────────────
    base_url = _resolve_base_url(backend)
    if base_url:
        table.add_row("Base URL", _OK, f"[dim]{base_url}[/dim]")

    # ── Live connectivity test ────────────────────────────────────────────────
    console.print(table)
    console.print()

    with console.status("[bold]Testing backend connectivity…[/bold]", spinner="dots"):
        try:
            from grandma.extractor import extract
            from grandma.models import Mode
            extract("Respond with only the word OK.", mode=Mode.DEFAULT)
            console.print(f"{_OK} [bold]Backend connectivity:[/bold] live call succeeded")
        except RuntimeError as exc:
            console.print(f"{_FAIL} [bold]Backend connectivity:[/bold] {exc}")
        except Exception as exc:  # noqa: BLE001
            console.print(f"{_FAIL} [bold]Backend connectivity:[/bold] {exc}")
