# ADR 0031: Bind the deep profile and bound first proof

- Status: Superseded for new runs by ADR 0032
- Date: 2026-08-30
- Owners: Runtime, workflow, and product-run protocol maintainers
- Supersedes for new runs: ADR 0030's `deep-economics-v2` profile

## Context

The first Quest production run using deep-v2 created a distinctive Three-Sky
Seed concept in 15m48s. Invent specified three captive 120-degree sky states,
three printable parts, a volumetric seed silhouette, and an exact early
mechanism/form falsifier.

Make nevertheless persisted no product file during its entire first 30-minute
turn. After the timeout, the fixed recovery instruction resumed the same Goal
and wrote the requested `review/early-proof/` source and proof runner within
about 4.5 minutes. Prompt ordering alone therefore did not control the expensive
period: the recoverable boundary did.

Inspection also found that deep-v2's promised stage shaping was not effective
within one CLI invocation. The host constructed one launcher at the initial
Invent checkpoint and reused it after advancing to Make, so Make inherited
Invent's high reasoning setting. Constructing a medium launcher only on a later
operator resume would conflict with the Codex session checkpoint, because that
checkpoint correctly bound the exact original per-turn runtime configuration.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v3.md`.

- One immutable profile-file hash becomes the persistent session's runtime
  profile identity. Model, CLI, sandbox, permissions, environment, paths, and
  that exact profile identity remain checkpoint-bound.
- The host constructs the Codex launcher for each native turn from the current
  lifecycle checkpoint. Invent uses high reasoning; Make, Playtest, and Release
  use medium. Every turn keeps the 24k compaction ceiling.
- The first Make turn for each exact Make checkpoint has a 12-minute boundary.
  If it does not finalize, the normal bounded recovery resumes the same thread,
  Goal, stage subject, and workspace with a 30-minute turn.
- Other normal turns retain 30 minutes, and one CLI invocation retains the
  eight-turn cap.
- The direct Make instruction and product-run reference still require the
  smallest exact causal/kinematic proof plus neutral held/signature blockout
  under `review/early-proof/` before the complete part tree.

The whole-profile identity permits only host-selected turn settings belonging
to the frozen profile. It does not weaken the stable security configuration or
give product-run code authority over runtime policy. The boundary is resource
control, not a stage, Goal, agent, semantic judge, retry loop, or gate.

Deep-v2 runs keep the effective all-high configuration bound when their thread
started, so stopped historical sessions remain resumable without same-version
policy drift. Deep-v1 and older materialized runs likewise keep their prior
marker and runtime binding.

## Consequences

- High reasoning is actually spent on concept selection, while artifact-heavy
  stages actually use medium reasoning.
- A silent first Make turn consumes at most 12 minutes before receiving the
  same proven critical-path recovery instruction.
- A productive Make may still complete inside the short first turn; a larger
  one retains a normal recovery window and every existing quality gate.
- The run still uses one persistent Codex thread and one active Goal at a time.
- A fresh production Quest and Forge run must verify quality, elapsed time,
  token telemetry, exact proof preservation, and terminal publication.

## Verification

- Runtime tests prove high-to-medium turn-policy changes resume one exact
  thread only when their immutable profile identity matches.
- Drift of the profile identity still fails before a resume launches.
- Workflow tests prove v3 selects high for Invent, medium afterward, 12 minutes
  for the initial Make boundary, and 30 minutes otherwise.
- Compatibility tests retain deep-v2, deep-v1, Spark, and unmarked behavior.
- Full tests pass before a v3 production run is started.
