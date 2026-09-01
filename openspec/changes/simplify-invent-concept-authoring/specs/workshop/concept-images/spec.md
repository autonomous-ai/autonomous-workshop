## ADDED Requirements

### Requirement: Simplified Concept renders only need-driven roles

For a run with the simplified capability, the sealed image set SHALL contain exactly the roles declared by the validated adaptive visual plan and SHALL contain no more than 20 images. The set SHALL include `primary-form` and at least one `signature-experience` role. Exploded, component, alternate-view, and additional state roles SHALL be present only when their authored purpose names a construction, form, hidden-interface, or interaction need not already communicated by the required roles.

#### Scenario: Minimal one-piece set is sealed
- **WHEN** primary form and signature state completely communicate a one-piece concept
- **THEN** exactly those needful roles are rendered and no empty assembly or duplicate component image is required

#### Scenario: Optional role has no purpose
- **WHEN** a visual plan adds a view without naming what unique construction or interaction information it communicates
- **THEN** validation refuses the role before provider transmission

#### Scenario: Declared set exceeds 20 images
- **WHEN** an adaptive visual plan declares more than 20 roles
- **THEN** no image is produced and the Concept remains unsealed for native repair

### Requirement: Adaptive images remain one coherent design

Every image instruction SHALL carry or be losslessly bound to the normalized brief facts that govern its depicted geometry. `primary-form` SHALL establish the shared appearance anchor. Every later role SHALL reference only earlier completed roles for material, finish, palette, surface treatment, and form language while deriving shape, dimensions, placement, interfaces, and states from the normalized brief and its own instruction.

The signature role SHALL depict the promised action, transformation, perceptual result, or before/action/after relationship rather than another camera angle of one unchanged state. Concept images remain design direction and MUST NOT count as geometry, printability, Playtest, manufacture, or product evidence.

#### Scenario: Signature depends on a state change
- **WHEN** the concept promises a transformation between distinct physical states
- **THEN** the signature instruction depicts the distinct states or causal interaction and does not substitute a turntable view

#### Scenario: Later view uses appearance reference
- **WHEN** an adaptive role references `primary-form`
- **THEN** it preserves shared appearance while its geometry and state remain governed by authored physical facts

### Requirement: Derived paths and exact role completeness are sealed

The finalizer SHALL derive one safe distinct canonical image path from every accepted role id. The host SHALL render roles in validated dependency order, seal exactly one permitted image per role, and refuse missing, extra, duplicate, changed, or mixed-proposal bytes.

#### Scenario: Adaptive role set completes
- **WHEN** every declared role has one reconciled provider result at its derived path
- **THEN** the descriptor, image manifest, effect evidence, and sealed Concept cover exactly that role set
