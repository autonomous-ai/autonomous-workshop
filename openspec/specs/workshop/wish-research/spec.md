## Purpose

Wish research is the step that turns a person's words into the physical facts a design can actually be built from. It reads the Wish against real-world knowledge — what the named object is, how big it really is, what parts it is made of — and returns a breakdown in which every number is either taken from a named source or recorded as a decision the Workshop made, so that Concept, Make, and CAD work from findings rather than from placeholders.

## Requirements

### Requirement: Concept researches the Wish before it locks any physical fact

The Wish SHALL be researched by the native session, inside the Concept turn, through the session's own research capability. The Workshop SHALL NOT install a separate research capability for the stage to call, and the host SHALL NOT perform the research, compose a query, choose a source, or score a finding.

The stage packet supplies the round's bindings — the Wish, the selected Taste, and the lane blueprint — and the turn researches against those. Research SHALL run before the brief is locked, and the brief SHALL be derived from what the research found. No physical fact may be settled ahead of the research that is supposed to decide it.

#### Scenario: Research receives the round's bindings

- **WHEN** the Concept turn begins a round that has no standing concept
- **THEN** it researches the Wish its stage packet names, against that packet's Taste and lane blueprint
- **AND** it locks no envelope, wall thickness, feature, print stance, fit target, or component before that research is done

#### Scenario: The brief comes from the research

- **WHEN** research produces a breakdown
- **THEN** the round's brief states the facts that breakdown decided
- **AND** no fact in the brief was substituted from a fixed default in place of a researched one

#### Scenario: The host researches nothing

- **WHEN** a concept is sealed
- **THEN** no query, source, excerpt, or finding in its research record originated with the host

#### Scenario: Research is not repeated for a refining round

- **WHEN** the Concept turn runs a round that carries a standing concept from an earlier round
- **THEN** it reuses that concept's research rather than researching the Wish again
- **AND** the standing brief's researched facts are carried forward unchanged except where this round's feedback asks the design to change

### Requirement: A breakdown decides every fact the brief must state

A researched breakdown SHALL decide what the object is, its category, its approximate envelope in millimetres, its wall thickness in millimetres, its distinctive features, its intended print orientation and support use, its component breakdown, and, where the design must hold or fit something, that target's own dimensions and the clearance around it.

Each decided fact SHALL be specific to this Wish. A feature that restates the Wish's own objective, or an envelope that is the same for every Wish regardless of what was asked for, does not satisfy this requirement. The Concept gate SHALL settle these rules over the breakdown the turn recorded, and refuse a concept whose breakdown decided nothing.

#### Scenario: The breakdown covers the brief

- **WHEN** the Concept turn records a breakdown
- **THEN** it states an object, a category, an envelope of three positive millimetre dimensions, a positive wall thickness, at least one distinctive feature, a print orientation, a support decision, and at least one component
- **AND** the gate refuses a breakdown missing any of these

#### Scenario: A fit target carries its own size

- **WHEN** research concludes the design must hold, seat, or fit something
- **THEN** the breakdown states that target, its own dimensions in millimetres, and the clearance around it
- **AND** where research concludes the design holds nothing, it states no fit target rather than an empty one

#### Scenario: A restated objective is not a feature

- **WHEN** a breakdown's only distinctive feature repeats the Wish's objective text
- **THEN** the gate refuses it as having decided nothing

### Requirement: Every fact in a breakdown is attributable

A breakdown SHALL attribute each fact it states to exactly one of two things: a source the research read, named and recorded; or a decision the native session made in the absence of a source, recorded in the brief's assumptions with the reason it was decided that way.

A fact carrying neither attribution SHALL be refused, and so SHALL a fact claiming both. A decided fact SHALL NOT be presented as if a source or the Wish supplied it, and a sourced fact SHALL NOT be recorded as an assumption.

#### Scenario: A sourced fact names its source

- **WHEN** research takes a dimension, proportion, standard, or material fact from a source
- **THEN** the breakdown records that fact against that source's identifier
- **AND** the fact does not appear in the brief's assumptions

#### Scenario: An unsourced fact is recorded as a decision

- **WHEN** research finds no source for a fact the brief must state
- **THEN** the native session decides it and records the decision, and the reason for it, in the brief's assumptions
- **AND** the decision is not attributed to any source

#### Scenario: An unattributed fact is refused

- **WHEN** a breakdown states a fact that names neither a source nor a recorded decision
- **THEN** the gate refuses the concept and no image is drawn from that brief

#### Scenario: A source that was cited but not recorded is refused

- **WHEN** a fact names a source identifier that the breakdown's source records do not contain
- **THEN** the gate refuses the concept

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
- **THEN** the gate refuses the concept

