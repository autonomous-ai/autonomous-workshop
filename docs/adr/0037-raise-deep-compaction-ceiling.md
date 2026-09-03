# ADR 0037: Raise the deep compaction ceiling to 256k

- Status: Accepted
- Date: 2026-08-31
- Owners: Runtime, workflow, and product-run protocol maintainers
- Supersedes for new runs: ADR 0036's `deep-economics-v8` profile

## Context

A real Forge Invent turn using the default `gpt-5.6-sol` session compacted
multiple times despite a short wall-clock duration. The observed 24k ceiling,
not the model's available context capacity, forced those compactions. The
resulting loss of working context makes the normal same-session recovery less
useful and is contrary to the deep route's evidence-heavy Invent and Make work.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v9.md`.

- V9 retains v8's reasoning levels, 20/10-minute Invent boundaries, 16-minute
  medium Make proof runway, 30-minute final Make boundary, eight-turn command
  cap, batched proof startup, deferred broad CAD skill, exact CAD command
  shapes, and every product gate.
- The automatic compaction ceiling is 256,000 tokens at every deep stage.
- The v9 file hash is the entire current deep runtime-profile identity. The
  launcher selects 256k only when that exact file is materialized.

## Compatibility and verification

Deep-v8 and every older profile remain recognized with their original 24k
ceiling, prompts, timeouts, and hashes. Tests prove v9 selects 256k while v8,
v7, v4, v3, and v2 retain 24k. The host still resumes only the exact bound
native session and never promotes a historical run to v9.
