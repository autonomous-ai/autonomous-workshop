## MODIFIED Requirements

### Requirement: Make compiles the sealed rules into an executable engine

The Make turn SHALL produce an executable model of the game from the rules sealed in the concept, and SHALL write it into the product tree so that it is covered by the product's content address.

ABO SHALL NOT own a Make stage of its own. The engine is built by the native session inside the shared Make turn, using the deterministic engine tool ABO declares as a hash-bound extension, and the host's Make gate seals it with the rest of the product. That tool is a specialist instrument, not an agent: it SHALL NOT start a session, schedule a prompt, choose a lifecycle transition, pass or waive a gate, read a credential, or perform an external effect. Its tree SHALL match the hash ABO's manifest declares for it, so that what ran is the thing that was reviewed.

The engine SHALL expose enough of the game to be played programmatically: starting a game for a supported seat count, reporting whose turn it is, enumerating the legal moves available, applying a chosen move, reporting whether the game is over, and reporting the winners once it is.

The engine SHALL declare the seat counts it supports, the move kinds the rules define, and whether any seat holds information another seat does not.

#### Scenario: The engine ships inside the product

- **WHEN** the Make gate seals a revision
- **THEN** the executable engine is a file inside the sealed product tree
- **AND** its bytes are covered by the product's content address

#### Scenario: The engine plays a game end to end

- **WHEN** the engine is driven from a fresh game to a terminal state using only legal moves it enumerated
- **THEN** it reports the game over and names the winners
- **AND** it never offers a move the rules do not define

#### Scenario: The engine declares its contract

- **WHEN** the engine is loaded
- **THEN** it declares its supported seat counts, its move kinds, and whether the game holds hidden information

#### Scenario: The native turn builds it, not an ABO stage

- **WHEN** an ABO run reaches Make
- **THEN** the engine is produced by the native Make turn using ABO's declared deterministic tool
- **AND** no ABO-owned Make stage, job, or lifecycle step runs

#### Scenario: An unmatched tool tree is refused

- **WHEN** the declared engine tool's bytes differ from the hash ABO's manifest records for it
- **THEN** the run refuses the tool and no engine built from it is accepted

### Requirement: The engine translates the rules and never invents them

The engine SHALL be a translation of the sealed rules and nothing more. Where the rules do not say what happens, the Make turn SHALL either refuse to proceed, naming the exact rule that is silent, or record the reading it took as a declared assumption naming the rule, the question, the reading chosen, and the alternative reading.

A declared assumption SHALL be written into the sealed product tree, so that it reaches Playtest as bytes bound to the revision under test rather than as state held in the session that decided it. An assumption that lives only in a turn's reasoning has not been declared, because the next stage reads bytes and nothing else.

The turn SHALL NOT invent a rule to make an unplayable game run, and SHALL NOT repair a game that the rules describe badly. A rules gap SHALL be returned as a finding against the rules, not absorbed into the engine.

#### Scenario: A silent rule is refused

- **WHEN** the rules do not define what happens in a state the engine can reach, and the reading is not recorded as an assumption
- **THEN** the Make turn refuses and names the rule that is silent
- **AND** the run does not advance to Playtest on that revision

#### Scenario: A chosen reading is declared

- **WHEN** the turn takes a reading of an ambiguous rule in order to proceed
- **THEN** that reading is recorded as an assumption naming the rule, the question, the reading taken, and the alternative
- **AND** it is written into the sealed product tree, where Playtest reads it and can exercise both readings

#### Scenario: An unsealed assumption is not an assumption

- **WHEN** a reading was taken but appears nowhere in the sealed product tree
- **THEN** the gate refuses the revision as having proceeded on an undeclared reading

#### Scenario: A broken game is not quietly fixed

- **WHEN** the sealed rules describe a game that cannot terminate or cannot be started
- **THEN** the turn returns that as a finding against the rules
- **AND** it does not add a rule of its own to make the engine run

### Requirement: Make builds STEP-first CAD for every component

The Make turn SHALL produce parametric CAD source and validated STEP geometry for every component in the sealed concept's brief, written into the same product tree. STEP SHALL be the primary CAD artifact; mesh and preview outputs SHALL be derived from it rather than authored independently.

Geometry SHALL be built with the Workshop's shared locked CAD skill, used exactly as it is locked. ABO SHALL NOT vendor a copy of that skill, wrap it behind a lane-specific interface, or ship a second geometry path of its own, because a private copy of a locked capability is a lock nobody can check.

