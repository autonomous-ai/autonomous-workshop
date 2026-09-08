- History (2026-09-03, superseded in part): the native turn boundary was
  raised to 60 minutes for new Spark runs (was 20) and for the normal Forge
  and Quest turn (was 30) because healthy Make turns timed out on shared
  hosts; short first-turn handoffs (Invent 20/10, Make proof 16, final Make
  15) and the 15-minute Daydream turn were unchanged, and each budgeted step
  got 120 minutes with 6 hours per toy. Today's rule (ADR 0049, ADR 0051):
  token-budgeted Codex runs keep only that 60-minute per-turn emergency
  watchdog; the profile minutes are pacing, not enforced clocks. Runs frozen
  earlier keep their original boundaries.
