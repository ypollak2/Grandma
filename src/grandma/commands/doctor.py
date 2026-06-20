"""grandma doctor — checks backend, env vars, model config, and connectivity."""

import json
import os
import shutil
from typing import Any, Tuple

from rich.console import Console
from rich.table import Table

from grandma.extractor import _resolve_backend, _resolve_model, _resolve_base_url

console = Console()

_OK = "[bold green]✅[/bold green]"
_WARN = "[bold yellow]⚠️ [/bold yellow]"
_FAIL = "[bold red]❌[/bold red]"

_STATUS_TEXT = {_OK: "ok", _WARN: "warn", _FAIL: "fail"}


def _row(status: str, check: str, detail: str) -> Tuple[str, str, str]:
    return status, check, detail


def run(json_out: bool = False) -> None:
    """Run all diagnostic checks and print a Rich table (or JSON with --json)."""
    backend = _resolve_backend()
    rows: list[dict[str, Any]] = []

    def add(status: str, check: str, detail: str) -> None:
        rows.append({"check": check, "status": _STATUS_TEXT.get(status, status), "detail": detail})

    # ── Backend ──────────────────────────────────────────────────────────────
    add(_OK, "Active backend", backend)

    # ── claude CLI ───────────────────────────────────────────────────────────
    claude_path = shutil.which("claude")
    if backend == "claude_cli":
        if claude_path:
            add(_OK, "claude CLI", f"Found at {claude_path}")
        else:
            add(
                _FAIL,
                "claude CLI",
                "`claude` not in PATH — install Claude Code or set GRANDMA_MODEL_BACKEND",
            )

    # ── Model config ─────────────────────────────────────────────────────────
    model = _resolve_model(__import__("grandma.models", fromlist=["Mode"]).Mode.DEFAULT)
    deep_model = _resolve_model(__import__("grandma.models", fromlist=["Mode"]).Mode.DEEP)

    if model:
        add(_OK, "GRANDMA_MODEL", model)
    else:
        if backend in ("openai", "openai_compatible", "ollama", "groq", "gemini"):
            add(
                _FAIL,
                "GRANDMA_MODEL",
                f"Required for backend '{backend}' — set GRANDMA_MODEL=<model-name>",
            )
        else:
            add(_WARN, "GRANDMA_MODEL", "Not set — backend will use its own default")

    if deep_model and deep_model != model:
        add(_OK, "GRANDMA_DEEP_MODEL", deep_model)

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
            add(_OK, label, f"Set ({masked})")
            any_key = True

    if not any_key and backend == "claude_cli":
        add(_WARN, "API keys", "None set — using Claude Code subscription (OK)")
    elif not any_key:
        add(_WARN, "API keys", "No API keys found — check .env or export them")

    # ── Base URL ─────────────────────────────────────────────────────────────
    base_url = _resolve_base_url(backend)
    if base_url:
        add(_OK, "Base URL", base_url)

    # ── JSON output ──────────────────────────────────────────────────────────
    if json_out:
        print(json.dumps({"checks": rows}, indent=2))
        return

    # ── Rich table ───────────────────────────────────────────────────────────
    table = Table(title="👵 grandma doctor", show_lines=False, expand=False)
    table.add_column("Check", style="bold", min_width=24)
    table.add_column("Status", justify="center", min_width=4)
    table.add_column("Detail", min_width=48)

    status_icon = {v: k for k, v in _STATUS_TEXT.items()}
    for r in rows:
        table.add_row(r["check"], status_icon.get(r["status"], r["status"]), r["detail"])

    console.print(table)
    console.print()

    # ── Live connectivity test ────────────────────────────────────────────────
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
