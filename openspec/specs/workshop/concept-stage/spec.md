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

### Requirement: Marked Forge and Quest activate Concept only inside Invent

For a new Forge or Quest run carrying the active Invent Concept capability, Workshop SHALL require Concept authoring and host sealing as a compound boundary inside `invent`. The active boundary SHALL reuse the current Invent packet, Goal, native turn, proposal, rejection budget, waiting state, and transition to Make. It MUST NOT add `concept` to the stage set or create a Concept-specific packet, Goal, checkpoint, transition, turn, pass-through record, or lifecycle status.

#### Scenario: Status reports an active Concept effect
- **WHEN** a marked run is authoring, rendering, reconciling, or sealing Concept work
- **THEN** its current lifecycle stage remains `invent`
- **AND** status does not report a Concept stage

#### Scenario: Invent advances
- **WHEN** the compound Invent gate accepts assignment, invention, and sealed Concept bytes
- **THEN** the only forward transition is `make`
- **AND** no intermediate Concept transition is recorded

### Requirement: Dormant and active contracts are selected by frozen capability

Installed host code SHALL distinguish dormant contract availability from active route behavior using immutable run capability bytes. Parsing or evaluating a Concept outside a marked Forge/Quest Invent attempt SHALL remain side-effect free and SHALL NOT mutate a lifecycle. A run created before activation MUST remain readable under its original packet, finalizer, artifacts, and gate behavior.

#### Scenario: Dormant validation is called directly
- **WHEN** a caller parses or evaluates a Concept contract outside an enabled compound Invent gate
- **THEN** it returns deterministic validation or an error only
- **AND** no effect or checkpoint mutation occurs

#### Scenario: A frozen unmarked Forge run resumes after upgrade
- **WHEN** installed Workshop contains activation code but the run lacks the exact marker
- **THEN** Invent completes under the older assignment-and-Invented protocol
- **AND** Make does not require a Concept binding
