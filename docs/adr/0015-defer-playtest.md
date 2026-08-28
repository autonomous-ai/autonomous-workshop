# ADR 0015: Defer Playtest from the executable fast path

- Status: Accepted
- Date: 2026-08-27
- Supersedes: ADR 0014's requirement that Playtest pass before Release
- Superseded for new runs by: ADR 0016 selectable effort routes

## Context

Workshop needs a short, usable end-to-end path now: turn a Wish into
ready-to-print CAD and a printable manual, then publish both through Factory.
The Playtest design and its product-specific evidence loops are not ready to be
a dependable release gate and currently make real-user runs substantially
slower.

Skipping a stage must not become a false pass. A missing Playtest cannot be
represented by model prose, an empty evidence tree, or a fabricated successful
receipt.

## Decision

New product runs use:

```text
Wish -> Match -> Invent -> Make -> Release

Release -- handoff to Operations --> Printing -> Deliver -> Review
```

Make must pass the host's full-tier CAD verifier, including wall-thickness and
print-ready eligibility. Release replays that verifier on the same sealed Made
revision, validates `MANUAL.pdf`, and publishes the exact CAD and manual through
Factory with authenticated hash readback.

Release schema v3 / product schema v5 explicitly records
`playtest_status: not-run`. The package contains canonical
`PLAYTEST-NOT-RUN.json`; its hash is used wherever the existing Factory effect
protocol requires a playtest-evidence identity. Claims contain only the
truthful omission record and no test claims. Direct Release does not create
`VERIFICATION.json`.

The materialized `direct-release-v1.md` marker freezes this choice per run.
Runs created before this decision keep their older Make–Playtest protocol and
resume with their original materialized finalizer and gates.

## Consequences

- Real-user runs reach publishable CAD and manual output in four native stages.
- Neither the public page nor the manual may imply that Playtest, physical
  printing, fit, durability, or human evaluation occurred.
- Playtest contracts and compatibility code remain for frozen historical runs
  and future work, but they are not part of new-run lifecycle order.
- Reintroducing Playtest requires a later ADR, a new immutable capability
  marker, and migration-safe tests; it must not reinterpret existing releases.
