## ADDED Requirements

### Requirement: New fixed-view Concept behavior remains inside Invent

For newly marked Forge and Quest runs, Workshop SHALL select the fixed-view Concept capability as a compound sub-boundary of `invent`. It SHALL reuse the existing Invent Goal, native turn, proposal, gate, effect wait, checkpoint, and transition to Make. It MUST NOT create a Concept stage, Goal, turn, transition, or pass-through record.

#### Scenario: Fixed-view effects wait after native Invent exits
- **WHEN** the native Invent turn finalizes valid fixed-view source and the provider work is incomplete
- **THEN** lifecycle status remains at `invent`
- **AND** resume continues host-owned reconciliation without rerunning Invent cognition

#### Scenario: Fixed-view Concept is sealed
- **WHEN** every exact fixed role is reconciled and sealed for the accepted Invent proposal
- **THEN** the existing Invent gate may advance directly to Make
- **AND** no intermediate lifecycle event is recorded

### Requirement: Fixed Concept version is frozen in the run

The selected fixed-view authoring reference, contract version, finalizer interface, role ceiling, and matching runtime-profile bytes SHALL be bound into the run at creation. Installed-code changes MUST NOT upgrade an existing fixed v1 or adaptive v2 run to the new contract or downgrade a fixed-view run on resume.

#### Scenario: Earlier marked run resumes
- **WHEN** a frozen earlier run lacks the new fixed-view marker
- **THEN** its original Concept behavior remains authoritative
