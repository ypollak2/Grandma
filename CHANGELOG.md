# Changelog

All notable changes to grandma are documented here.

## [0.1.0] — 2026-06-19

### Added

- **Multi-backend support** — auto-detect from env: claude_cli, anthropic, openai, openai_compatible, ollama, groq, gemini, custom_command
- **Dynamic model names** — no hardcoded vendor model strings; all model selection via `GRANDMA_MODEL` / `GRANDMA_DEEP_MODEL`
- **`.env` support** — `python-dotenv` loads `.env` at startup; `.env.example` with full provider examples
- **MCP server** — `grandma serve` exposes `grandma_summarize` and `grandma_summarize_json` tools
- **Story arc context** — `story_so_far` field tracks conversation arc across turns
- **`**bold**` marker support** — extractor uses Markdown bold; card renders as Rich yellow bold
- **Claude Code Stop hook** — auto-fires after every long response; reads transcript JSONL for history
- **11 IDE integrations** — Claude Code, Codex CLI, Gemini CLI, Cursor, Cline, Continue, Windsurf, Zed, Goose, Aider, OpenHands
- **`install.sh`** — auto-detects installed tools and installs the right adapter
- **Daily mascot rotation** — GitHub Action picks a random grandma portrait from `assets/grandmas/`
- **PyPI publish workflow** — auto-publishes on `v*` tag push via OIDC trusted publishing
- **`--demo` flag** — works with zero config, no stdin required
- **`--json` flag** — outputs raw Verdict JSON
- **`GRANDMA_MODE` env var** — sets default mode for the shell session
- **Helpful error on missing model** — backends that require a model name give a clear error with example fix
