## ADDED Requirements

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
