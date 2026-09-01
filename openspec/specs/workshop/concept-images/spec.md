## Purpose

The concept image set is the concrete visual answer to an abstract Wish: a locked brief of physical facts plus a group of images that all depict one and the same design, sealed so that what Make is shown cannot drift from what Make was handed.

## Requirements

### Requirement: Dormant Concept source is complete before rendering

A dormant pre-render Concept contract SHALL lock the brief, research, drawing instructions, derived Wish, and path-only descriptor before image bytes can be accepted into a sealed form. Structural validation SHALL enforce required physical facts and attribution without invoking a renderer.

#### Scenario: Source is validated before rendering
- **WHEN** a pre-render Concept is evaluated
- **THEN** all source documents and output paths are validated
- **AND** no image byte is required, generated, or claimed

### Requirement: Dormant descriptors separate planned paths from sealed bytes

A pre-render descriptor SHALL declare exactly one safe distinct output path for `front`, `top`, `bottom`, `exploded`, and every component in the brief. A sealed descriptor SHALL additionally bind exactly one regular image and hash for every declared role. Mixed path-only and hashed descriptor leaves MUST be rejected.

#### Scenario: Pre-render descriptor is complete
- **WHEN** every required role has one unique safe path and no image hash
- **THEN** the descriptor is accepted as pre-render only

#### Scenario: Sealed descriptor is incomplete
- **WHEN** a sealed descriptor or manifest lacks any required role or names an unknown component
- **THEN** the sealed Concept is rejected

### Requirement: Dormant image validation proves bytes, not visual quality

Dormant validation SHALL require drawing instructions to carry the locked design facts, a shared bounded presentation treatment, and deterministic prior-role references. A sealed Concept SHALL derive one stable identity from canonical source documents, descriptor, manifest, and image bytes. It MUST reject unsafe paths, links, special nodes, duplicate roles, hash mismatch, and post-seal drift.

It MUST NOT claim that unrendered paths or structurally valid image bytes visually depict the same design, are buildable, are printable, or constitute product evidence.

#### Scenario: Reference ordering is inconsistent
- **WHEN** a role omits a required earlier reference, names an unavailable reference, or depends on a later role
- **THEN** structural validation rejects the instruction set

#### Scenario: Tree is unchanged
- **WHEN** the complete sealed tree is rehashed without byte changes
- **THEN** it reproduces the same sealed identity

#### Scenario: Sealed image bytes are structurally valid
- **WHEN** every image hash and path matches
- **THEN** validation proves byte identity and role completeness only
- **AND** it makes no visual-quality or physical-evidence claim

### Requirement: Dormant Concept bytes stay outside current products

Dormant Concept bytes SHALL NOT enter current Make packets, product trees, Release packages, Factory handoffs, evidence records, or public media. This change MUST NOT add a concept-pixel comparison to current Make because no current Make route consumes Concept.

#### Scenario: Current product run completes
- **WHEN** a Spark, Forge, or Quest run reaches terminal Release
- **THEN** no dormant Concept source or image byte appears in its artifacts or publication handoff
