<div align="center">

<!-- Mascot rotates daily — see .github/workflows/rotate-grandma.yml -->
<img src="https://raw.githubusercontent.com/ypollak2/Grandma/main/assets/grandma.png" alt="grandma mascot" width="320" />

# 👵 grandma

**Explain it like you'd tell grandma.**

[![PyPI - Version](https://img.shields.io/pypi/v/grandma)](https://pypi.org/project/grandma)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/grandma)](https://pypi.org/project/grandma)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/grandma)](https://pypi.org/project/grandma)
[![License: MIT](https://img.shields.io/github/license/ypollak2/Grandma)](https://github.com/ypollak2/Grandma/blob/main/LICENSE)
[![CI](https://github.com/ypollak2/Grandma/actions/workflows/ci.yml/badge.svg)](https://github.com/ypollak2/Grandma/actions/workflows/ci.yml)

</div>

---

You know her. She loves you, she read the whole thing, and she is **not** sitting through six paragraphs of agent confetti to find out whether the test passed.

Grandma does not dumb it down. She keeps every fact that matters. She just refuses to waste your afternoon.

`grandma` takes verbose LLM output and distils it to three lines: **what happened**, **the bottom line**, and **what to do next**.

---

## 💸 Token savings

Every time you read a raw LLM response, you pay in attention — or in tokens if you pipe it into another model.

| | Words | Reading tokens | Cost to re-read |
|---|---|---|---|
| Raw LLM response | ~400 | ~530 | 100% |
| **grandma card** | **~40** | **~55** | **~10%** |
| **Savings** | | | **~90% fewer tokens** |

**Why this matters:**

- In agent loops, every intermediate response fed back into context costs tokens. Grandma compresses the signal.
- In multi-step workflows (plan → code → review → deploy), each step can save 400–500 tokens of context bloat.
- Deep mode trades a bit more output for full structured data — still 70–80% smaller than the raw response.
- Across a 20-turn session, grandma typically saves **8,000–12,000 context tokens**.

---

## Before / After

**Raw LLM output (~90 words, ~120 tokens):**

```text
I inspected the repository and found that the authentication flow now routes through
the new async session adapter. I updated three files, added one regression test, and
confirmed that the login path still returns the expected token shape. There is one
compatibility consideration: the adapter relies on asyncio.TaskGroup, so Python 3.10+
is required. Overall, this should reduce request latency by ~70%, but the deployment
notes should mention the runtime floor bump.
```

**After grandma (default mode — ~30 words, ~40 tokens):**

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

## Requirements

- **Python ≥ 3.10**
- One of: Claude Code subscription (no API key needed) or `ANTHROPIC_API_KEY`

---

## Install

```bash
# pip
pip install grandma

# pipx (isolated, recommended for CLI tools)
pipx install grandma

# uv
uv tool install grandma

# from source
pip install git+https://github.com/ypollak2/Grandma.git
```

---

## Usage

**Pipe any text through grandma:**

```bash
echo "long agent output..." | grandma
cat response.txt | grandma --mode deep
cat response.txt | grandma --json        # raw JSON verdict
cat response.txt | grandma --mode off    # passthrough
```

**Demo (no API key needed):**

```bash
grandma --demo
grandma --demo --mode deep
```

**Set a default mode for your shell session:**

```bash
export GRANDMA_MODE=deep
```

---

## The Modes

| Mode | What you get | Model | Best for |
|---|---|---|---|
| `default` | 3-line card: happened / bottom line / do next | Haiku | Most agent output |
| `deep` | Full impact table with positive/negative/neutral | Sonnet | PRs, arch decisions, refactors |
| `off` | Passthrough — original text unchanged | — | When you need the whole casserole |

---

## Model backends

Grandma auto-detects the best available backend. No configuration needed to get started.

| Priority | Condition | Backend used |
|---|---|---|
| 1 | `GRANDMA_MODEL_BACKEND` set | Explicit provider |
| 2 | `GRANDMA_MODEL` / `GRANDMA_API_KEY` / `GRANDMA_BASE_URL` set | OpenAI-compatible |
| 3 | `OPENAI_API_KEY` set | OpenAI |
| 4 | `GROQ_API_KEY` set | Groq |
| 5 | `GEMINI_API_KEY` / `GOOGLE_API_KEY` set | Gemini |
| 6 | `ANTHROPIC_API_KEY` set | Anthropic SDK |
| 7 | _(nothing set)_ | `claude -p -` (Claude Code subscription) |

Copy `.env.example` to `.env` and uncomment what you need:

```bash
cp .env.example .env
```

**Ollama (local, no key):**
```env
GRANDMA_MODEL_BACKEND=ollama
GRANDMA_MODEL=llama3.1
GRANDMA_DEEP_MODEL=deepseek-r1
```

**Groq (fast cloud inference):**
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

**Any OpenAI-compatible provider:**
```env
GRANDMA_MODEL_BACKEND=openai_compatible
GRANDMA_BASE_URL=https://your-provider.example.com/v1
GRANDMA_API_KEY=your-key
GRANDMA_MODEL=your-model-name
```

---

## IDE & agent integrations

Grandma works anywhere LLMs produce text. One-liner install for all detected tools:

```bash
./install.sh
```

| Tool | Integration | What happens |
|---|---|---|
| **Claude Code** | Stop hook (native) | Auto-card after every long response |
| **Codex CLI** | Stop hook (native) | Auto-card after every long response |
| **Gemini CLI** | AfterAgent hook (native) | Auto-card after every agent turn |
| **Cursor** | MCP + `.cursor/rules` | Agent calls `grandma_summarize` after long replies |
| **Cline** | MCP + rules | Agent calls `grandma_summarize` after tasks |
| **Continue** | MCP + `/grandma` slash command | On demand or automatic |
| **Windsurf** | MCP + `.windsurfrules` | Agent calls `grandma_summarize` after long replies |
| **Zed** | MCP (`context_servers`) | Tool available in Zed AI panel |
| **Goose** | MCP extension | Tool available in Goose sessions |
| **Aider** | `grandma-aider` wrapper | Pipe aider output through grandma |
| **OpenHands** | `grandma-openhands` wrapper | Pipe headless output through grandma |

**MCP server (any MCP-capable IDE):**

```bash
grandma serve
```

Exposes two tools:
- `grandma_summarize(text, mode, story_context)` → plain-text card
- `grandma_summarize_json(text, mode, story_context)` → structured dict

Add to any `.mcp.json`:

```json
{
  "mcpServers": {
    "grandma": { "command": "grandma", "args": ["serve"] }
  }
}
```

---

## How the mascot rotates

Each portrait in `assets/grandmas/` was generated with Gemini Image.  
A [daily GitHub Action](.github/workflows/rotate-grandma.yml) picks one at random and replaces `assets/grandma.png`.  
The README always shows the current winner. No JS. No CDN. No infrastructure.

Want to add your own grandma? Drop a PNG into `assets/grandmas/` and open a PR.

---

## Contributing

```bash
git clone https://github.com/ypollak2/Grandma.git
cd Grandma
pip install -e ".[dev]"
pytest tests/        # run tests
ruff check src       # lint
```

---

## FAQ

**Does grandma make it dumber?**  
No dear. She keeps the facts. She removes the fog machine.

**Does default mode include everything?**  
It includes what you need first. Use `--mode deep` when you need the full table.

**Why is there an off mode?**  
Because sometimes you want the original, and grandma knows when to leave a person alone.

**What's the `story_so_far` line?**  
Grandma reads the last 3 turns of the conversation to understand where you are in the arc.  
If you are on turn 8 of debugging the same auth bug, she will tell you. This is the dementia prevention feature.

**Which models does it use?**  
Default: `claude-haiku-4-5-20251001`. Deep: `claude-sonnet-4-6`.  
Both run on your Claude Code subscription — no extra key needed.

**Why Python ≥ 3.10?**  
The `mcp` package (used for `grandma serve`) requires 3.10+.

---

<div align="center">
<sub>Made with 💜 by <a href="https://github.com/ypollak2">Yali Pollak</a> · <a href="https://github.com/ypollak2/Grandma/blob/main/LICENSE">MIT License</a> · <a href="https://pypi.org/project/grandma">PyPI</a></sub>
</div>
