# Contributing to grandma

Thanks for wanting to help. This doc covers how to contribute code, integrations, and bug reports.

## Quick start

```bash
git clone https://github.com/ypollak2/Grandma.git
cd Grandma
pip install -e ".[dev]"
pytest tests/        # all tests must pass
ruff check src       # no lint errors
```

## What to work on

Check [open issues](https://github.com/ypollak2/Grandma/issues) — anything tagged `good first issue` is a good starting point.

High-value areas:

- **`grandma doctor`** — a `grandma doctor` CLI command that checks backend availability, env vars, model config, and prints a diagnostic report
- **Session digest** — `grandma replay` that reads the last Claude/Codex/aider session log and produces a day summary card
- **Terminal GIF demo** — a recorded demo showing before/after that can live at the top of the README
- **New integrations** — any IDE or agent tool not yet in `integrations/`
- **Test coverage** — CLI exit codes, backend priority, malformed model output, hook transcript extraction

## Adding a new backend

1. Add the backend name to `_BACKEND_MODEL_REQUIRED` in `src/grandma/extractor.py`
2. Add detection logic in `_resolve_backend()` (what env var signals this backend?)
3. Add a `_extract_via_<name>()` function
4. Wire it into the `extract()` backend dispatch block
5. Add examples to `.env.example` and the README backend table
6. Add at least one test in `tests/test_extractor.py`

## Adding a new IDE integration

1. Create `integrations/<tool-name>/` with a `README.md` explaining setup
2. Add the integration method and effect to the README integrations table
3. If the tool supports hooks or MCP, add the config snippet
4. Update `install.sh` to detect and install it

## Tests

- Run `pytest tests/` before opening a PR
- New features need at least one test
- Prefer testing behavior over implementation (use `monkeypatch` for env vars, mock for SDK calls)

## Code style

- Follow existing patterns in `src/grandma/`
- Type hints on all public functions
- No hardcoded model names or vendor strings
- No comments that describe what the code does — only *why* if it's non-obvious

## PR checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] No lint errors (`ruff check src`)
- [ ] `.env.example` updated if new env vars added
- [ ] README updated if user-facing behavior changed
- [ ] Descriptive commit message

## Reporting bugs

Open an issue with:
- Your OS and Python version
- The backend you're using (`GRANDMA_MODEL_BACKEND` value)
- The command you ran
- The error or unexpected output
