## ADDED Requirements

### Requirement: Dormant Concept research is validated without being performed

Dormant Concept contracts SHALL carry authored research and the exact creative provenance it supports, but this change SHALL NOT start a Concept research turn or perform research in the host. The structural evaluator SHALL only validate supplied bounded records, complete fact attribution, and exact identities.

#### Scenario: Dormant research is evaluated
- **WHEN** a caller supplies a Concept research record
- **THEN** deterministic validation checks its structure and bindings
- **AND** no research tool, model, network call, or lifecycle turn is invoked

#### Scenario: Attribution points outside the research record
- **WHEN** a brief fact cites a source identifier the research record does not contain
- **THEN** validation rejects the fact

### Requirement: Dormant breakdowns remain complete and non-evidentiary

The evaluator SHALL require all physical facts, source-or-decision attribution, and fully specified components needed by the dormant brief. It MUST NOT supply defaults or interpret structural completeness as semantic quality, buildability, printability, Playtest evidence, or Release evidence.

#### Scenario: Physical breakdown is incomplete
- **WHEN** a required envelope, wall thickness, print stance, fit target, feature, or component fact is absent
- **THEN** validation rejects the brief and names the structural omission

#### Scenario: Research is offered as current evidence
- **WHEN** Concept research is supplied to a current product or release evidence boundary
- **THEN** it is refused as evidence

### Requirement: Derived Wish preserves exact routed identity

A dormant derived-Wish record SHALL preserve the routed Wish product id, objective, and context exactly and SHALL carry researched constraints in a separate field with its own canonical identity. Validation MUST reject any derived record that changes the person's original routed Wish words or context.

The record SHALL remain dormant data and MUST NOT be written into current stage packets or downstream jobs by this change.

#### Scenario: Derived constraints preserve routing identity
- **WHEN** a derived-Wish record adds researched constraints while preserving the exact routed Wish fields and identity
- **THEN** contract validation accepts it as dormant Concept source

#### Scenario: Derived record rewrites the Wish
- **WHEN** the derived record changes the product id, objective, or context
- **THEN** validation rejects it even if its own internal hash is canonical

## REMOVED Requirements

### Requirement: Concept researches the Wish before it locks any physical fact
**Reason**: No active Concept research turn exists in this slice.
**Migration**: Preserve research source structure in dormant contracts and add this work to the owning Invent or folded Make Goal only during merged-boundary activation.

### Requirement: A breakdown decides every fact the brief must state
**Reason**: Replaced by route-neutral dormant structural validation.
**Migration**: Keep the same completeness rules without implying an active turn.

### Requirement: Every fact in a breakdown is attributable
**Reason**: Attribution is folded into the new dormant research-validation requirement.
**Migration**: Continue requiring exactly one recorded source or reasoned decision per fact.

### Requirement: A breakdown names the design's real parts
**Reason**: Component completeness is folded into the new dormant breakdown requirement.
**Migration**: Continue rejecting placeholder components structurally.

### Requirement: Research is sealed with the concept it produced
**Reason**: Exact research identity is now owned by the new Concept contracts capability.
**Migration**: Bind the same bytes in pre-render and sealed forms.

### Requirement: Researched constraints are written back without touching the routed Wish
**Reason**: The derived-Wish behavior is retained under a newly named dormant requirement that forbids downstream wiring.
**Migration**: Preserve routed identity exactly and defer propagation until activation.

### Requirement: Research directs the design and never evidences it
**Reason**: Replaced by the explicit non-evidentiary dormant breakdown requirement.
**Migration**: Keep research outside current evidence boundaries.

### Requirement: Research that cannot be done is refused, never approximated
**Reason**: No active Concept research turn or lifecycle wait exists in this dormant slice.
**Migration**: A later activation change must define how the owning creative Goal reports incomplete research and how any wait remains bound to that Invent or Make checkpoint and exact round.