### Requirement: Research is sealed with the concept it produced

The research a brief came from SHALL be recorded inside the concept tree and covered by the seal the stage takes over that tree, so that the concept's `concept_sha256` covers the findings as well as the pixels and the two cannot be separated afterwards.

The record SHALL state each finding and the source identifiers it rests on, and for each source: where it came from, the exact excerpt relied upon, that excerpt's content hash, and when it was retrieved.

#### Scenario: The research travels with the concept

- **WHEN** the Concept gate seals a concept
- **THEN** the concept tree contains the research record for the brief it locked
- **AND** the concept's `concept_sha256` covers that record

#### Scenario: Swapping the research invalidates the concept

- **WHEN** the research record inside a sealed concept tree is altered after the gate accepted it
- **THEN** the concept no longer matches its recorded `concept_sha256` and the next boundary that checks it fails

#### Scenario: A source is recorded by what was read, not by promise

- **WHEN** a source is recorded
- **THEN** the record states its origin, the excerpt relied on, that excerpt's content hash, and its retrieval time
- **AND** a source recorded without the excerpt it contributed is refused

### Requirement: Researched constraints are written back without touching the routed Wish

The researched constraints SHALL be written back as a derived Wish record in the concept tree, carrying the original Wish's product identifier, objective, and context together with the researched constraints. It is an artifact the native session authors and the gate validates, sealed with the rest of the concept. The routed Wish SHALL NOT be mutated, and the identity that matching was decided from SHALL remain the untouched Wish.

The derived record SHALL name both identities — the routed Wish's hash and its own — so that the two can never be mistaken for one another. Downstream stages SHALL receive it through their stage packet rather than in place of the Wish the run was routed on.

#### Scenario: The derived Wish carries the researched constraints

- **WHEN** research completes for a Wish
- **THEN** a derived Wish record is written into the concept tree stating the researched envelope, wall thickness, features, print stance, fit target, and components as constraints
- **AND** its objective, product identifier, and context are those of the routed Wish, unchanged

#### Scenario: Routing identity survives the write-back

- **WHEN** a derived Wish is written for a routed assignment
- **THEN** the routed Wish's recorded hash is unchanged
- **AND** the derived record names both that hash and its own

#### Scenario: Later jobs receive the researched constraints

- **WHEN** the run proceeds from Concept to Make
- **THEN** the Make stage packet names the derived Wish, carrying the researched constraints
- **AND** the objective the stages after it quote to a person is still the person's own words

#### Scenario: A derived Wish that changed the words is refused

- **WHEN** a derived Wish record states an objective, product identifier, or context that differs from the routed Wish
- **THEN** the gate refuses the concept

### Requirement: Research directs the design and never evidences it

Research SHALL be treated as instruction, in the same way concept art is: it says what should be built and what that decision rested on. It SHALL NOT count as evidence that anything was built, SHALL NOT satisfy any Playtest check, and SHALL NOT be admitted as product proof.

#### Scenario: Research is labelled as research

- **WHEN** the research record is written
- **THEN** it states that it is research behind an intended design and is not valid as product proof

#### Scenario: Research does not stand in for a Playtest result

- **WHEN** a Playtest check has no evidence and the research record contains a finding that speaks to it
- **THEN** the check does not pass on the strength of the finding

### Requirement: Research that cannot be done is refused, never approximated

Where the Wish cannot actually be researched — the session's research capability is unavailable, or what it found does not decide the facts the brief must state — the Concept turn SHALL report a waiting or failed outcome carrying a need that names what is missing, and the run SHALL NOT advance to Make. Where a breakdown was recorded but breaks any rule of this capability, the gate SHALL refuse the concept and name the rule that refused it.

Neither path SHALL fall back to a default breakdown. Substituting fixed placeholder facts for research that did not happen SHALL NOT occur, and a waiting run SHALL NOT be treated as licence to proceed with a defaulted brief.

#### Scenario: A failing researcher stops the round

- **WHEN** the Concept turn cannot research the Wish
- **THEN** the run is recorded as waiting at `concept`, with a need naming what is missing
- **AND** the round produces no brief and no images
- **AND** no default envelope, wall thickness, feature, or component is substituted

#### Scenario: A refused breakdown is reported for what it is

- **WHEN** a breakdown is refused by any rule of this capability
- **THEN** the recorded decision names which rule refused it
- **AND** the run does not advance to Make

#### Scenario: Waiting continues the same run

- **WHEN** a run waiting at `concept` for research is resumed
- **THEN** it continues in the same session and round rather than starting a replacement run
