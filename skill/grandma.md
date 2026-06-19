# Grandma

Install first:

```bash
pipx install git+https://github.com/yalipollak/grandma.git
```

Enable this skill when you want Claude Code responses piped through `grandma`: a short bottom-line stamp for verbose LLM output.

Grandma does not dumb things down. She keeps the facts and cuts the rambling.

## Usage

Pipe the final response through:

```bash
grandma --mode "${GRANDMA_MODE:-default}"
```

Use `GRANDMA_MODE=default` for the compact stamp, `GRANDMA_MODE=deep` for the full structured table, and `GRANDMA_MODE=off` for passthrough.

## Behavior

- Default mode returns the key facts: what happened, net gain, and action items.
- Deep mode returns the full verdict with positive, negative, and neutral impact.
- Off mode returns the original text unchanged.
- If the output is already short and clear, keep it short and clear.