The host SHALL run its deterministic CAD gate over the exact sealed product tree, on an isolated copy, using a verifier whose bytes match the hash carried in the run's trusted input manifest. A verifier that does not match that hash SHALL NOT run, and a CAD project whose bytes differ from the inventory the revision declared SHALL be refused.

#### Scenario: Every component has geometry

- **WHEN** the Make gate seals a revision
- **THEN** the product tree contains CAD source and STEP geometry for each component named in the brief

#### Scenario: Meshes derive from STEP

- **WHEN** mesh outputs are present
- **THEN** each is derived from the STEP artifact for the same component
- **AND** no mesh is present for a component that has no STEP artifact

#### Scenario: The locked skill is used as-is

- **WHEN** the Make turn builds geometry
- **THEN** it invokes the Workshop's shared locked CAD skill
- **AND** no copy or wrapper of that skill ships inside ABO
- **AND** the skill lock verification is unaffected by the run

#### Scenario: The gate runs only the trusted verifier

- **WHEN** the CAD gate runs
- **THEN** the verifier's bytes match the hash the run's trusted input manifest carries
- **AND** a verifier whose bytes differ is refused rather than run

#### Scenario: The gate measures the sealed bytes

- **WHEN** the CAD gate runs
- **THEN** it runs over an isolated copy of the exact product tree being sealed
- **AND** a CAD project that differs from its declared inventory fails the round

### Requirement: The brief's numbers govern the geometry

Where the sealed concept's images and its brief's millimetre facts disagree, the numbers SHALL govern. The Make turn SHALL build to the brief's envelope, wall thickness, fit targets, and print stance. A component's geometry SHALL be traceable to the brief facts it was built from.

#### Scenario: A number beats a picture

- **WHEN** a concept image implies a proportion that contradicts the brief's stated dimension
- **THEN** the built geometry matches the stated dimension

#### Scenario: Geometry is traceable to the brief

- **WHEN** a built component is inspected
- **THEN** the brief facts that determined its envelope and fits are identifiable

### Requirement: The product's components match the concept's, one to one

This guarantee is not ABO's to enforce. The shared Make gate settles it for every lane — see `workshop/make-concept-adherence` — and ABO inherits it rather than restating a private copy, because a lane-owned second copy could disagree with the check the host actually runs.

Under that shared gate the sealed Make result declares the product's components, they SHALL correspond one-to-one with the components in the sealed concept's brief, and no file in the product tree SHALL carry the bytes of a concept image. A product that ships a different set of parts is a different game, and the round SHALL be refused.

#### Scenario: A matching component set is accepted

- **WHEN** the Make turn seals a product whose components correspond one-to-one with the brief's
- **THEN** the round proceeds

#### Scenario: A changed part set is refused

- **WHEN** the Make turn seals a product containing a component the brief does not name, or omitting one it does
- **THEN** the round is refused

#### Scenario: Concept pixels stay out of the product

- **WHEN** any file in the product tree carries the bytes of a concept image
- **THEN** the round is refused

#### Scenario: ABO adds no correspondence check of its own

- **WHEN** component correspondence is checked for an ABO run
- **THEN** it is the shared Make gate that checks it
- **AND** ABO contributes no separate rule that could pass a product the shared gate would refuse

### Requirement: Make returns one immutable revision

The Make turn SHALL yield one sealed result bound to the exact bytes of its content-addressed product tree. Changing any byte after the gate sealed it SHALL invalidate the revision and every result bound to it.

A later round SHALL seal a new revision rather than amend the standing one, and SHALL invalidate the evidence downstream of the revision it replaces, while earlier revisions and their evidence remain unchanged.

#### Scenario: The revision is content-bound

- **WHEN** the Make gate seals a revision
- **THEN** its content address covers every file in the product tree, engine and geometry alike

#### Scenario: A post-Make edit is caught

- **WHEN** a product file changes after the revision is sealed
- **THEN** the next boundary that checks the revision fails

#### Scenario: A later round seals a new revision

- **WHEN** a failed Playtest returns the run to Make
- **THEN** the next round seals a new revision and the downstream evidence is invalidated
- **AND** the superseded revision is not edited in place

#### Scenario: An earlier round is preserved

- **WHEN** a later round produces a new revision
- **THEN** the earlier revision and its evidence remain unchanged
