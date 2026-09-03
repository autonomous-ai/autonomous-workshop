## Purpose

Concept is the run stage that turns an invented idea into one decided, visualized design before any geometry exists. The native session researches the Wish and commits the design's physical facts; the host validates that commitment, seals it, and binds Make to it — so Make builds to a design that was decided, rather than reinterpreting a title and a summary.

## Requirements

### Requirement: Concept is a run stage between Invent and Make

The Workshop SHALL carry `concept` as a stage of a run, ordered after `invent` and before `make`. Every place that enumerates or sequences stages — the stage set, the forward transitions, the upstream mapping, the stages invalidated by a new Make revision, and the stages a run may be waiting at — SHALL treat `concept` on the same terms as the stages either side of it.

Concept SHALL have exactly one deterministic gate, and only that gate SHALL be able to advance a run out of Concept.

#### Scenario: The stage set contains Concept in order

- **WHEN** the run stages are enumerated
- **THEN** they are `wish`, `match`, `invent`, `concept`, `make`, `playtest`, `release`, `deliver`, in that order

#### Scenario: A run reaches Make only through Concept

- **WHEN** a run whose current stage is `invent` advances
- **THEN** its only legal next stage is `concept`
- **AND** a run whose current stage is `concept` may advance only to `make`

#### Scenario: Concept's upstream is Invent

- **WHEN** the stage upstream of `concept` is resolved
- **THEN** it is `invent`

#### Scenario: A proposal cannot skip the gate

- **WHEN** a Concept proposal names a transition other than the one Concept's gate permits
- **THEN** the proposal is refused and the run does not advance

### Requirement: The stage packet binds Concept to the exact upstream bytes

Before the Concept turn the host SHALL write a read-only stage packet binding the stage to the current checkpoint and to a subject derived from the complete upstream identity vector — the Wish, the accepted Match assignment, the selected Taste, the lane blueprint, and the sealed Invent result. The packet SHALL name the canonical paths the turn must write, and the round and round allowance the turn is running under.

The native session SHALL read the packet and SHALL NOT edit it. A proposal bound to a different checkpoint or a different subject SHALL be refused, so a proposal authored against superseded inputs cannot be replayed.

#### Scenario: The packet carries the upstream bindings

- **WHEN** the host prepares the Concept turn
- **THEN** the packet names the Wish, the assignment, the selected Taste, the lane blueprint, and the sealed Invent result with its hash
- **AND** it names the canonical paths for the brief, the research record, and the concept tree

#### Scenario: A replayed proposal is refused

- **WHEN** a Concept proposal names a checkpoint or subject other than the one the current packet binds
- **THEN** the proposal is refused and no gate is consumed

#### Scenario: The concept is written only where the packet says

- **WHEN** the Concept turn writes its output
- **THEN** every file it produces resolves inside the concept tree the packet named
- **AND** output written outside that tree is refused

### Requirement: The native session decides the design and the host composes nothing

The Concept turn SHALL be the work of the native session: it researches the Wish through its own capabilities, decides the design's physical facts, and authors the brief, the research record, and one drawing instruction per required image role.

The host SHALL NOT compose, score, rank, or select any part of a concept. It SHALL NOT author a drawing instruction, choose between candidate designs, or judge whether a design is good. Its whole part is to validate the authored structure, run the effects the design calls for, seal the result, and decide the transition.

#### Scenario: The turn authors the design

- **WHEN** the Concept turn completes
- **THEN** the brief, the research record, and one drawing instruction per required image role were written by the native session

#### Scenario: The host writes no design content

- **WHEN** a concept is sealed
- **THEN** no physical fact, drawing instruction, or design decision in it originated with the host

#### Scenario: Quality is not judged by the host

- **WHEN** the gate evaluates a Concept proposal
- **THEN** it decides only whether the authored structure satisfies this capability's rules
- **AND** it forms no view on whether the design is a good design

### Requirement: The gate refuses a brief that decided nothing

The gate SHALL refuse a concept whose brief is not a decision about this Wish. It SHALL refuse a brief missing an object, a category, an envelope of three positive millimetre dimensions, a positive wall thickness, a print stance, or at least one component. It SHALL refuse a fact that names neither a source the research recorded nor a decision recorded with its reason, and a fact that names both. It SHALL refuse a component specified only by name and purpose, without its form, bounding dimensions, placement, and interfaces. It SHALL refuse a distinctive feature that only restates the Wish's own objective.

A refusal SHALL name the rule that refused it, and the run SHALL NOT advance to Make.

#### Scenario: A brief missing required facts is refused

- **WHEN** a brief states no object, no envelope, no wall thickness, no print stance, or no component
- **THEN** the gate refuses it, naming the missing fact

#### Scenario: An unattributed fact is refused

