import os
import re

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from grandma.models import Mode, Verdict

console = Console()

THEMES = ("default", "minimal", "neon", "mono")


def _current_theme(theme: str | None) -> str:
    t = (theme or os.getenv("GRANDMA_THEME", "default")).lower()
    return t if t in THEMES else "default"


def _md_bold_to_rich(text: str, theme: str = "default") -> str:
    if theme == "minimal":
        return re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    if theme == "mono":
        return re.sub(r"\*\*(.+?)\*\*", r"[bold]\1[/bold]", text)
    if theme == "neon":
        return re.sub(r"\*\*(.+?)\*\*", r"[bold cyan]\1[/bold cyan]", text)
    return re.sub(r"\*\*(.+?)\*\*", r"[bold yellow]\1[/bold yellow]", text)


def render(verdict: Verdict, mode: Mode = Mode.DEFAULT, theme: str | None = None) -> None:
    if not isinstance(mode, Mode):
        mode = Mode(mode)
    t = _current_theme(theme)
    if t == "minimal":
        _render_minimal(verdict, mode)
    elif mode is Mode.DEEP:
        _render_deep(verdict, t)
    else:
        _render_default(verdict, t)


def _story_header(verdict: Verdict, theme: str) -> str:
    if not verdict.story_so_far:
        return ""
    if theme == "minimal":
        return f"Story: {verdict.story_so_far}\n\n"
    return f"[dim italic]📖 {verdict.story_so_far}[/dim italic]\n\n"


def _render_minimal(verdict: Verdict, mode: Mode) -> None:
    """Plain text output — no Rich markup, no emoji."""
    strip = lambda s: re.sub(r"[*]{1,2}", "", s)  # noqa: E731
    lines = []
    if verdict.story_so_far:
        lines.append(f"Story: {strip(verdict.story_so_far)}\n")
    lines.append(f"What happened: {strip(verdict.what_happened)}")
    if mode is Mode.DEEP and verdict.what_changed:
        lines.append(f"What changed:  {strip(verdict.what_changed)}")
        if verdict.impact.positive:
            lines.append(f"Positive:      {strip(verdict.impact.positive)}")
        if verdict.impact.negative:
            lines.append(f"Negative:      {strip(verdict.impact.negative)}")
        if verdict.impact.neutral:
            lines.append(f"Neutral:       {strip(verdict.impact.neutral)}")
    lines.append(f"Bottom line:   {strip(verdict.net_gain)}")
    if verdict.action_items:
        lines.append("Do next:")
        for item in verdict.action_items:
            lines.append(f"  - {strip(item)}")
    print("\n".join(lines))


def _panel_style(theme: str) -> tuple[str, str]:
    if theme == "neon":
        return "bold magenta", "cyan"
    if theme == "mono":
        return "bold white", "white"
    return "bold magenta", "magenta"


def _render_default(verdict: Verdict, theme: str) -> None:
    title_color, border = _panel_style(theme)
    actions = "; ".join(verdict.action_items) if verdict.action_items else "No action items."
    body = "".join(
        [
            _story_header(verdict, theme),
            f"[bold]What happened:[/bold] {_md_bold_to_rich(verdict.what_happened, theme)}\n",
            f"[bold]Bottom line:[/bold]   {_md_bold_to_rich(verdict.net_gain, theme)}\n",
            f"[bold]Do next:[/bold]       {_md_bold_to_rich(actions, theme)}",
        ]
    )
    console.print(
        Panel(body, title=f"[{title_color}]👵 grandma[/{title_color}]", border_style=border)
    )


def _render_deep(verdict: Verdict, theme: str) -> None:
    title_color, border = _panel_style(theme)
    field_style = "bold magenta" if theme != "mono" else "bold white"
    highlight = (
        "bold yellow" if theme == "default" else ("bold cyan" if theme == "neon" else "bold")
    )

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("field", style=field_style, width=18)
    table.add_column("value", style="white")

    if verdict.story_so_far:
        table.add_row("📖 story arc", f"[dim italic]{verdict.story_so_far}[/dim italic]")
        table.add_row("", "")

    table.add_row("👀 happened", _md_bold_to_rich(verdict.what_happened, theme))
    table.add_row("🧶 changed", _md_bold_to_rich(verdict.what_changed, theme))
    table.add_row("✅ positive", _md_bold_to_rich(verdict.impact.positive or "None", theme))
    table.add_row("⚠️ negative", _md_bold_to_rich(verdict.impact.negative or "None", theme))
    table.add_row("➖ neutral", _md_bold_to_rich(verdict.impact.neutral or "None", theme))
    table.add_row(
        "💡 net gain",
        f"[{highlight}]{_md_bold_to_rich(verdict.net_gain, theme)}[/{highlight}]",
    )
    table.add_row(
        "📋 actions",
        _md_bold_to_rich("\n".join(f"- {item}" for item in verdict.action_items) or "None", theme),
    )

    console.print(
        Panel(table, title=f"[{title_color}]👵 grandma[/{title_color}]", border_style=border)
    )
