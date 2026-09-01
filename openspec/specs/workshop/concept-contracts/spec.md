# concept-contracts Specification

## Purpose

Defines dormant, content-addressed Concept data and deterministic validation that can be tested and packaged before any current Workshop lifecycle route is changed.

## Requirements

### Requirement: Concept contracts are dormant infrastructure

Workshop SHALL expose Concept contract parsing, canonical serialization, exact-byte validation, and structural evaluation without adding Concept to an executable lifecycle. Constructing, parsing, or evaluating a Concept contract MUST NOT create a stage packet, native turn, Goal, checkpoint transition, wait state, gate record, credential read, network request, or external effect.

The contract boundary SHALL remain suitable for later composition into the first active creative stage. Its data model MUST NOT require or encode a standalone Concept stage, Concept transition, or Concept-only checkpoint.

#### Scenario: A valid contract is evaluated on current main
- **WHEN** a caller evaluates a valid dormant Concept contract
- **THEN** the caller receives only deterministic validation output
- **AND** the frozen Spark, Forge, or Quest checkpoint is unchanged

#### Scenario: Dormant code is imported
- **WHEN** the Concept contract package is imported or its schema is discovered
- **THEN** no workflow, runtime, credential, or integration side effect occurs

#### Scenario: Contract provenance is used by a later route
- **WHEN** a later route binds a valid Concept contract to its owning creative stage
- **THEN** the contract identity requires no standalone Concept lifecycle identity

### Requirement: Every Concept identity binds its complete creative provenance

A Concept contract SHALL bind the exact routed Wish identity, product id, objective, context, roster-bound assignment, selected Taste, universal blueprint, Invented contract, authored creative-source bytes, round, and revision inputs. The provenance SHALL identify whether the assignment and Invented contracts originated in a Forge/Quest Invent source or a Spark folded selection-and-Make source, while applying the same exact identity checks to both origins.

The contract MUST reject a source whose embedded assignment, Taste, blueprint, Invented, Wish, or origin identity disagrees with the accepted upstream contracts. Supporting the Spark origin in the dormant type MUST NOT change Spark's current Make finalizer or artifact set.

#### Scenario: Forge or Quest provenance matches
- **WHEN** a Concept contract declares an Invent origin and names the exact preserved Invent source, assignment, Invented contract, Taste, blueprint, and routed Wish identities
- **THEN** provenance validation accepts the input vector

#### Scenario: Spark provenance matches
- **WHEN** a Concept contract declares a Spark folded Make origin and names the exact combined creative source plus the assignment and Invented identities derived from it
- **THEN** provenance validation accepts the input vector without creating a standalone Invent or Concept stage

#### Scenario: Upstream identity is substituted
- **WHEN** any Wish, assignment, Taste, blueprint, Invented, creative-source, origin, or revision identity differs from the expected input vector
- **THEN** validation rejects the Concept as belonging to different Workshop inputs

### Requirement: Concept source and sealed forms have distinct exact identities

The dormant capability SHALL distinguish an authored pre-render Concept from a host-sealed Concept. A pre-render contract SHALL bind canonical brief, research, drawing-instruction, derived-Wish, and path-only descriptor bytes and MUST NOT claim image bytes or a completed Concept seal. A sealed contract SHALL additionally bind one regular image file and SHA-256 for every descriptor role, and its whole-tree identity SHALL cover every source document, descriptor, and image byte.

Both forms SHALL use canonical round-scoped in-run paths, safe relative POSIX paths, bounded regular files, unique manifest entries, strict duplicate-key-rejecting JSON, and one deterministic identity computed from canonical fields. A mixed descriptor containing some hashed and some path-only roles MUST be rejected.

#### Scenario: Pre-render source is valid without images
- **WHEN** every authored source document is valid and every descriptor leaf contains only a safe output path
- **THEN** the pre-render contract is accepted as source-ready
- **AND** it is not accepted as a sealed Concept

#### Scenario: Sealed form covers exact image bytes
- **WHEN** every required image exists as a regular in-root file and its descriptor hash matches its bytes
- **THEN** the sealed identity covers the complete source and image tree

#### Scenario: Descriptor states are mixed
- **WHEN** one descriptor role carries an image hash and another carries only a path
- **THEN** the contract is rejected as neither a valid pre-render nor sealed form

#### Scenario: Sealed bytes change
- **WHEN** any source, descriptor, or image byte is added, removed, or modified after sealing
- **THEN** exact-tree validation rejects the Concept

### Requirement: Structural evaluation rejects incomplete or fabricated design source

The deterministic evaluator SHALL require a bounded brief with an object, category, three positive envelope dimensions, positive wall thickness, print stance, at least one distinctive feature, and at least one fully specified component. Every required fact SHALL name exactly one recorded research source or one explicit decision with its reason. The evaluator SHALL require complete research records, one drawing instruction and safe descriptor path for each overall role and brief component, valid reference ordering, and an exploded instruction that names every component.

The evaluator MUST NOT repair, default, rank, semantically score, render, or add design content. A refusal SHALL identify the violated structural rule.

#### Scenario: A required physical fact is missing
- **WHEN** the brief omits its object, category, envelope, wall thickness, print stance, feature set, or component set
- **THEN** evaluation rejects it and names the missing rule

#### Scenario: A fact has ambiguous attribution
- **WHEN** a required fact names neither a recorded source nor a reasoned decision, or names both
- **THEN** evaluation rejects the fact

#### Scenario: A component is only named
- **WHEN** a component lacks its form, bounding dimensions, placement, or interfaces
- **THEN** evaluation rejects the brief

#### Scenario: Structure is valid
- **WHEN** all brief, research, instruction, descriptor, path, and provenance rules pass
- **THEN** evaluation returns deterministic evidence describing only the checks performed
- **AND** it makes no quality, buildability, printability, or physical-evidence claim

### Requirement: Repair freshness is explicit and fail closed

A Concept contract SHALL carry its exact round and SHALL bind any standing Concept and feedback or revision request supplied for that round. Validation against an expected context MUST reject a contract from an earlier or later round, a contract that omits required revision inputs, or a contract that cites superseded revision bytes.

#### Scenario: Prior-round contract is replayed
- **WHEN** a contract finalized for round 1 is validated against an expected round 2 context
- **THEN** validation rejects it without accepting or mutating any artifact

#### Scenario: Revision input is stale
- **WHEN** a revision contract cites a standing Concept or feedback identity other than the exact expected bytes
- **THEN** validation rejects it as stale

### Requirement: Concept schema is package-owned and discoverable

Workshop SHALL package the Concept JSON schema with the component that owns the contract and SHALL expose it through the existing schema discovery boundary. Built distributions MUST contain the same schema bytes used by source-tree tests.

#### Scenario: Installed schema discovery runs
- **WHEN** schemas are discovered from an installed Workshop distribution
- **THEN** the Concept schema is present and resolves from package data

#### Scenario: Package schema differs
- **WHEN** the packaged Concept schema is missing or differs from the source contract expectations
- **THEN** packaging acceptance fails