- **WHEN** the brief states a fact carrying neither a recorded source nor a recorded decision
- **THEN** the gate refuses the concept

#### Scenario: A fact claiming both attributions is refused

- **WHEN** a fact is recorded against a source and also recorded as an assumption
- **THEN** the gate refuses the concept

#### Scenario: A named-only component is refused

- **WHEN** a component states a name and a purpose but no form, bounding dimensions, placement, or interfaces
- **THEN** the gate refuses the concept

#### Scenario: A restated objective is not a feature

- **WHEN** the brief's only distinctive feature repeats the Wish's objective text
- **THEN** the gate refuses the concept as having decided nothing

#### Scenario: A refusal names its rule

- **WHEN** the gate refuses a concept for any reason
- **THEN** the recorded decision names the rule that refused it
- **AND** the run does not advance to Make

### Requirement: A sealed concept has one identity, and Make is bound to it

A concept accepted by the gate SHALL be sealed by content addressing over its whole tree — the brief, the research record, the drawing instructions, the descriptor, and every image — yielding one `concept_sha256`. The host SHALL record that identity on the run, and the Make stage's packet and sealed result SHALL both carry it.

A run resumed after parking SHALL restore the same concept identity. A sealed concept whose bytes changed after the gate accepted it SHALL be refused at the next boundary that checks it.

#### Scenario: Sealing produces one identity over everything

- **WHEN** a concept is sealed
- **THEN** its identity covers the brief, the research record, the drawing instructions, the descriptor, and every image file

#### Scenario: Make carries the concept identity

- **WHEN** the Make stage runs after Concept
- **THEN** its packet names the concept identity
- **AND** the sealed Make result records the concept identity it was built from

#### Scenario: Tampering is caught at the next boundary

- **WHEN** any byte under a sealed concept tree is added, removed, or modified after the gate accepted it
- **THEN** the next boundary that checks the concept fails

#### Scenario: Resume restores the same concept

- **WHEN** a run is resumed after parking downstream of Concept
- **THEN** the restored state names the same concept identity it recorded before parking
- **AND** a restored state naming a different concept is refused

### Requirement: A later round revises the standing design rather than restarting it

When a failed Playtest returns the run to Make, the standing concept SHALL remain in force unless the feedback invalidates the design itself. Where feedback invalidates the concept, the run SHALL revise it before Make runs again: the next Concept turn SHALL receive the standing concept and the feedback, SHALL reuse the standing research rather than researching the Wish again, and SHALL preserve every feature the feedback did not challenge.

Revision SHALL NOT accumulate without bound. Beyond the configured refine allowance the next revision SHALL re-anchor on the design's locked facts rather than refine a drifting design further.

#### Scenario: Build-only feedback leaves the design standing

- **WHEN** feedback invalidates the build but not the design
- **THEN** the standing concept is carried into the next Make round unchanged
- **AND** no Concept turn runs for that round

#### Scenario: Design feedback revises the standing concept

- **WHEN** feedback invalidates the design
- **THEN** the next Concept turn receives the standing concept and that feedback
- **AND** the revised concept reflects each requested change while the parts the feedback did not mention remain recognizably the same design

#### Scenario: A refining round does not re-research the Wish

- **WHEN** a Concept turn runs carrying a standing concept
- **THEN** it reuses that concept's research record rather than researching the Wish again

#### Scenario: Revision is bounded

- **WHEN** consecutive rounds have each refined the previous round's concept up to the refine allowance
- **THEN** the next revision re-anchors on the design's locked facts

### Requirement: Concept waits truthfully rather than proceeding without a design

Concept SHALL NOT invent, placeholder, or approximate a design it could not actually research or draw. Where a capability the design needs is absent — including an effect the host must perform outside the native turn — the run SHALL be recorded as waiting at `concept`, carrying a need that names what is missing and what would satisfy it, and Make SHALL NOT be called for that round.

A waiting run SHALL preserve its round and its accepted work, so resuming it continues the same run rather than starting a replacement.

#### Scenario: A missing capability parks the run

- **WHEN** a capability the concept needs is not configured
- **THEN** the run is recorded as waiting at `concept` with a need naming that capability
- **AND** Make is not called for that round

#### Scenario: Waiting preserves the round

- **WHEN** Concept waits in a round
- **THEN** the recorded run reports stage `concept`, that round, and the raised needs

#### Scenario: No placeholder design is substituted

- **WHEN** Concept cannot complete
- **THEN** no default envelope, wall thickness, feature, print stance, or component breakdown is recorded in place of one that was never decided

#### Scenario: Resuming continues the same run

- **WHEN** a run waiting at `concept` is resumed once the missing capability is configured
- **THEN** it continues in the same session and round rather than starting a replacement run
