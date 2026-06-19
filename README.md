<div align="center">

<!-- Mascot rotates daily — see .github/workflows/rotate-grandma.yml -->
<img src="https://raw.githubusercontent.com/ypollak2/Grandma/main/assets/grandma.png" alt="grandma mascot" width="280" />

# 👵 grandma

**The digest layer for noisy AI agents.**

[![PyPI - Version](https://img.shields.io/pypi/v/grandma)](https://pypi.org/project/grandma)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/grandma)](https://pypi.org/project/grandma)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/grandma)](https://pypi.org/project/grandma)
[![License: MIT](https://img.shields.io/github/license/ypollak2/Grandma)](https://github.com/ypollak2/Grandma/blob/main/LICENSE)
[![CI](https://github.com/ypollak2/Grandma/actions/workflows/ci.yml/badge.svg)](https://github.com/ypollak2/Grandma/actions/workflows/ci.yml)

</div>

---

Your AI agent just wrote 2,000 words. You need the next step. grandma extracts it.

Pipe any LLM output through grandma and get a clean terminal card: **what happened**, **the bottom line**, **what to do next**. No API key needed if you use Claude Code.

```bash
pipx install grandma
grandma --demo
```

---

## Try it in 30 seconds

```bash
# zero-config if you have Claude Code installed
echo "$(cat some-agent-output.txt)" | grandma

# local model via Ollama (no cloud key needed)
GRANDMA_MODEL_BACKEND=ollama GRANDMA_MODEL=llama3.1 grandma --demo

# any provider
GRANDMA_MODEL_BACKEND=openai GRANDMA_MODEL=gpt-4o-mini OPENAI_API_KEY=sk-... grandma --demo
```

---

## Before / After

**Raw agent output (~90 words, ~120 tokens):**

```text
I inspected the repository and found that the authentication flow now routes through
the new async session adapter. I updated three files, added one regression test, and
confirmed that the login path still returns the expected token shape. There is one
compatibility consideration: the adapter relies on asyncio.TaskGroup, so Python 3.10+
is required. Overall, this should reduce request latency by ~70%, but the deployment
notes should mention the runtime floor bump.
```

**After grandma (default mode — ~30 words):**

```
👵 grandma
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 Second turn reviewing an auth refactor PR.

What happened: Auth moved to the async session adapter.
Bottom line:   Faster login path, but Python ≥3.10 required.
Do next:       Update deployment docs before shipping.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**After grandma (deep mode — full impact table):**

```
👵 grandma
┌──────────────┬──────────────────────────────────────────────┐
│ 📖 story arc │ Second turn reviewing an auth refactor PR.   │
│ 👀 happened  │ Auth moved to async session adapter.         │
│ 🧶 changed   │ 3 files, 1 regression test added.            │
│ ✅ positive  │ Login latency reduced ~70%; token shape OK.  │
│ ⚠️  negative  │ Requires Python ≥3.10 (asyncio.TaskGroup).  │
│ ➖ neutral   │ API surface unchanged.                        │
│ 💡 net gain  │ Win — ship it with a runtime floor note.     │
│ 📋 actions   │ - Bump requires-python to >=3.10             │
│              │ - Update deployment docs                      │
└──────────────┴──────────────────────────────────────────────┘
```

---

## Install

```bash
pip install grandma        # pip
pipx install grandma       # isolated (recommended)
uv tool install grandma    # uv
pip install git+https://github.com/ypollak2/Grandma.git  # from source
```

Requires **Python ≥ 3.10**.

---

## Usage

```bash
echo "agent output..." | grandma              # default 3-line card
cat output.txt | grandma --mode deep          # full impact table
cat output.txt | grandma --json               # raw JSON verdict
cat output.txt | grandma --mode off           # passthrough (for hooks)
grandma --demo                                # try it with no input
grandma --demo --mode deep
export GRANDMA_MODE=deep                      # set default for session
```

---

## The modes

| Mode | Output | Best for |
|---|---|---|
| `default` | 3-line card: happened / bottom line / do next | Most agent output |
| `deep` | Full impact table with positive/negative/neutral | PRs, arch decisions, refactors |
| `off` | Passthrough — original text unchanged | Hook pass-through control |

---

## 💸 Why this matters: token savings

Every intermediate agent response fed into the next prompt costs tokens. Grandma compresses the signal.

| | Words | Tokens (approx) |
|---|---|---|
| Raw LLM response | ~400 | ~530 |
| **grandma card** | **~40** | **~55** |
| **Saving** | **~90%** | **~90%** |

Across a 20-turn session: **8,000–12,000 context tokens saved**.

---

## Model backends — bring your own

Grandma auto-detects the best available backend. **No config needed** to get started with Claude Code.

| Priority | When | Backend |
|---|---|---|
| 1 | `GRANDMA_MODEL_BACKEND` set | Explicit provider |
| 2 | `GRANDMA_MODEL` / `GRANDMA_API_KEY` / `GRANDMA_BASE_URL` set | OpenAI-compatible |
| 3 | `OPENAI_API_KEY` set | OpenAI |
| 4 | `GROQ_API_KEY` set | Groq |
| 5 | `GEMINI_API_KEY` / `GOOGLE_API_KEY` set | Gemini |
| 6 | `ANTHROPIC_API_KEY` set | Anthropic SDK |
| 7 | _(nothing set)_ | `claude -p -` (Claude Code subscription, no key) |

**Model names are fully dynamic** — no hardcoded vendor strings in grandma. You choose the model; grandma uses whatever you set. For backends that don't require an explicit model (claude_cli, anthropic SDK), grandma lets the provider pick its own default.

Copy `.env.example` → `.env` and uncomment your provider:

```bash
cp .env.example .env
```

**Ollama (local, no key):**
```env
GRANDMA_MODEL_BACKEND=ollama
GRANDMA_MODEL=llama3.1
GRANDMA_DEEP_MODEL=deepseek-r1
```

**Groq (fast inference):**
```env
GRANDMA_MODEL_BACKEND=groq
GRANDMA_MODEL=llama-3.1-8b-instant
GRANDMA_DEEP_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...
```

**OpenAI:**
```env
GRANDMA_MODEL_BACKEND=openai
GRANDMA_MODEL=gpt-4o-mini
GRANDMA_DEEP_MODEL=gpt-4.1
OPENAI_API_KEY=sk-...
```

**Gemini:**
```env
GRANDMA_MODEL_BACKEND=gemini
GRANDMA_MODEL=gemini-2.5-flash
GRANDMA_DEEP_MODEL=gemini-2.5-pro
GEMINI_API_KEY=AIza...
```

**Any OpenAI-compatible provider (Together, Fireworks, LM Studio, etc.):**
```env
GRANDMA_MODEL_BACKEND=openai_compatible
GRANDMA_BASE_URL=https://your-provider.example.com/v1
GRANDMA_API_KEY=your-key
GRANDMA_MODEL=your-model-name
```

**Custom subprocess (anything that reads stdin):**
```env
GRANDMA_MODEL_BACKEND=custom_command
GRANDMA_MODEL_COMMAND=ollama run llama3.1
```

---

## IDE & agent integrations

Auto-install all detected tools:

```bash
./install.sh
```

| Tool | How | Effect |
|---|---|---|
| **Claude Code** | Stop hook | Auto-card after every long response |
| **Codex CLI** | Stop hook | Auto-card after every long response |
| **Gemini CLI** | AfterAgent hook | Auto-card after every agent turn |
| **Cursor** | MCP + rules | Agent calls `grandma_summarize` automatically |
| **Cline** | MCP + rules | Agent calls `grandma_summarize` after tasks |
| **Continue** | MCP + slash command | On demand or automatic |
| **Windsurf** | MCP + rules | Agent calls `grandma_summarize` automatically |
| **Zed** | MCP (`context_servers`) | Tool in Zed AI panel |
| **Goose** | MCP extension | Tool in Goose sessions |
| **Aider** | pipe wrapper | Pipe aider output through grandma |
| **OpenHands** | pipe wrapper | Pipe headless output through grandma |

**MCP server** — works with any MCP-capable IDE:

```bash
grandma serve
```

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "grandma": { "command": "grandma", "args": ["serve"] }
  }
}
```

Tools exposed: `grandma_summarize(text, mode, story_context)` and `grandma_summarize_json(...)`.

---

## Troubleshooting

**"No model configured for backend X"**
Set `GRANDMA_MODEL=<model-name>` in your `.env`. See `.env.example` for provider examples.

**"claude CLI not found"**
Install [Claude Code](https://claude.ai/code) or set a different backend via `GRANDMA_MODEL_BACKEND`.

**Output is not JSON / parsing error**
The model returned something unexpected. Try `--mode off` to see the raw response, then check your model/backend config.

**Provider returns 401 / 403**
Check that the right API key env var is set for your backend (e.g. `OPENAI_API_KEY`, `GROQ_API_KEY`).

---

## How the mascot rotates

Each portrait in `assets/grandmas/` was generated with Gemini Image.
A [daily GitHub Action](.github/workflows/rotate-grandma.yml) picks one at random and replaces `assets/grandma.png` with a `[skip ci]` commit.

Want to add your own grandma? Drop a PNG into `assets/grandmas/` and open a PR.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details. Quick start:

```bash
git clone https://github.com/ypollak2/Grandma.git
cd Grandma
pip install -e ".[dev]"
pytest tests/        # run tests
ruff check src       # lint
```

Good first issues are tagged [`good first issue`](https://github.com/ypollak2/Grandma/labels/good%20first%20issue).

---

## FAQ

**Does grandma make it dumber?**
No dear. She keeps the facts. She removes the fog machine.

**What model does it use?**
Whatever you configure via `GRANDMA_MODEL`. There are no hardcoded model names. If you set nothing, `claude_cli` lets Claude Code pick, and `anthropic` lets the SDK pick its default. API-based backends (openai, groq, ollama, gemini) require `GRANDMA_MODEL` to be set.

**Why is there an off mode?**
Because hooks need a clean passthrough option. When `GRANDMA_MODE=off`, grandma becomes transparent — useful for temporarily disabling the Stop hook without unregistering it.

**What's the `story_so_far` line?**
Grandma reads the last 3 turns of the conversation to track where you are in the arc. Turn 8 of the same auth bug? She'll say so. This is the dementia prevention feature.

**Why Python ≥ 3.10?**
The `mcp` package (used for `grandma serve`) requires 3.10+.

**How is this different from llm / fabric / shell_gpt?**
`llm` gives you model access. `fabric` gives you prompt patterns. `shell_gpt` gives you a REPL. grandma does none of those things. It sits at the *output* end — it is the digest layer you add after any of those tools to stop reading 2,000-word agent responses.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

<div align="center">
<sub>Made with 💜 by <a href="https://github.com/ypollak2">Yali Pollak</a> · <a href="https://github.com/ypollak2/Grandma/blob/main/LICENSE">MIT License</a> · <a href="https://pypi.org/project/grandma">PyPI</a></sub>
</div>
