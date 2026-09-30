# Context compaction v1

This immutable marker gives a Claude Code Manager a 256,000-token automatic
context-compaction window for a new run, instead of the model's whole context
window. Claude Code compacts a little short of that window, leaving room for
the summary. A Codex Manager keeps the ceiling its economics profile names.
Runs frozen without this marker keep their policy on resume.

The window is working memory, not permission to read more. Durable state
belongs in the run's notes and artifacts, not only in conversation history,
because a compaction keeps a summary and drops the rest.
