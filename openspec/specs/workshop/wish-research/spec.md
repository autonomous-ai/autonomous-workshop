## Purpose

Wish research is the step that turns a person's words into the physical facts a design can actually be built from. It reads the Wish against real-world knowledge — what the named object is, how big it really is, what parts it is made of — and returns a breakdown in which every number is either taken from a named source or recorded as a decision the Workshop made, so that Concept, Make, and CAD work from findings rather than from placeholders.

## Requirements

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
