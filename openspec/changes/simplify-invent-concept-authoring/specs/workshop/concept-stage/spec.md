## ADDED Requirements

### Requirement: Simplified Concept remains a compound Invent sub-boundary

For a new Forge or Quest run with the simplified capability, Concept authoring, pre-effect validation, host image effects, sealing, and acceptance SHALL remain inside the existing Invent checkpoint and one Invent Goal. The route MUST NOT add a `concept` stage, Goal, native turn, checkpoint, transition, pass-through artifact, or Concept-only revision edge.

#### Scenario: Simplified Forge advances
- **WHEN** the consolidated source, visual plan, normalization, authorized images, and sealed Concept all pass
- **THEN** the route advances directly from Invent to Make with no Concept lifecycle event

#### Scenario: Image effect waits
- **WHEN** a validated adaptive role cannot be safely completed or reconciled
- **THEN** the run waits at the same Invent checkpoint and does not rerun completed native authorship on resume

### Requirement: Only native content and deterministic projections enter the Concept

The Manager and selected Inventor SHALL own every design decision, research conclusion, physical constraint, component definition, presentation treatment, image role, and drawing instruction. The host SHALL own only structural validation, lossless normalization, canonical identities and paths, authorized effects, exact-byte sealing, and gate application.

#### Scenario: Host normalization succeeds
- **WHEN** the host derives a descriptor path or hashes exact source bytes
- **THEN** the derived value is accepted as plumbing and no new creative content is introduced

#### Scenario: Host would need to choose content
- **WHEN** an authored input omits a component, constraint, instruction, or necessary design decision
- **THEN** the host refuses the proposal instead of filling the omission
