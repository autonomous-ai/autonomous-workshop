Codex product runs now accept `--max-tokens` (default 10,000,000), shared across
stages, native children and resumes. A version-pinned native usage monitor
persists completed-request accounting and stops at the observed cap. Normal
time/turn budgets are superseded for marked runs; gates remain unchanged.
