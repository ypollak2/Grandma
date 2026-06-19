# 👵 grandma

> "Explain it like you'd tell grandma."

You know her. She loves you, she read the whole thing, and she is not sitting through six paragraphs of agent confetti to find out whether the test passed. Grandma does not dumb it down. She keeps every fact that matters. She just refuses to waste your afternoon.

`grandma` takes verbose LLM output and gives you the bottom line.

## Before

```text
I inspected the repository and found that the authentication flow now routes through
the new async session adapter. I updated three files, added one regression test, and
confirmed that the login path still returns the expected token shape. There is one
compatibility consideration: the adapter relies on Python 3.9+ typing behavior, so
Python 3.8 users will need to upgrade or pin the old release. Overall, this should
reduce request latency, but the deployment notes should mention the runtime floor.
```

## After

```text
👵 grandma
What happened: Auth moved to the async session adapter.
Bottom line: Faster login path, but Python 3.8 is out.
Do next: Document Python >=3.9 before shipping.
```

## The Modes

`--mode default`

This is the kitchen-table version. Four lines, no ceremony: what happened, the bottom line, and what to do next. Cheap, fast, and enough for most agent output.

`--mode deep`

This is when Grandma puts on the reading glasses. You get the full structured breakdown: what changed, positive impact, negative impact, neutral shifts, net gain, and action items.

`--mode off`

Grandma steps aside. The original text passes through unchanged. Sometimes you really do need the whole casserole.

## Install

```bash
pipx install git+https://github.com/yalipollak/grandma.git
```

## Claude Code Hook

Add grandma as a stop hook so Claude Code responses get the stamp before they hit your eyeballs:

```bash
claude hooks add Stop --command 'grandma --mode "${GRANDMA_MODE:-default}"'
```

Set a default mode when you want:

```bash
export GRANDMA_MODE=deep
```

## CLI

```bash
grandma "long agent output goes here"
cat agent-output.txt | grandma --mode deep
cat agent-output.txt | grandma --json
cat agent-output.txt | grandma --mode off
```

## FAQ

### Does grandma make it dumber?

No dear. Grandma keeps the facts. She removes the fog machine.

### Does default mode include everything?

It includes what you need first: what happened, whether it matters, and what to do. Use `--mode deep` when you need the full table.

### Why is there an off mode?

Because sometimes you want the original output, and Grandma knows when to leave a person alone.

### Which models does it use?

Default mode uses `claude-haiku-4-5-20251001`. Deep mode uses `claude-sonnet-4-6`.

### What API key do I need?

Set `ANTHROPIC_API_KEY`. Grandma is direct, not magic.
