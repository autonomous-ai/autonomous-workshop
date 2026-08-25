## ADDED Requirements

### Requirement: A concept carries the research its brief was decided from

A sealed concept SHALL contain the research record behind its brief, and that record SHALL be covered by the same content addressing that covers the images. The record SHALL state each finding and the source identifiers it rests on, and for each source its origin, the excerpt relied upon, that excerpt's content hash, and its retrieval time.

The research record SHALL be labelled as research behind an intended design and SHALL NOT be admissible as product proof, on the same terms as the concept art it accompanies.

#### Scenario: The research is sealed with the pixels

- **WHEN** a concept is sealed
- **THEN** its root contains the research record for its brief
- **AND** its content-addressed hash covers that record as well as the images

#### Scenario: Altering the research invalidates the concept

- **WHEN** the research record inside a sealed concept root is altered after the job completed
- **THEN** the concept no longer matches its recorded hash and is refused

#### Scenario: Research is not product proof

- **WHEN** the research record is offered in place of evidence that something was built
- **THEN** it is refused, and it is labelled in the record itself as not valid as product proof

## MODIFIED Requirements

### Requirement: A concept locks its design facts before it draws

A `ConceptImages` SHALL carry a `ConceptBrief` of the design's decided physical facts, and those facts SHALL be settled before any image is produced so that every image is drawn against the same numbers. The brief SHALL record what the object is, its category, its approximate envelope in millimetres, its wall thickness in millimetres, its distinctive features, its intended print orientation and support use, its component breakdown, any fit target it must accommodate, and the assumptions Concept made where research found no source.

Those facts SHALL be researched rather than defaulted. Each fact SHALL be attributable either to a source the research recorded or to a decision recorded in the brief's assumptions with its reason; a fact taken from neither is refused. A fixed envelope, wall thickness, feature, print stance, or component breakdown substituted because a fact was not stated SHALL NOT satisfy this requirement, and a feature that restates the Wish's own objective decides nothing.

The brief is the design's complete description, and it SHALL be complete independently of any image. Text does not occlude: a component hidden behind another in every external view is still fully stated in the brief. Accordingly the brief SHALL describe each component in its own right — its form, its bounding dimensions in millimetres, where it sits in the assembly, and how it meets its neighbours — in enough detail to draw that component without reading its shape off another image. The component breakdown SHALL be the parts the researched object actually has; a single component SHALL appear only where research concluded the design is genuinely one printed part and recorded that conclusion.

#### Scenario: The brief carries the numbers the geometry hangs on

- **WHEN** a `ConceptBrief` is produced
- **THEN** it states an envelope of three positive millimetre dimensions and a positive wall thickness
- **AND** where the design must fit or hold something, it states that target's own dimensions and the clearance around it

#### Scenario: Every component is specified, not merely named

- **WHEN** a `ConceptBrief` names a component
- **THEN** it states that component's form, its bounding dimensions in millimetres, its placement in the assembly, and its interfaces to adjoining components
- **AND** a component carrying only a name and purpose is rejected

#### Scenario: Hidden geometry is specified in the brief

- **WHEN** a component is not visible in any external view of the assembled design
- **THEN** the brief still states its form, dimensions, placement, and interfaces in full

#### Scenario: A researched fact names where it came from

- **WHEN** the brief states a fact that research took from a source
- **THEN** the concept's research record attributes that fact to that source
- **AND** the fact does not appear in the brief's assumptions

#### Scenario: Silence in the Wish becomes a recorded assumption

- **WHEN** neither the Wish nor the research finds a source for a fact the brief must state
- **THEN** Concept decides it and records the decision, with its reason, in the brief's assumptions
- **AND** the brief is never left with an invented number presented as if a source or the Wish supplied it

#### Scenario: A defaulted brief is refused

- **WHEN** a brief states an envelope, wall thickness, feature, print stance, or component breakdown that was substituted from a fixed default rather than decided for this Wish
- **THEN** the brief is refused and no image is drawn from it

#### Scenario: The parts of the object are the parts of the brief

- **WHEN** research concluded the wished-for object is made of distinguishable parts
- **THEN** the brief names those parts rather than one enclosing body
- **AND** a lone component whose form and placement merely restate the envelope is refused

#### Scenario: A brief missing required facts is refused

- **WHEN** a `ConceptBrief` is constructed without an object, an envelope, a wall thickness, or at least one component
- **THEN** construction fails with a contract error
