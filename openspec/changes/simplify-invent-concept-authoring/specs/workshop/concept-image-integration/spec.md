## ADDED Requirements

### Requirement: Host effects execute the validated adaptive graph without composition

For a simplified Concept, the host SHALL build its effect plan solely from the validated ordered role ids, exact agent-authored instructions, derived canonical paths, and declared earlier-role references. It MUST NOT invent an omitted role, rewrite an instruction, choose a visual treatment, add a physical fact, or silently repair a dependency.

#### Scenario: Adaptive graph is valid
- **WHEN** each role references only earlier roles and every dependency has reconciled bytes
- **THEN** the host transmits exactly the role's instruction and ordered reference bytes under one durable intent

#### Scenario: Dependency is invalid
- **WHEN** a role cites itself, a later role, an absent role, or an incomplete image
- **THEN** no request for that role is transmitted and the Concept remains unsealed

#### Scenario: Role count is over the frozen limit
- **WHEN** the authored plan contains more than 20 roles
- **THEN** the host creates no effect plan or intent and transmits no provider request

### Requirement: Adaptive effect recovery preserves exact identities

Every role intent and receipt SHALL bind the current checkpoint, pre-render Concept, role id, instruction, dependency hashes, derived output path, provider profile, and request format. Partial completion, ambiguity, reconciliation, safe retry, and credential isolation SHALL retain their existing fail-closed behavior regardless of how many adaptive roles were declared.

#### Scenario: Optional role is removed in a revised proposal
- **WHEN** a new finalized visual plan changes the role set or any role input
- **THEN** prior intents cannot satisfy the new Concept and the new exact effect plan receives distinct identities

#### Scenario: Completed role survives resume
- **WHEN** resume finds a matching succeeded role and unchanged dependency bytes
- **THEN** the host reuses its exact receipt without repeating native authorship or blindly resending the request
