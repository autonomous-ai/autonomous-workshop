# ADR 0019: Freeze a lower-cost Codex profile for Spark

- Status: Accepted
- Date: 2026-08-30
- Owners: Runtime, Workflow, and product-run instruction maintainers
- Relates to: ADR 0012 (one native session), ADR 0016 (effort routes)

## Context

Spark removed standalone Match, Invent, and Playtest turns, but a measured
production run still spent 24,616,026 gross input tokens and 88,501 output
tokens over 49 minutes 28 seconds. Make alone accounted for 22,343,631 input
tokens. The product and its repaired two-page manual passed every existing gate
and were published as Moonchase Fox, so this run is the named quality and cost
baseline rather than a synthetic estimate.

The gross input counter includes repeated cached context across native tool
cycles. Cached input is not equivalent to fresh input or a dollar total, but it
still consumes runtime capacity and cannot be ignored at Workshop scale. Two
host turns are therefore insufficient evidence of an economical run when each
turn contains many model/tool cycles.

## Decision

New Codex Spark workspaces freeze
`references/spark-economics-v1.md`. When, and only when, that exact immutable
capability is present, the host launches the one Wish-wide Codex session with
`model_reasoning_effort="low"`. Make and Release resume the same session with
the same profile.

Forge and Quest retain `high` reasoning. Other Manager adapters retain their
own native policy. Older Spark runs lack the marker and resume with the
historical `high` setting, preserving the private Codex runtime-policy binding.
No installed-code update silently changes a frozen session.

The product-run playbook also requires independent reads, searches, renders,
and checks to be batched in native code mode. Spark spends additional cycles
only on a concrete failing check or visible defect. This is native-agent
guidance, not a Python planner, prompt loop, or token judge.

All quality and truth boundaries remain unchanged: exact Inventor Taste,
signature interaction and anti-generic mechanism, full-tier CAD and thickness
checks, direct visual inspection, printable manual review, truthful Playtest
omission, authenticated Factory publication, and public hash readback.

## Alternatives considered

### Lower every effort to the same profile

Rejected. Forge and Quest explicitly buy deeper invention and evidence work.
Their economics need separate comparable baselines rather than inheriting a
Spark optimization.

### Enforce a Python token or tool-call loop

Rejected. It would make the host a cognitive scheduler and could terminate a
stage before its exact artifact passes. The native runtime owns its Goal and
tool use; the host continues to own only deterministic budgets and gates.

### Remove quality checks to save tokens

Rejected. A cheaper generic or unverifiable toy fails the conjunctive quality
and economics objective.

## Compatibility and migration

The capability is frozen by an exact file in the materialized product-run
instruction manifest. Resume selects `low` only from the frozen checkpoint's
input inventory. Existing sessions and runs without the marker remain `high`.

## Verification

- Runtime tests prove new marked Spark selects `low` while Forge and unmarked
  Spark select `high`.
- Packaging tests prove the marker is present in new product projects.
- Codex's private session checkpoint continues to bind the exact reasoning
  setting, so a changed profile fails closed.
- A production challenger must pass every existing gate, remain publicly
  inspectable, and report complete per-stage token telemetry.
- The economics target is at most 0.1x Moonchase Fox's gross input without an
  increase hidden in uncached input or output. The quality target requires a
  blind preference over the baseline on the signature experience and most
  other dimensions. Until that benchmark exists, the combined 10x/0.1x goal
  remains unproven.
