# ADR 0002: Dependency and orchestration boundaries

- Status: Accepted
- Date: 2026-08-25
- Owners: Workflow maintainer and all component DRIs

ADR 0012 supersedes this record's Python composition model while preserving
its component ownership, dependency direction, and workflow-sequencing rules.

## Context

The flat implementation allowed stage agents to compose later stages, import
private sibling classes, and reach concrete providers. That made ownership
unclear and created cycles. In particular, Invent should not construct the
whole Workshop, and Playtest should not import a private Make builder to verify
an artifact.

## Decision

The Workshop applies these dependency rules:

1. A component owns its input/output contracts and publishes them from its
   package boundary.
2. Components import only another component's documented public contracts.
3. Components do not invoke the next lifecycle stage.
4. `workflow` alone sequences Invent, Make, Playtest, Release, and Deliver
   and mediates Playtest feedback back to Make.
5. `workshop.workflow.native_run` is the trusted host and sole composition
   root. Components do not construct the next stage or native agent session.
6. A component declares ports for model, storage, CAD, Factory, carrier, or
   other outside behavior. `integrations` implements those ports.
7. Domain components never import a concrete integration.
8. CLI calls the public Workflow host service. Workshop never imports CLI or
   executable Inventor profile code; Inventors are immutable persona data.
9. Match produces an immutable assignment before the six-stage Workflow;
   Reviews authenticate feedback after delivery and may inform future work.
10. Missing capability and ambiguous outcomes remain typed needs or waits, not
    successful results.

The conceptual flow is:

```text
Wish -> Match -> Workflow
                  |
                  v
        Invent -> Make <-> Playtest -> Release -> Deliver
                    feedback is mediated by Workflow

Reviews --------------------------------------------> future work
```

Shared artifact and runtime services support the flow but are not lifecycle
stages. `WorkshopServices` is the composition record; the term `skill` remains
reserved for executable agent resources.

## Alternatives considered

### Let each stage call the next

Rejected because retries, feedback, checkpoints, and failures would be split
across owners and could not be audited as one transition graph.

### Put all contracts in one central jobs module

Rejected because every component change would modify one hotspot and no
component could evolve its public seam independently.

### Let adapters define domain records

Rejected because provider choices would leak into Workshop contracts and make
offline testing dependent on concrete services.

## Consequences

The import graph can be acyclic and mechanically enforced. Components are
testable with deterministic port fakes. Cross-component changes require
explicit contracts and both owners' reviews. Workflow becomes smaller but more
important: it owns order and state transitions, never stage implementation.

Some data must be mapped at boundaries rather than imported from a shared model
bag. That explicit conversion is intentional evidence of coupling.

## Compatibility and migration

Extract public contracts before moving implementation. Characterization tests
freeze current successful, waiting, malformed, retry, and ambiguous outcomes.
Move composition out of stage agents before enforcing the no-cycle rule.

Compatibility facades may translate old Python call shapes during the refactor,
but canonical code cannot depend on them and they cannot sequence stages.

## Verification

- Static architecture tests reject private sibling and forbidden directional
  imports.
- Tests prove Workflow is the only stage sequencer and feedback mediator.
- Every concrete provider is replaceable by a deterministic fake through a
  component-owned port.
- CLI and inventor smoke tests run against installed public APIs.
