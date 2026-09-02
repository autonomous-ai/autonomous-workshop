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

### Requirement: Active Invent source locks design before host rendering

In a marked Forge or Quest run, the native Invent finalizer SHALL lock the brief, research, drawing instructions, derived Wish, and path-only descriptor before any image effect starts. The host SHALL render only from that accepted pre-render identity and MUST NOT edit, default, or repair design content between source validation and transmission.

#### Scenario: Valid source reaches the renderer
- **WHEN** all required source documents pass independent host validation
- **THEN** every image request is derived from those exact locked bytes
- **AND** later host processing cannot substitute a physical fact or instruction

#### Scenario: Source is edited after finalization
- **WHEN** any locked source byte changes before or during rendering
- **THEN** the image set cannot be sealed for that proposal
- **AND** the altered source requires a newly finalized Invent proposal

### Requirement: Every required role is rendered and sealed for active Invent

The active sealed Concept SHALL contain exactly one image for `front`, `top`, `bottom`, `exploded`, and every stable component key in the brief. Each role SHALL match its declared safe distinct path and exact returned hash. A missing, extra, duplicate, mixed-state, or changed role SHALL prevent Invent from advancing.

#### Scenario: All roles complete
- **WHEN** every validated overall and component instruction has one reconciled returned image
- **THEN** the sealed descriptor and manifest cover exactly those roles and bytes
- **AND** the whole-tree identity is reproducible by independent rehashing

#### Scenario: One component view is missing
- **WHEN** the provider has not completed a role for one brief component
- **THEN** the Concept remains unsealed
- **AND** the run cannot reach Make

### Requirement: Active Concept images direct Make but remain non-evidentiary

The sealed images SHALL communicate the intended form, proportions, features, component relationships, and assembly views to Make. Numerical physical facts in the brief SHALL prevail if pixels imply a conflicting dimension. Concept images and research MUST remain outside product proof, signature-review evidence, Playtest evidence, and Release claims, and their exact bytes MUST NOT be copied into the product tree.

#### Scenario: An image and brief disagree on size
- **WHEN** Make reads a visual proportion that conflicts with an explicit millimetre fact
- **THEN** Make follows the brief's numerical fact
- **AND** it does not rewrite the sealed Concept

#### Scenario: Concept pixels are offered as product evidence
- **WHEN** a later gate receives a Concept image as evidence that the product exists or works
- **THEN** the evidence is refused
