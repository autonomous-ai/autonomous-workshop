Budgeted Codex Spark v3 now explicitly limits each native turn to 20 minutes,
including same-session resumes. This replaces the September 3 one-hour limit
for this budgeted profile. Command budgets also preserve shorter launcher
boundaries. Unbudgeted sessions retain their existing policy bindings.
The complete launcher-path regression asserts 1,200 seconds independently of
the legacy timeout constant. This change does not bound total time across
explicit resumes or eliminate expensive CAD repair work.
