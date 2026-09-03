# ADR 0027: Bind every printable before visual review

- Status: Accepted
- Date: 2026-08-30
- Owners: Make, CAD skill, product-run instruction, and native finalizer maintainers
- Relates to: ADR 0022 (blind review), ADR 0026 (Wish-form preservation)
- Supersedes for new runs: ADR 0026's advisory single-draft preflight and schema-v5 review

## Context

Moonseed Bloom was a real Forge production run. Invent sealed a creative
six-part kinetic concept in one turn. Make then spent a visual review before the
integrated final verifier found sub-minimum walls in the base. The session had
checked an assembly or selected part rather than every printable. It also
reran the thickness tool with 0.2, 0.1, and 0.04 mm nozzle arguments, creating
local passes that did not satisfy the normal 0.4 mm final profile.

The same review described a mechanical device/prototype with rough faceting,
dominant exposed workings, and a small signature detail, yet marked the product
finished and desirable. Two Make turns consumed 1h44m58s without a valid
proposal or public product.

## Decision

New materialized runs use signature-review schema v6. Before rendering or
coordinating the visual critic, Make runs:

```text
verify_project <cad-project> --print-preflight
```

Print-preflight is a deterministic mode, not another cognitive stage. It:

1. generates every declared printable entry;
2. runs strict bed fit across those entries;
3. exports every printable STL;
4. checks every mesh; and
5. checks every wall thickness at a fixed 0.4 mm nozzle profile.

It always writes `measure/print-preflight.md`. The schema-v6 visual review binds
the exact passing report hash. Both the CAD verifier and run-local finalizer
reject a missing, failing, weakened-profile, incomplete, or hash-mismatched
preflight. The final full-tier verifier and isolated host rebuild remain
unchanged independent gates.

The native iterative command intentionally omits `--fresh`. Product-run
sandboxes may allow generated-file cleanup while protecting empty directory
removal. Source-closure freshness rebuilds changed entries during iteration;
the trusted isolated host alone performs destructive `--fresh` cleanup and the
authoritative rebuild. This clarification was added after the Comet Choir
production run exposed an agent-side `PermissionError` on an empty generated
cache directory.

The critic must fail closed on visible presentation defects. A prototype or
wrong-object read, dominant exposed mechanism, zoom-dependent signature, raw
faceting, unclear state change, or visible caveat in `largest_risk` is blocking
even when the deterministic CAD is valid.

## Consequences

- Multi-part print failures are found before spending the bounded critic.
- A smaller nozzle cannot turn an ordinary-FDM failure into accepted preflight
  evidence.
- Review evidence is bound to the exact deterministic prerequisite it consumed.
- The quality bar explicitly distinguishes technically valid prototypes from
  desirable finished toys.
- No Python reasoning, model judge, additional agent, or retry loop is added.
- Frozen older runs retain their materialized schema and protocol.

## Verification

- CAD tests prove print-preflight includes every printable, strict fit, mesh,
  and fixed-profile thickness, and refuses a weakened nozzle.
- Finalizer tests reject a hash-bound report that used a 0.1 mm nozzle.
- The CAD self-check retains every existing refusal and failure-path fixture.
