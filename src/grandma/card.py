import re

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from grandma.models import Mode, Verdict

console = Console()


def _md_bold_to_rich(text: str) -> str:
    """Convert **word** Markdown bold to Rich yellow-bold markup."""
    return re.sub(r"\*\*(.+?)\*\*", r"[bold yellow]\1[/bold yellow]", text)


def render(verdict: Verdict, mode: Mode = Mode.DEFAULT) -> None:
    if not isinstance(mode, Mode):
        mode = Mode(mode)

    if mode is Mode.DEEP:
        _render_deep(verdict)
    else:
        _render_default(verdict)


def _story_header(verdict: Verdict) -> str:
    if verdict.story_so_far:
        return f"[dim italic]📖 {verdict.story_so_far}[/dim italic]\n\n"
    return ""


def _render_default(verdict: Verdict) -> None:
    actions = "; ".join(verdict.action_items) if verdict.action_items else "No action items."
    body = "".join(
        [
            _story_header(verdict),
            f"[bold]What happened:[/bold] {_md_bold_to_rich(verdict.what_happened)}\n",
            f"[bold]Bottom line:[/bold]   {_md_bold_to_rich(verdict.net_gain)}\n",
            f"[bold]Do next:[/bold]       {_md_bold_to_rich(actions)}",
        ]
    )
    console.print(
        Panel(body, title="[bold magenta]👵 grandma[/bold magenta]", border_style="magenta")
    )


def _render_deep(verdict: Verdict) -> None:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("field", style="bold magenta", width=18)
    table.add_column("value", style="white")

    if verdict.story_so_far:
        table.add_row("📖 story arc", f"[dim italic]{verdict.story_so_far}[/dim italic]")
        table.add_row("", "")

    table.add_row("👀 happened", _md_bold_to_rich(verdict.what_happened))
    table.add_row("🧶 changed", _md_bold_to_rich(verdict.what_changed))
    table.add_row("✅ positive", _md_bold_to_rich(verdict.impact.positive or "None"))
    table.add_row("⚠️ negative", _md_bold_to_rich(verdict.impact.negative or "None"))
    table.add_row("➖ neutral", _md_bold_to_rich(verdict.impact.neutral or "None"))
    table.add_row("💡 net gain", f"[bold yellow]{_md_bold_to_rich(verdict.net_gain)}[/bold yellow]")
    table.add_row(
        "📋 actions",
        _md_bold_to_rich("\n".join(f"- {item}" for item in verdict.action_items) or "None"),
    )

    console.print(
        Panel(table, title="[bold magenta]👵 grandma[/bold magenta]", border_style="magenta")
    )
