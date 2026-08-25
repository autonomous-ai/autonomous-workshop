## Purpose

Wish research is the step that turns a person's words into the physical facts a design can actually be built from. It reads the Wish against real-world knowledge — what the named object is, how big it really is, what parts it is made of — and returns a breakdown in which every number is either taken from a named source or recorded as a decision the Workshop made, so that Concept, Make, and CAD work from findings rather than from placeholders.

## Requirements

### Requirement: Concept researches the Wish before it locks any physical fact

The Workshop SHALL provide a wish-research capability as an injected port on the Concept job, installed once for a Workshop in the same way its image and inspection capabilities are. The capability SHALL be a callable that receives the round's Wish, the inventor's Taste, and the lane blueprint, and returns one researched breakdown of that Wish.

Research SHALL run before the brief is locked, and the brief SHALL be derived from what research returned. No physical fact may be settled ahead of the research that is supposed to decide it.

#### Scenario: Research receives the round's bindings

- **WHEN** Concept begins a round that has no standing concept
- **THEN** it calls the wish-research capability with that round's Wish, Taste, and lane blueprint
- **AND** it locks no envelope, wall thickness, feature, print stance, fit target, or component before that call returns

#### Scenario: The brief comes from the research

- **WHEN** research returns a breakdown
- **THEN** the round's brief states the facts that breakdown decided
- **AND** no fact in the brief was substituted from a fixed default in place of a researched one

#### Scenario: Research is not repeated for a refining round

- **WHEN** Concept runs a round that carries a standing concept from an earlier round
- **THEN** it reuses that concept's research rather than researching the Wish again
- **AND** the standing brief's researched facts are carried forward unchanged except where this round's feedback asks the design to change

### Requirement: A breakdown decides every fact the brief must state

A researched breakdown SHALL decide what the object is, its category, its approximate envelope in millimetres, its wall thickness in millimetres, its distinctive features, its intended print orientation and support use, its component breakdown, and, where the design must hold or fit something, that target's own dimensions and the clearance around it.

Each decided fact SHALL be specific to this Wish. A feature that restates the Wish's own objective, or an envelope that is the same for every Wish regardless of what was asked for, does not satisfy this requirement.

#### Scenario: The breakdown covers the brief

- **WHEN** a breakdown is returned
- **THEN** it states an object, a category, an envelope of three positive millimetre dimensions, a positive wall thickness, at least one distinctive feature, a print orientation, a support decision, and at least one component
- **AND** a breakdown missing any of these is refused

#### Scenario: A fit target carries its own size

- **WHEN** research concludes the design must hold, seat, or fit something
- **THEN** the breakdown states that target, its own dimensions in millimetres, and the clearance around it
- **AND** where research concludes the design holds nothing, it states no fit target rather than an empty one

#### Scenario: A restated objective is not a feature

- **WHEN** a breakdown's only distinctive feature repeats the Wish's objective text
- **THEN** the breakdown is refused as having decided nothing

### Requirement: Every fact in a breakdown is attributable

A breakdown SHALL attribute each fact it states to exactly one of two things: a source the research read, named and recorded; or a decision the Workshop made in the absence of a source, recorded in the brief's assumptions with the reason it was decided that way.

A fact carrying neither attribution SHALL be refused. A decided fact SHALL NOT be presented as if a source or the Wish supplied it, and a sourced fact SHALL NOT be recorded as an assumption.

#### Scenario: A sourced fact names its source

- **WHEN** research takes a dimension, proportion, standard, or material fact from a source
- **THEN** the breakdown records that fact against that source's identifier
- **AND** the fact does not appear in the brief's assumptions

#### Scenario: An unsourced fact is recorded as a decision

- **WHEN** research finds no source for a fact the brief must state
- **THEN** the Workshop decides it and records the decision, and the reason for it, in the brief's assumptions
- **AND** the decision is not attributed to any source

#### Scenario: An unattributed fact is refused

- **WHEN** a breakdown states a fact that names neither a source nor a recorded decision
- **THEN** the breakdown is refused and the round does not proceed to drawing

#### Scenario: A source that was cited but not recorded is refused

- **WHEN** a fact names a source identifier that the breakdown's source records do not contain
- **THEN** the breakdown is refused

### Requirement: A breakdown names the design's real parts

The component breakdown SHALL be the parts the researched object actually has, each specified in its own right — its purpose, its form, its bounding dimensions in millimetres, its placement in the assembly, and its interfaces to adjoining parts.

