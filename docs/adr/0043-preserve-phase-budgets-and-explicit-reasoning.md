# ADR 0043: Preserve phase boundaries under command budgets

- Status: Accepted for new runs; production quality improvement unproven
- Date: 2026-09-07

The budget wrapper replaced short native phase boundaries with a 60-minute
remaining-budget ceiling and dropped an explicitly configured model provider.
This allowed an early proof to spend final-build time and could route a model
through the wrong provider.

New runs freeze `budgets-v2.md`. Their Codex timeout is the minimum of the
phase timeout and remaining native-work budget; Spark is capped at 20 minutes.
V1-only runs retain their original budget policy and identity. Provider,
model, reasoning, compaction, and binary survive launcher reconstruction.

Operators may select `--reasoning-effort` for Codex explicitly. It applies to
the invocation and must be repeated on resume; omission retains the effort
profile. Existing private runtime-policy drift checks still apply. Other
Managers reject this option rather than ignoring it.

Make instructions bring the cheap held-form/signature check to Spark, require
geometry-based local checks, and preserve the actual blind response before
reveal. These are native-agent work instructions, not a host semantic judge.
No CAD or publication gate is removed. A real completed comparison is still
needed to establish better product quality or lower end-to-end cost.

Budget counters measure native work, not all host verification/publication
time. They reset on explicit resume; this change does not claim a wall-clock
deadline for the entire product lifecycle.

The first local Astra run exposed a prerequisite failure: Homebrew Python's
framework binary and launcher symlink traversal were outside the admitted
runtime, and importing CAD also needed Python's linked SQLite library. The
runtime now resolves the framework install name against its framework prefix,
walks the launcher symlinks, and inspects the trusted stdlib Mach-O dependencies
with bounded `otool` calls. Only exact libraries and their runtime directories
are readable; host state and effect credentials remain denied. An exact
predecessor-policy comparison admits this additive runtime repair on resume;
arbitrary permission or environment drift remains rejected.
