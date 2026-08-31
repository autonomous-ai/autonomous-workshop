## ADDED Requirements

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

## REMOVED Requirements

### Requirement: A concept locks its design facts before it draws
**Reason**: The active drawing behavior is split into dormant source validation and a later rendering protocol.
**Migration**: Use the new dormant source-completeness requirement before implementing image effects.

### Requirement: A concept carries the research its brief was decided from
**Reason**: Research identity is now defined by the dormant Concept contract capability, independently of rendered pixels.
**Migration**: Preserve the same exact research bytes in both pre-render and sealed forms.

### Requirement: A concept provides the overall views, an exploded view, and one view per component
**Reason**: This slice declares role paths and validates sealed bytes but does not promise images are generated.
**Migration**: The later rendering protocol must fulfill every validated role before sealing.

### Requirement: Every image in a concept depicts one same design
**Reason**: Structural validation cannot prove semantic visual consistency, and no renderer is active.
**Migration**: Preserve reference and instruction constraints; leave visual judgment to the future native workflow.

### Requirement: A concept says what each of its images is, outside the pixels
**Reason**: Replaced by the explicit dormant descriptor-state requirement.
**Migration**: Keep canonical external role descriptors and never infer roles from pixels.

### Requirement: A concept is sealed to its exact bytes
**Reason**: Exact sealing is moved to the route-neutral dormant Concept contract capability.
**Migration**: Use the new pre-render/sealed forms and whole-tree identity.

### Requirement: Concept art directs the build but never evidences it
**Reason**: Concept does not direct current Make routes while dormant.
**Migration**: Keep Concept bytes outside current products and define future Make adherence only when the merged creative-stage boundary is activated.
