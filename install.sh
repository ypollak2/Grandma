#!/usr/bin/env bash
# grandma install — detects AI tools present and installs the right adapter
set -euo pipefail

GRANDMA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRANDMA_BIN="$(command -v grandma 2>/dev/null || echo "")"

if [ -z "$GRANDMA_BIN" ]; then
  echo "❌ grandma not found in PATH — install first: pip install grandma"
  exit 1
fi

installed=0

# ── Claude Code ────────────────────────────────────────────────────────────────
if command -v claude &>/dev/null && [ -d "$HOME/.claude" ]; then
  HOOK_DEST="$HOME/.claude/bin/grandma-hook"
  mkdir -p "$HOME/.claude/bin"
  cp "$GRANDMA_DIR/integrations/claude-code/hook.py" "$HOOK_DEST"
  chmod +x "$HOOK_DEST"

  SETTINGS="$HOME/.claude/settings.json"
  if [ -f "$SETTINGS" ]; then
    # Check if grandma hook already present
    if ! grep -q "grandma-hook" "$SETTINGS" 2>/dev/null; then
      python3 - "$SETTINGS" "$HOOK_DEST" <<'PYEOF'
import json, sys
path, hook_path = sys.argv[1], sys.argv[2]
with open(path) as f:
    cfg = json.load(f)
cfg.setdefault("hooks", {}).setdefault("Stop", [])
cfg["hooks"]["Stop"].append({
    "matcher": "",
    "hooks": [{"type": "command", "command": f"python3 {hook_path}", "timeout": 140, "background": True}]
})
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
print(f"  ✅ Claude Code Stop hook registered in {path}")
PYEOF
    else
      echo "  ℹ️  Claude Code: grandma hook already present"
    fi
  fi
  ((installed++)) || true
  echo "✅ Claude Code — hook installed at $HOOK_DEST"
fi

# ── Codex CLI ──────────────────────────────────────────────────────────────────
if command -v codex &>/dev/null && [ -d "$HOME/.codex" ]; then
  HOOK_DEST="$HOME/.codex/grandma-hook.py"
  cp "$GRANDMA_DIR/integrations/codex-cli/hook.py" "$HOOK_DEST"
  chmod +x "$HOOK_DEST"
  echo "✅ Codex CLI — hook copied to $HOOK_DEST"
  echo "   Add to ~/.codex/config.json: hooks.Stop[].command = \"python3 $HOOK_DEST\""
  ((installed++)) || true
fi

# ── Gemini CLI ─────────────────────────────────────────────────────────────────
if command -v gemini &>/dev/null && [ -d "$HOME/.gemini" ]; then
  HOOK_DEST="$HOME/.gemini/grandma-hook.py"
  cp "$GRANDMA_DIR/integrations/gemini-cli/hook.py" "$HOOK_DEST"
  chmod +x "$HOOK_DEST"
  echo "✅ Gemini CLI — hook copied to $HOOK_DEST"
  echo "   Add to ~/.gemini/settings.json: hooks.AfterAgent[].command = \"python3 $HOOK_DEST\""
  ((installed++)) || true
fi

# ── Cursor ─────────────────────────────────────────────────────────────────────
if [ -d "$HOME/.cursor" ] || [ -d "$HOME/Library/Application Support/Cursor" ]; then
  CURSOR_DIR="${CURSOR_DIR:-$HOME/.cursor}"
  mkdir -p "$CURSOR_DIR/rules"
  cp "$GRANDMA_DIR/integrations/cursor/.cursor/rules/grandma.mdc" "$CURSOR_DIR/rules/grandma.mdc"
  echo "✅ Cursor — rules file installed at $CURSOR_DIR/rules/grandma.mdc"
  echo "   Add grandma MCP server to Cursor settings: grandma serve"
  ((installed++)) || true
fi

# ── Windsurf ───────────────────────────────────────────────────────────────────
if [ -d "$HOME/.codeium/windsurf" ] || command -v windsurf &>/dev/null; then
  WIND_RULES="$HOME/.codeium/windsurf/memories/grandma.md"
  mkdir -p "$(dirname "$WIND_RULES")"
  cp "$GRANDMA_DIR/integrations/windsurf/.windsurfrules" "$WIND_RULES"
  echo "✅ Windsurf — rules installed at $WIND_RULES"
  echo "   Add grandma MCP server to Windsurf MCP settings: grandma serve"
  ((installed++)) || true
fi

# ── Zed ────────────────────────────────────────────────────────────────────────
if command -v zed &>/dev/null || [ -d "$HOME/.config/zed" ]; then
  echo "✅ Zed — merge integrations/zed/settings-snippet.json into ~/.config/zed/settings.json"
  ((installed++)) || true
fi

# ── Aider ──────────────────────────────────────────────────────────────────────
if command -v aider &>/dev/null; then
  BIN_DIR="$(dirname "$GRANDMA_BIN")"
  cp "$GRANDMA_DIR/integrations/aider/grandma-aider" "$BIN_DIR/grandma-aider"
  chmod +x "$BIN_DIR/grandma-aider"
  echo "✅ Aider — wrapper installed as grandma-aider (use instead of aider)"
  ((installed++)) || true
fi

# ── OpenHands ──────────────────────────────────────────────────────────────────
if command -v openhands &>/dev/null; then
  BIN_DIR="$(dirname "$GRANDMA_BIN")"
  cp "$GRANDMA_DIR/integrations/openhands/grandma-openhands" "$BIN_DIR/grandma-openhands"
  chmod +x "$BIN_DIR/grandma-openhands"
  echo "✅ OpenHands — wrapper installed as grandma-openhands"
  ((installed++)) || true
fi

# ── MCP-compatible editors (Cline, Continue, Goose) ───────────────────────────
echo ""
echo "📋 For MCP-native tools (Cline, Continue, Goose), add this MCP server config:"
echo "   command: grandma  args: [\"serve\"]"
echo "   See integrations/cline/.mcp.json, integrations/continue/config-snippet.json,"
echo "   and integrations/goose/.goose/config.yaml for copy-paste snippets."

echo ""
if [ "$installed" -eq 0 ]; then
  echo "⚠️  No supported AI tools detected. Install grandma manually per tool."
else
  echo "🎉 Done — grandma integrated with $installed tool(s)."
fi
