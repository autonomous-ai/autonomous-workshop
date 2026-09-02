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

### Requirement: Marked Invent researches before locking the physical brief

For a marked Forge or Quest run, the native Manager and selected Inventor SHALL perform required Wish research inside the existing Invent Goal before finalizing the Concept brief. The host SHALL NOT compose queries, choose sources, generate findings, supply default facts, or run a separate research agent or stage. Deliberate design decisions MAY remain unsourced only when they are explicitly recorded with their reason under the Concept attribution rules.

#### Scenario: Initial marked Invent authors a brief
- **WHEN** the Wish contains factual uncertainties relevant to dimensions, construction, fit, object structure, or constraints
- **THEN** Invent records bounded sources and findings before locking those facts
- **AND** every required brief fact has exactly one source or reasoned design-decision attribution

#### Scenario: No source exists for a design choice
- **WHEN** a required fact is a deliberate invention rather than an externally discoverable fact
- **THEN** the native session records the decision and its reason
- **AND** it does not fabricate a source attribution

### Requirement: Research remains bound, exact, and non-evidentiary

The accepted Concept SHALL seal the exact research record and derived Wish together with the physical brief and images. The derived Wish SHALL preserve the routed product id, objective, context, and Wish identity exactly while carrying researched constraints separately. Research SHALL direct Invent and Make but MUST NOT count as CAD, Playtest, Release, manufacture, or delivery evidence.

#### Scenario: Research bytes change after Invent
- **WHEN** the sealed research record or derived Wish changes before a later gate rehashes it
- **THEN** the Concept identity no longer matches and the later boundary fails closed

#### Scenario: Derived Wish rewrites the request
- **WHEN** researched constraints are accompanied by a changed objective, product id, context, or routed Wish identity
- **THEN** the compound Invent gate refuses the Concept

### Requirement: Research failure waits at Invent without placeholders

If the native session cannot obtain enough trustworthy information to decide the required physical facts, it SHALL finalize a concrete waiting or failed need for `invent` rather than author a placeholder breakdown. Resume SHALL continue the same session, checkpoint, Goal scope, and round. A Concept image effect MUST NOT start until complete attributed source passes the compound finalizer and host validation.

#### Scenario: Research capability is unavailable
- **WHEN** required factual research cannot be performed safely
- **THEN** the run waits or fails at `invent` with the missing condition named
- **AND** no default envelope, wall thickness, feature, component, source, or image is substituted

#### Scenario: Research is structurally incomplete
- **WHEN** a submitted fact cites an absent source or lacks a recorded decision reason
- **THEN** the finalizer or host rejects the authored source for repair inside Invent
- **AND** no provider transmission occurs

### Requirement: Re-Invent reuses exact valid research and changes only justified facts

On a Concept revision, the Invent packet SHALL provide the exact prior research, standing brief, sealed Concept, and revision feedback. The native session SHALL reuse unchanged supported findings and SHALL research again only where the revision exposes a factual gap or invalidates prior support. Every changed required fact SHALL receive fresh valid attribution, and stale prior research identities SHALL be refused.

#### Scenario: Feedback changes only a deliberate mechanism
- **WHEN** the prior factual research remains applicable to a revised design decision
- **THEN** the new Concept may preserve those exact research records
- **AND** it records the changed decision and reason without repeating unrelated research

#### Scenario: Feedback invalidates a researched dimension
- **WHEN** the revision changes a fact that was previously source-backed
- **THEN** the replacement fact must bind applicable source evidence or an explicit reasoned decision
