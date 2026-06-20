"""grandma config — get/set/list persistent configuration."""

from __future__ import annotations

import os
from pathlib import Path

CONFIG_FILE = Path.home() / ".grandma.env"

_KNOWN_KEYS = {
    "backend": "GRANDMA_MODEL_BACKEND",
    "model": "GRANDMA_MODEL",
    "deep_model": "GRANDMA_DEEP_MODEL",
    "api_key": "GRANDMA_API_KEY",
    "base_url": "GRANDMA_BASE_URL",
    "mode": "GRANDMA_MODE",
    "theme": "GRANDMA_THEME",
}


def _read_config() -> dict[str, str]:
    if not CONFIG_FILE.exists():
        return {}
    config: dict[str, str] = {}
    for line in CONFIG_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        config[k.strip()] = v.strip()
    return config


def _write_config(config: dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in sorted(config.items())]
    CONFIG_FILE.write_text("\n".join(lines) + ("\n" if lines else ""))


def _resolve_env_key(key: str) -> str:
    """Accept short alias (backend) or full env var name (GRANDMA_MODEL_BACKEND)."""
    if key in _KNOWN_KEYS:
        return _KNOWN_KEYS[key]
    if key.upper() in _KNOWN_KEYS.values():
        return key.upper()
    return key.upper()


def cmd_set(key: str, value: str) -> None:
    env_key = _resolve_env_key(key)
    config = _read_config()
    config[env_key] = value
    _write_config(config)
    print(f"Set {env_key}={value}  →  {CONFIG_FILE}")


def cmd_get(key: str) -> None:
    env_key = _resolve_env_key(key)
    # Runtime env takes priority over config file
    val = os.getenv(env_key)
    source = "env"
    if val is None:
        val = _read_config().get(env_key)
        source = str(CONFIG_FILE)
    if val is None:
        print(f"{env_key} is not set")
    else:
        print(f"{env_key}={val}  (from {source})")


def cmd_unset(key: str) -> None:
    env_key = _resolve_env_key(key)
    config = _read_config()
    if env_key in config:
        del config[env_key]
        _write_config(config)
        print(f"Unset {env_key}")
    else:
        print(f"{env_key} was not set")


def cmd_list() -> None:
    config = _read_config()
    if not config:
        print(f"No config set. ({CONFIG_FILE})")
        return
    print(f"# {CONFIG_FILE}")
    for k, v in sorted(config.items()):
        # Mask keys that look like secrets
        display = v[:4] + "..." if "KEY" in k and len(v) > 8 else v
        print(f"  {k}={display}")
