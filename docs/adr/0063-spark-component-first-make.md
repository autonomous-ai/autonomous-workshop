# ADR 0063: Build and review Spark components before assembly

- Date: 2026-09-10
- Status: Accepted and deterministically tested
- Relates to: ADR 0060 (Make-round visual feedback), ADR 0061 (Spark Make
  ownership) and ADR 0062 (STEP-only CAD toolchain)

## Context

Spark asked one early combined CAD baseline to carry component construction,
part-level form judgment, interfaces, and whole-object composition at once.
Although Make already required `part_<role>.step.py` for printable parts, its
round tool rendered the combined entry. A weak individual component could
therefore survive until assembly inspection, where defects are harder to
isolate and repairs can disturb already plausible neighbors.

## Decision

Newly materialized Spark Make runs use a component-first baseline:

1. every distinct physical component, including a one-piece product's sole
   component, is modeled in its own `part_<role>.step.py`;
2. the Manager runs an isolated `make_round --component` review-and-fix loop
   for each component, with its own build verdict, front/top/isometric packet,
   native visual feedback, and round history;
3. only after every component passes does the Manager author and inspect the
   combined non-part entry, using `--require-component-passes`; and
4. if an assembly repair changes a component's STEP, that component must pass
   its isolated loop again before another assembled-object round.

The round tool keeps component histories under
`measure/component-rounds/<role>/`. Component mode skips project-level motion
and implicit whole-object references; an explicit component-only reference may
still be supplied. Before assembly inspection, the tool freshly builds every
part and compares its exact STEP hash with the latest passing component state.
It renders no assembly when a pass is missing, failed, or stale.

This is native Make work. Python sequences existing deterministic tools and
binds exact evidence but does not interpret images, choose repairs, or judge
quality. The independent final signature critic and integrated verifier remain
required after assembled-object rounds. ADR 0061 still applies: Workshop does
not add a second Spark host rebuild or geometry acceptance gate.

Forge, Quest, and frozen existing product workspaces retain their materialized
whole-product baseline sequence and tool bytes.

## Verification

- Make-round tests prove component histories are isolated from assembly state.
- Assembly review is refused until every component's latest round passes.
- Freshly exported geometry that differs from a component pass is refused.
- Product-run asset tests bind the Spark-only component-first work order.
