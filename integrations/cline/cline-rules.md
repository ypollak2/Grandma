# grandma integration for Cline

After completing any multi-step task or writing a response longer than 80 words,
call `grandma_summarize` with your response text to show the user a compact
bottom-line card.

- Use `mode="default"` for standard replies (What happened / Bottom line / Do next).
- Use `mode="deep"` for PRs, architecture decisions, multi-file changes.
- Pass `story_context` if you know the conversation arc.
