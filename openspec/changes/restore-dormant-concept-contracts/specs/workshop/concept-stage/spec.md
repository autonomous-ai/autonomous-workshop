## ADDED Requirements

### Requirement: Concept remains outside the lifecycle stage set

Concept SHALL remain dormant for current effort-aware runs. The authoritative executable routes SHALL remain Spark `Wish -> Make -> Release`, Forge `Wish -> Invent -> Make -> Release`, and Quest `Wish -> Invent -> Make -> Playtest -> Release`. No current or future effort route SHALL enumerate, enter, pass through, or synthesize a Concept stage, and dormant Concept validation SHALL NOT advance a run.

A later activation SHALL treat Concept as a compound sub-boundary of the first active creative stage: Invent for Forge/Quest and folded Make for Spark. It MUST version the owning stage's packet, finalizer, gate, wait/reconciliation behavior, downstream bindings, deterministic E2E, and real-Codex acceptance behavior together without adding a Concept Goal, native turn, checkpoint, transition, or pass-through artifact.

#### Scenario: A new run is created after dormant contracts are restored
- **WHEN** the run freezes Spark, Forge, or Quest effort
- **THEN** its enabled stages and turn count are unchanged from ADR 0016
- **AND** it contains no Concept stage, packet, gate, artifact, wait, or evidence

#### Scenario: Dormant validation succeeds
- **WHEN** a Concept contract passes deterministic structural evaluation
- **THEN** no lifecycle transition is proposed or applied

#### Scenario: Merged Concept behavior is later activated
- **WHEN** a new frozen route enables Concept authoring and sealing
- **THEN** that work executes inside the route's first active creative stage
- **AND** the route still contains no Concept stage, Goal, turn, checkpoint, or transition

### Requirement: Dormant evaluation does not compose design content

This change SHALL NOT ask the native Manager to author a Concept proposal. Dormant structural evaluation MUST NOT compose, repair, rank, render, semantically judge, or default design content, and no host-written placeholder SHALL be treated as an authored Concept.

#### Scenario: Dormant evaluator receives invalid source
- **WHEN** Concept source fails a structural rule
- **THEN** the evaluator rejects it rather than supplying or repairing design content

### Requirement: Dormant Concept identity does not alter Make

A dormant sealed Concept SHALL have one exact whole-tree identity, but current Make packets and Made contracts SHALL remain bound only to their existing Wish, assignment, Taste, blueprint, Invented, product, and CAD identities. Make MUST NOT require, accept, or emit a Concept identity until the later merged-boundary activation change updates its public contracts and frozen protocols.

#### Scenario: Current Make runs after dormant restoration
- **WHEN** Spark, Forge, or Quest reaches Make
- **THEN** its packet, finalizer, gate, and Made contract are unchanged
- **AND** no Concept identity is required or recorded

## REMOVED Requirements

### Requirement: Concept is a run stage between Invent and Make
**Reason**: The fixed Match/Invent/Concept topology predates ADR 0016 and contradicts the current selectable routes.
**Migration**: Keep Concept dormant until a later change versions it as a sub-boundary of Forge/Quest Invent and Spark folded Make; never restore a standalone Concept stage.

### Requirement: The stage packet binds Concept to the exact upstream bytes
**Reason**: No current stage packet targets Concept.
**Migration**: Exact input binding moves to dormant contract validation; a later activation change must extend the owning Invent or Make packet subject rather than create a Concept packet.

### Requirement: The native session decides the design and the host composes nothing
**Reason**: No native Concept turn exists in this slice.
**Migration**: Preserve the ownership invariant in dormant validation and add Concept authorship to the owning creative Goal only with merged-boundary activation.

### Requirement: The gate refuses a brief that decided nothing
**Reason**: This slice restores a structural evaluator, not a live stage gate.
**Migration**: Apply the same structural rules through dormant APIs until activation connects them to the owning Invent or Make host gate.

### Requirement: A sealed concept has one identity, and Make is bound to it
**Reason**: Sealed Concept identity can be restored without changing the current Made contract.
**Migration**: Keep exact identity dormant, then version the owning creative-stage receipt and downstream Make binding together during activation.

### Requirement: A later round revises the standing design rather than restarting it
**Reason**: There is no active Concept stage or standing Concept in the ADR 0016 routes.
**Migration**: Current Quest feedback continues to return to Make or Invent. After activation, design- and invention-level feedback both return to the merged Invent boundary for Forge/Quest, while build-only feedback returns to Make; no Concept edge is added.

### Requirement: Concept waits truthfully rather than proceeding without a design
**Reason**: A dormant contract library cannot create a lifecycle wait, and no authorized Concept effect exists in this slice.
**Migration**: Current stage waits keep their existing behavior; a later effect and activation change must bind any image-effect wait to the owning Invent or Make checkpoint rather than create a Concept waiting state.
