## ADDED Requirements

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
