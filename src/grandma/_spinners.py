"""Maps grandma's 20 CSS loaders to Rich terminal spinners.

CSS animations cannot run in a terminal, but every loader's motion concept
translates to a frame sequence. Custom spinners are injected into Rich's own
SPINNERS registry so console.status(spinner=name) works transparently.
"""

from __future__ import annotations

import os

from rich._spinners import SPINNERS as _S

# ── register grandma-specific frame sequences ──────────────────────────────
_S["grandma_breath"] = {"interval": 400, "frames": ["·", "○", "◯", "○", "·", "○"]}
_S["grandma_heartbeat"] = {"interval": 220, "frames": ["♡", "♥", "♥", "♡", "♡"]}
_S["grandma_ripple"] = {"interval": 280, "frames": ["·", "∘", "○", "◯", "○", "∘"]}
_S["grandma_orbit"] = {"interval": 120, "frames": ["◜●", "◠●", "◝●", "◞●", "◡●", "◟●"]}
_S["grandma_proof"] = {
    "interval": 180,
    "frames": [
        "▁",
        "▂",
        "▃",
        "▄",
        "▅",
        "▆",
        "▇",
        "█",
        "▇",
        "▆",
        "▅",
        "▄",
        "▃",
        "▂",
    ],
}
_S["grandma_quilt"] = {"interval": 400, "frames": ["▪▫▪▫", "▫▪▫▪"]}
_S["grandma_merge"] = {"interval": 220, "frames": ["● ·", "●·", "●", "·●", "· ●"]}
_S["grandma_drift"] = {
    "interval": 220,
    "frames": [
        "● ● ●",
        "● ●●",
        " ●●●",
        "●●● ",
        "●● ●",
    ],
}

# ── loader name → Rich spinner name ────────────────────────────────────────
SPINNER_MAP: dict[str, str] = {
    "breath": "grandma_breath",
    "yarn": "moon",
    "simmer": "dots",  # default — classic Braille bubbling
    "knead": "arc",
    "proof": "grandma_proof",
    "rock": "line",
    "steep": "grandma_ripple",
    "merge": "grandma_merge",
    "heartbeat": "grandma_heartbeat",
    "wander": "bouncingBall",
    "settle": "dots2",
    "orbit": "grandma_orbit",
    "wobble": "arc",
    "digest": "dots",
    "quilt": "grandma_quilt",
    "ripple": "grandma_ripple",
    "drip": "line",
    "crawl": "bouncingBall",
    "wind": "dots12",
    "drift": "grandma_drift",
}

_DEFAULT = "simmer"
SPINNER_NAMES: tuple[str, ...] = tuple(SPINNER_MAP)


def get_spinner(name: str | None = None) -> str:
    """Return a Rich spinner name for the given grandma loader name (or env/default)."""
    n = (name or os.getenv("GRANDMA_SPINNER", _DEFAULT)).lower()
    return SPINNER_MAP.get(n, SPINNER_MAP[_DEFAULT])
