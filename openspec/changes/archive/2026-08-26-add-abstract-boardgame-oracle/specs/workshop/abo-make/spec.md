## Purpose

ABO's Make turns a sealed, already-invented game into the exact files that make it playable and printable: an executable model of the rules that Playtest can run thousands of times, and STEP-first parametric CAD of every piece built to the brief's millimetres. It writes both into one immutable product tree, so the evidence that follows is bound to the same bytes a customer would receive.

## ADDED Requirements

### Requirement: Make compiles the sealed rules into an executable engine

ABO's Make SHALL produce an executable model of the game from the rules sealed in the concept, and SHALL write it into the product artifact tree so that it is covered by the product hash. The engine SHALL expose enough of the game to be played programmatically: starting a game for a supported seat count, reporting whose turn it is, enumerating the legal moves available, applying a chosen move, reporting whether the game is over, and reporting the winners once it is.

The engine SHALL declare the seat counts it supports, the move kinds the rules define, and whether any seat holds information another seat does not.

#### Scenario: The engine ships inside the product

- **WHEN** Make returns
- **THEN** the executable engine is a file inside the product artifact tree
- **AND** its bytes are covered by the product hash

#### Scenario: The engine plays a game end to end

- **WHEN** the engine is driven from a fresh game to a terminal state using only legal moves it enumerated
- **THEN** it reports the game over and names the winners
- **AND** it never offers a move the rules do not define

#### Scenario: The engine declares its contract

- **WHEN** the engine is loaded
- **THEN** it declares its supported seat counts, its move kinds, and whether the game holds hidden information

### Requirement: The engine translates the rules and never invents them

The engine SHALL be a translation of the sealed rules and nothing more. Where the rules do not say what happens, Make SHALL either refuse to proceed, naming the exact rule that is silent, or record the reading it took as a declared assumption naming the rule, the question, the reading chosen, and the alternative reading.

Make SHALL NOT invent a rule to make an unplayable game run, and SHALL NOT repair a game that the rules describe badly. A rules gap SHALL be returned as a finding against the rules, not absorbed into the engine.

#### Scenario: A silent rule is refused

- **WHEN** the rules do not define what happens in a state the engine can reach, and the reading is not recorded as an assumption
- **THEN** Make refuses and names the rule that is silent

#### Scenario: A chosen reading is declared

- **WHEN** Make takes a reading of an ambiguous rule in order to proceed
- **THEN** that reading is recorded as an assumption naming the rule, the question, the reading taken, and the alternative
- **AND** the assumption is available to Playtest so both readings can be exercised

#### Scenario: A broken game is not quietly fixed

- **WHEN** the sealed rules describe a game that cannot terminate or cannot be started
- **THEN** Make returns that as a finding against the rules
- **AND** it does not add a rule of its own to make the engine run

### Requirement: Hidden information is enforced by the engine, not by convention

Where the engine declares that the game holds hidden information, it SHALL expose what a given seat is permitted to see separately from the full state, and SHALL expose a way to resample the parts of the state a seat cannot see. A seat SHALL never be shown the full state.

Where the engine declares that the game holds no hidden information, the absence of those facilities SHALL be treated as the game having nothing to hide, not as the engine having forgotten to hide it.

#### Scenario: A seat sees only its own view

- **WHEN** a hidden-information engine is asked what a seat may see
- **THEN** it returns only that seat's permitted view
- **AND** the full state is not reachable from it

#### Scenario: Resampling preserves the seat's own view

- **WHEN** the hidden parts of a state are resampled for a seat
- **THEN** what that seat may see is unchanged

#### Scenario: Declared-open games need no concealment

- **WHEN** an engine declares the game holds no hidden information
- **THEN** the absence of concealment facilities is accepted
- **AND** that declaration is recorded so it can be checked against play

### Requirement: Make builds STEP-first CAD for every component

ABO's Make SHALL produce parametric CAD source and validated STEP geometry for every component in the brief, written into the same product artifact tree. STEP SHALL be the primary CAD artifact; mesh and preview outputs SHALL be derived from it rather than authored independently. Make SHALL build using the repository's locked CAD skill and SHALL NOT vendor or edit a second copy of it.

#### Scenario: Every component has geometry

- **WHEN** Make returns
- **THEN** the product tree contains CAD source and STEP geometry for each component named in the brief

#### Scenario: Meshes derive from STEP

- **WHEN** mesh outputs are present
- **THEN** each is derived from the STEP artifact for the same component
- **AND** no mesh is present for a component that has no STEP artifact

#### Scenario: The locked skill is used as-is

- **WHEN** Make builds geometry
- **THEN** it invokes the repository's locked CAD skill
- **AND** the skill lock verification is unaffected by the run

### Requirement: The brief's numbers govern the geometry

Where the concept's images and the brief's millimetre facts disagree, the numbers SHALL govern. Make SHALL build to the brief's envelope, wall thickness, fit targets, and print stance. A component's geometry SHALL be traceable to the brief facts it was built from.

#### Scenario: A number beats a picture

- **WHEN** a concept image implies a proportion that contradicts the brief's stated dimension
- **THEN** the built geometry matches the stated dimension

#### Scenario: Geometry is traceable to the brief

- **WHEN** a built component is inspected
- **THEN** the brief facts that determined its envelope and fits are identifiable

### Requirement: The product's components match the concept's, one to one

`Made` SHALL declare the product's components, and they SHALL correspond one-to-one with the brief's components. A product that ships a different set of parts is a different game and SHALL be refused.

Concept image bytes SHALL NOT appear anywhere in the product tree.

#### Scenario: A matching component set is accepted

- **WHEN** Make returns a product whose components correspond one-to-one with the brief's
- **THEN** the round proceeds

#### Scenario: A changed part set is refused

- **WHEN** Make returns a product containing a component the brief does not name, or omitting one it does
- **THEN** the round is refused

#### Scenario: Concept pixels stay out of the product

- **WHEN** any file in the product tree carries the bytes of a concept image
- **THEN** the round is refused

### Requirement: Make returns one immutable revision

Make SHALL return one revision whose product metadata is bound to the exact bytes of its artifact tree. Changing any byte after Make returns SHALL invalidate the revision and every result bound to it.

#### Scenario: The revision is content-bound

- **WHEN** Make returns
- **THEN** the returned revision's hash covers every file in the product tree, engine and geometry alike

#### Scenario: A post-Make edit is caught

- **WHEN** a product file changes after Make returns
- **THEN** the next boundary that checks the revision fails

#### Scenario: An earlier round is preserved

- **WHEN** a later round produces a new revision
- **THEN** the earlier revision and its evidence remain unchanged
