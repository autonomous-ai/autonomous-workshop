## Purpose

Concept is the run stage that turns an invented idea into one decided, visualized design before any geometry exists. The native session researches the Wish and commits the design's physical facts; the host validates that commitment, seals it, and binds Make to it — so Make builds to a design that was decided, rather than reinterpreting a title and a summary.

## Requirements

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
