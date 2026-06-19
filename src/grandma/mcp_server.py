"""MCP server — exposes grandma as a tool any MCP-aware IDE can call."""

import re
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from grandma.extractor import extract
from grandma.models import Mode, Verdict

mcp = FastMCP(
    "grandma",
    instructions="Explain it like you'd tell grandma — compact bottom-line cards from verbose LLM output.",
)


def _verdict_to_text(verdict: Verdict, mode: Mode) -> str:
    """Render verdict as plain text (no ANSI) suitable for IDE tool responses."""

    def strip_md_bold(s: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"\1", s)

    lines = ["👵 grandma", "━" * 40]
    if verdict.story_so_far:
        lines.append(f"📖 {verdict.story_so_far}")
        lines.append("")
    lines.append(f"What happened: {strip_md_bold(verdict.what_happened)}")
    lines.append(f"Bottom line:   {strip_md_bold(verdict.net_gain)}")
    if verdict.action_items:
        lines.append(f"Do next:       {'; '.join(strip_md_bold(a) for a in verdict.action_items)}")
    if mode is Mode.DEEP:
        lines.append("")
        lines.append(f"Changed:   {strip_md_bold(verdict.what_changed)}")
        if verdict.impact.positive:
            lines.append(f"✅ {strip_md_bold(verdict.impact.positive)}")
        if verdict.impact.negative:
            lines.append(f"⚠️  {strip_md_bold(verdict.impact.negative)}")
        if verdict.impact.neutral:
            lines.append(f"➖ {strip_md_bold(verdict.impact.neutral)}")
    lines.append("━" * 40)
    return "\n".join(lines)


@mcp.tool()
def grandma_summarize(
    text: Annotated[str, Field(description="The verbose LLM output to summarise.")],
    mode: Annotated[
        str, Field(description="'default' (compact 3-liner) or 'deep' (full impact table).")
    ] = "default",
    story_context: Annotated[
        Optional[str],
        Field(description="Brief description of the conversation arc so far, if known."),
    ] = None,
) -> str:
    """
    Summarise verbose LLM output into a compact grandma card.

    Returns plain-text card: What happened / Bottom line / Do next.
    Call after any long LLM response to get the bottom line.
    """
    history = [story_context] if story_context else None
    result = extract(text, mode=Mode(mode), history=history)
    if isinstance(result, str):
        return result
    return _verdict_to_text(result, Mode(mode))


@mcp.tool()
def grandma_summarize_json(
    text: Annotated[str, Field(description="The verbose LLM output to summarise.")],
    mode: Annotated[str, Field(description="'default' or 'deep'.")] = "default",
    story_context: Annotated[
        Optional[str], Field(description="Optional conversation arc context.")
    ] = None,
) -> dict:
    """
    Summarise verbose LLM output and return a structured JSON verdict.

    Returns: {what_happened, net_gain, action_items, story_so_far, impact?, what_changed?}
    """
    history = [story_context] if story_context else None
    result = extract(text, mode=Mode(mode), history=history)
    if isinstance(result, str):
        return {"raw": result}
    return result.model_dump()


def serve() -> None:
    mcp.run()
