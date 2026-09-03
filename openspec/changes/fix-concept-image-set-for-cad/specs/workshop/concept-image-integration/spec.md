## ADDED Requirements

### Requirement: Host executes the fixed reference graph without choosing design content

For a fixed-view Concept, the host SHALL derive the exact role order and execute `front` first, `top` and `bottom` from the completed front anchor, `exploded` from the completed front, top, and bottom images, and component roles from the completed exploded image plus their normalized textual component facts. The adapter SHALL preserve the declared reference order and MUST NOT add a role, creative feature, measurement, or alternative design.

#### Scenario: Fixed multipart graph executes
- **WHEN** the front, top, and bottom effects complete for a multipart Concept
- **THEN** the exploded request receives those three exact images in fixed order
- **AND** no component request is transmitted before the exploded result is available

#### Scenario: Required predecessor is unavailable
- **WHEN** an exploded or component request lacks one of its fixed predecessors
- **THEN** that request is not transmitted and the Invent effect remains incomplete

### Requirement: Provider requests carry the frozen reconstruction presentation

Each provider request SHALL bind the agent-authored role instruction, exact normalized physical facts relevant to that role, and a frozen role-specific presentation block derived from the fixed capability. The presentation block SHALL enforce direct view semantics, one complete subject, simple neutral lighting and background, consistent scale and orientation, visible construction, and the exclusion of text, dimensions, logos, watermarks, people, hands, unrelated props, scenes, reflections, and dramatic effects.

#### Scenario: Captured top-view request is inspected
- **WHEN** a deterministic adapter captures a top-view provider request
- **THEN** it contains the exact front image as its appearance anchor
- **AND** its frozen prompt requires the same object unchanged from a direct top view

#### Scenario: Captured component request is inspected
- **WHEN** a deterministic adapter captures a component provider request
- **THEN** it contains the exact exploded image and that component's normalized form, measurements, placement, interfaces, and assembly relationship
- **AND** it requests exactly one isolated complete part

### Requirement: Fixed-role effects retain durable safety and identity

Every fixed-role intent and receipt SHALL remain bound to the checkpoint, pre-render Concept identity, role id and kind, exact authored instruction, frozen presentation version, normalized facts, ordered reference hashes, output path, provider profile, and request format. Existing credential isolation, authorization, ambiguity handling, reconciliation, bounded retry, byte validation, atomic installation, and exact sealing requirements SHALL remain unchanged.

#### Scenario: Prompt protocol version changes
- **WHEN** the frozen presentation block changes for an otherwise identical role
- **THEN** the pre-render and effect identities change and old returned bytes cannot satisfy the new request
