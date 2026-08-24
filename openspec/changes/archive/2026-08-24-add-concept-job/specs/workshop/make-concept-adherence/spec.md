## Purpose

Defines what Make receives from Concept and what following a concept actually obliges it to do — which parts of the concept are binding, what the Workshop checks at the boundary, and how a rejected build revises the design rather than only the geometry.

## ADDED Requirements

### Requirement: MakeContext carries the round's concept

`MakeContext` SHALL gain a `concept_images` field carrying the sealed `ConceptImages` for that round. The field SHALL be optional and SHALL default to absent, so a `MakeContext` constructed without one remains valid and behaves as it did before Concept existed.

#### Scenario: The round's concept reaches Make

- **WHEN** the Workshop builds the `MakeContext` for a round in which Concept produced a concept
- **THEN** that context's `concept_images` is the concept Concept returned for that same round

#### Scenario: Omitting the concept stays valid

- **WHEN** a `MakeContext` is constructed without `concept_images`
- **THEN** construction succeeds and the context reports no concept

#### Scenario: A stale concept is refused

- **WHEN** a `MakeContext` is constructed with a concept whose bytes have changed since it was sealed
- **THEN** construction fails with an artifact error

#### Scenario: A concept from another round is refused

- **WHEN** a `MakeContext` for round N is constructed with a concept produced for a different round
- **THEN** construction fails with a contract error

### Requirement: Make is told which image is which

A concept SHALL reach Make with every image identified by role. Where the images are presented to an agent as attachments, the accompanying text SHALL name each one in the order supplied — which is the front view, which is the top, which is the bottom, which is the exploded view, and which component each remaining image depicts. Make SHALL never have to infer an image's role from its contents.

The text SHALL also state the images' standing relative to each other: the overall views establish form and proportion, the exploded view establishes the part breakdown, and each component image establishes one part.

#### Scenario: Attached images are named in order

- **WHEN** a concept's images are supplied to an agent-backed Make as attachments
- **THEN** the accompanying text identifies each attachment by position and role
- **AND** every attachment supplied is named, and no name refers to an attachment that was not supplied

#### Scenario: A programmatic Make reads roles from the record

- **WHEN** a Make implementation consumes the concept directly rather than as attachments
- **THEN** it obtains each image's role from the concept record or its on-disk descriptor

#### Scenario: The component images map to brief components

- **WHEN** component images are supplied
- **THEN** each is identified by the component key it depicts
- **AND** that key matches a component named in the brief

### Requirement: Make builds to the concept when one is present

When `concept_images` is present, it SHALL be the primary reference for the product's form, proportion, construction, and component breakdown. The Wish objective remains the statement of what the person asked for, and the brief's millimetre facts remain the binding physical constraints; where the images and the brief's numbers disagree, the numbers govern. Make SHALL NOT silently produce a product that is a different design from the one visualized.

#### Scenario: The concept governs form

- **WHEN** Make runs with a concept present
- **THEN** the product it returns follows the concept's silhouette, proportions, and distinctive features

#### Scenario: The brief's numbers outrank the pictures

- **WHEN** an image and the brief's stated envelope, wall thickness, or clearance imply different geometry
- **THEN** Make builds to the brief's stated numbers

#### Scenario: The component breakdown carries through

- **WHEN** Make returns a product built from a concept
- **THEN** the product's component list matches the components named in the concept's brief

#### Scenario: Make cannot build the visualized design

- **WHEN** the concept cannot be realized as printable geometry
- **THEN** Make raises a need or fails, rather than returning a product that quietly departs from the concept

#### Scenario: No concept present

- **WHEN** Make runs with no concept in its context
- **THEN** it behaves exactly as it did before Concept existed

### Requirement: Building to the concept does not put concept pixels in the product

Make follows the concept as direction; it SHALL NOT emit the concept's own images as part of the product it returns. A `Made` artifact SHALL NOT contain a file whose bytes match any image in the concept it was built from, and the Workshop SHALL refuse such a product.

The two obligations are complementary, not competing: the concept says what to build, and the artifact must show what was built. A product that ships the drawing instead of a picture of the thing has satisfied neither.

#### Scenario: A product carrying concept pixels is refused

- **WHEN** Make returns a product whose artifact tree contains a file with the same bytes as any image in that round's concept
- **THEN** the Workshop rejects the product with a contract error

#### Scenario: Building faithfully is still accepted

- **WHEN** Make returns a product that follows the concept closely but contains none of its image bytes
- **THEN** the product is accepted

### Requirement: The Workshop verifies the concept binding at the Make boundary

The Workshop SHALL re-check the concept's seal when Make returns, so a concept altered while Make was running is caught. It SHALL record which concept the returned product was built from, and it SHALL refuse a product whose declared components contradict the concept's brief.

#### Scenario: The concept is re-checked after Make returns

- **WHEN** Make returns for a round that supplied a concept
- **THEN** the Workshop re-checks that the concept's bytes are unchanged
- **AND** a changed concept fails the round with an artifact error

#### Scenario: The product records its concept

- **WHEN** a product is accepted from a round that supplied a concept
- **THEN** the run records that product's artifact hash together with the concept hash it was built from

#### Scenario: A contradicting component list is refused

- **WHEN** Make returns a product whose components do not match the concept brief's components
- **THEN** the Workshop rejects the product with a contract error

### Requirement: A failed Playtest revises the design, not only the build

Feedback from Playtest SHALL be able to invalidate the concept as well as the build. When feedback invalidates `concept`, the next round SHALL revise the concept before Make runs again, so that a design flaw is corrected in the design rather than worked around in geometry.

#### Scenario: Feedback can name Concept as invalidated

- **WHEN** a `Feedback` item is constructed listing `concept` among the jobs it invalidates
- **THEN** it is accepted

#### Scenario: Design feedback reaches the next concept

- **WHEN** a round's Playtest returns feedback invalidating `concept`
- **THEN** the next round's `ConceptContext` carries that feedback
- **AND** the concept handed to that round's Make reflects the requested change

#### Scenario: Build-only feedback leaves the design standing

- **WHEN** feedback invalidates `make` but not `concept`
- **THEN** the next round's concept is the standing design, revised only as that feedback requires
