# ADR 0045: Own agent-selected dependencies

- Status: Accepted
- Date: 2026-09-05
- Owners: Workflow, Make, and product-run instruction maintainers

## Context

An autonomous product run selected a commercial motor, discovered that its
supplier drawings contradicted one another, and returned a waiting need asking
the operator for manufacturer clarification. The run was correct not to make a
fabrication claim from ambiguous evidence, but wrong to delegate resolution of
its own engineering choice. The Wish required a desktop robot, not that exact
motor.

If every weak supplier document becomes a human escalation, Workshop is an
assistant to a human product engineer rather than an autonomous workshop.
Removing the evidence gate would be equally wrong: autonomy is not permission
to fabricate dimensions or hide physical uncertainty.

## Decision

The native product-run agent owns every dependency it selects. Missing,
ambiguous, contradictory, or inaccessible evidence for such a dependency is
ordinary repairable work. Unless the Wish explicitly requires that exact
component, the agent must qualify a different component, redesign the
mechanism, or eliminate the dependency while preserving the Wish and every
deterministic and safety gate.

The run-local `need` outcome is reserved for an external condition that cannot
be removed through product or implementation choices without violating the
Wish, a deterministic gate, safety, or host-only effect authority. It cannot be
used to ask the operator to make an engineering decision created by the
agent's own design.

This is native-agent judgment and work inside the existing stage Goal. Python
does not pick the replacement, generate candidates, or weaken a gate. The host
prompt states the ownership boundary; the agent searches, redesigns, builds,
checks, and finalizes through its own tools.

## Consequences

- A product run may change an agent-selected bill of materials without human
  approval when necessary to finish the Wish.
- Ambiguous supplier data still cannot support a fabrication-ready claim.
- Exact user constraints remain authoritative; the agent cannot redesign away
  a component that the Wish explicitly requires.
- Authentication, purchasing, publication, manufacture, and other host-owned
  effects retain their existing authorization boundaries.

## Verification

- Workflow prompt tests bind the substitute/redesign/eliminate instruction.
- Materialized product-run instructions reserve `need` for irreducible
  external conditions.
- A real resumed run that previously waited on an agent-selected component
  must continue Make and either pass its deterministic gate or expose a truly
  irreducible condition.
