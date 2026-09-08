Codex product runs now accept `--max-tokens`, shared across stages, native
children and resumes; the default is 30,000,000 (raised from the initial
10,000,000, see `default-product-token-cap.changed.md`). A version-pinned
native usage monitor persists completed-request accounting and stops at the
observed cap. Normal time/turn budgets are superseded for marked runs; every
native turn keeps a 60-minute emergency watchdog; gates remain unchanged.