A single-component breakdown SHALL be legitimate only where research concluded the design is genuinely one printed part, and that conclusion SHALL be recorded. A single component standing in for parts that were never worked out SHALL be refused.

#### Scenario: A multi-part object is broken into its parts

- **WHEN** research concludes the Wish names an object made of distinguishable parts
- **THEN** the breakdown names those parts, each with its own purpose, form, dimensions, placement, and interfaces
- **AND** each part's dimensions are consistent with the envelope the breakdown decided

#### Scenario: A genuinely single-part design says so

- **WHEN** research concludes the design prints as one part
- **THEN** the breakdown names one component and records the finding that the design is one part
- **AND** the finding names the source or decision it rests on

#### Scenario: A placeholder component is refused

- **WHEN** a breakdown names a single component whose form, placement, or interfaces merely restate the envelope and state nothing about the design
- **THEN** the breakdown is refused

### Requirement: Research is sealed with the concept it produced

The research a brief came from SHALL be recorded inside the concept root and sealed by the same content addressing that seals the images, so that the concept's hash covers the findings as well as the pixels.

The record SHALL state each finding and the source identifiers it rests on, and for each source: where it came from, the exact excerpt relied upon, that excerpt's content hash, and when it was retrieved.

#### Scenario: The research travels with the concept

- **WHEN** Concept returns a sealed concept
- **THEN** the concept root contains the research record for the brief it locked
- **AND** the concept's hash covers that record

#### Scenario: Swapping the research invalidates the concept

- **WHEN** the research record inside a sealed concept root is altered after the job completed
- **THEN** the concept no longer matches its recorded hash and is refused

#### Scenario: A source is recorded by what was read, not by promise

- **WHEN** a source is recorded
- **THEN** the record states its origin, the excerpt relied on, that excerpt's content hash, and its retrieval time
- **AND** a source recorded without the excerpt it contributed is refused

### Requirement: Researched constraints are written back without touching the routed Wish

The researched constraints SHALL be written back as a derived Wish record carrying the original Wish's product identifier, objective, and context together with the researched constraints. The routed Wish SHALL NOT be mutated, and the identity that matching was decided from SHALL remain the untouched Wish.

The derived record SHALL name both identities — the routed Wish's hash and its own — so that the two can never be mistaken for one another.

#### Scenario: The derived Wish carries the researched constraints

- **WHEN** research completes for a Wish
- **THEN** a derived Wish record is written stating the researched envelope, wall thickness, features, print stance, fit target, and components as constraints
- **AND** its objective, product identifier, and context are those of the routed Wish, unchanged

#### Scenario: Routing identity survives the write-back

- **WHEN** a derived Wish is written for a routed assignment
- **THEN** the routed Wish's recorded hash is unchanged
- **AND** the derived record names both that hash and its own

#### Scenario: Later jobs receive the researched constraints

- **WHEN** the round proceeds from Concept to Make
- **THEN** the Wish that Make and the jobs after it receive is the derived one, carrying the researched constraints
- **AND** the objective those jobs quote to a person is still the person's own words

#### Scenario: A derived Wish that changed the words is refused

- **WHEN** a derived Wish record states an objective, product identifier, or context that differs from the routed Wish
- **THEN** it is refused

### Requirement: Research directs the design and never evidences it

Research SHALL be treated as instruction, in the same way concept art is: it says what should be built and what that decision rested on. It SHALL NOT count as evidence that anything was built, SHALL NOT satisfy any Playtest check, and SHALL NOT be admitted as product proof.

#### Scenario: Research is labelled as research

- **WHEN** the research record is written
- **THEN** it states that it is research behind an intended design and is not valid as product proof

#### Scenario: Research does not stand in for a Playtest result

- **WHEN** a Playtest check has no evidence and the research record contains a finding that speaks to it
- **THEN** the check does not pass on the strength of the finding

### Requirement: Research that cannot be done is refused, never approximated

Where the wish-research capability fails, returns nothing usable, or returns a breakdown that fails any rule of this capability, Concept SHALL fail or wait for the round rather than fall back to a default breakdown. Substituting fixed placeholder facts for research that did not happen SHALL NOT occur.

#### Scenario: A failing researcher stops the round

- **WHEN** the wish-research capability raises or returns an unusable result
- **THEN** the round produces no brief and no images
- **AND** no default envelope, wall thickness, feature, or component is substituted

#### Scenario: A refused breakdown is reported for what it is

- **WHEN** a breakdown is refused by any rule of this capability
- **THEN** the failure names which rule refused it
- **AND** the run does not advance to Make
