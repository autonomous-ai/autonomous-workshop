## Purpose

Defines what Make receives from Concept and what following a concept actually obliges it to do — which parts of the concept are binding, what the Workshop checks at the boundary, and how a rejected build revises the design rather than only the geometry.

## Requirements

### Requirement: Make is told which image is which

A concept SHALL reach Make with every image identified by role in the stage packet's inputs — which is the front view, which is the top, which is the bottom, which is the exploded view, and which component each remaining image depicts. Make SHALL never have to infer an image's role from its contents, because a role read off pixels is a guess, and the point of a sealed concept is that the design was decided.

The packet SHALL also state the images' standing relative to each other: the overall views establish form and proportion, the exploded view establishes the part breakdown, and each component image establishes one part.

Every image the concept sealed SHALL be named, and no name SHALL refer to an image the concept does not contain.

#### Scenario: Attached images are named in order

- **WHEN** the Make packet presents a concept's images to the native turn
- **THEN** its inputs name each image by role, in the order the concept sealed them
- **AND** every image the concept contains is named, and no name refers to an image it does not contain

#### Scenario: A programmatic Make reads roles from the record

- **WHEN** the Make turn resolves which image is the exploded view
- **THEN** it takes that role from the packet's inputs and the concept's on-disk descriptor
- **AND** no image's role is derived from that image's contents

#### Scenario: The images' standing is stated

- **WHEN** the Make packet names the image roles
- **THEN** it states that the overall views establish form and proportion, the exploded view establishes the part breakdown, and each component image establishes one part

#### Scenario: The component images map to brief components

- **WHEN** component images are named
- **THEN** each is identified by the component key it depicts
- **AND** that key matches a component named in the brief

### Requirement: Building to the concept does not put concept pixels in the product

Make follows the concept as direction; it SHALL NOT emit the concept's own images as part of the product it builds. No file in a sealed product tree SHALL carry the same bytes as any image in the concept that round was built from, and the Make gate SHALL refuse such a product.

The two obligations are complementary, not competing: the concept says what to build, and the artifact must show what was built. A product that ships the drawing instead of a picture of the thing has satisfied neither.

#### Scenario: A product carrying concept pixels is refused

- **WHEN** a sealed product tree contains a file with the same bytes as any image in that round's concept
- **THEN** the Make gate refuses the product and the run does not advance to Playtest

#### Scenario: The whole tree is checked

- **WHEN** the Make gate checks a product for concept pixels
- **THEN** it checks every file in the sealed product tree, at any depth and under any name

#### Scenario: Building faithfully is still accepted

- **WHEN** a product follows the concept closely but contains none of its image bytes
- **THEN** the product is accepted

### Requirement: The Workshop verifies the concept binding at the Make boundary

The Make gate SHALL re-check the concept's seal when the Make turn returns, so a concept altered while the turn was running is caught. It SHALL record on the sealed Make result which concept the product was built from, and it SHALL refuse a product whose declared components contradict the concept's brief.

This check is load-bearing in a way it was not before. It is now the only remaining automated guarantee that the built part set is the designed part set, because the Workshop no longer asks a vision model to inspect the exploded view. So the correspondence SHALL be exact and settled in bytes: a component named in the brief with no counterpart in the product, and a component declared by the product with no counterpart in the brief, SHALL each refuse the round — because a divergence between what was designed and what was actually made is exactly what a product record exists to reveal.

#### Scenario: The concept is re-checked after Make returns

- **WHEN** a Make turn returns for a round with a standing concept
- **THEN** the gate re-checks that the concept's bytes are unchanged
- **AND** a changed concept fails the round

#### Scenario: The product records its concept

- **WHEN** a product is accepted for a round
- **THEN** the sealed result records the product's artifact identity together with the concept identity it was built from

#### Scenario: A contradicting component list is refused

- **WHEN** a product declares no component for a component the brief named
- **THEN** the gate refuses the product, naming the missing component

#### Scenario: An extra component is refused

- **WHEN** a product declares a component the brief did not name
- **THEN** the gate refuses the product, naming the extra component

#### Scenario: The check asks no model

- **WHEN** the gate checks component correspondence
- **THEN** it decides from the brief's components and the product's declared components alone
- **AND** no model is asked to look at an image or to agree with the result

### Requirement: A failed Playtest revises the design, not only the build

Playtest feedback SHALL be able to invalidate the concept as well as the build. Where feedback invalidates the design, the run SHALL return through a Concept turn before Make runs again, so a design flaw is corrected in the design rather than worked around in geometry. Where feedback invalidates only the build, the standing concept SHALL remain in force and the next Make turn SHALL run against it unchanged.

A revised concept SHALL be sealed and bound before the Make turn that follows it, so a round's product is always bound to the design that round was actually built to.

#### Scenario: Feedback can name Concept as invalidated

- **WHEN** sealed Playtest feedback lists the concept among the stages it invalidates
- **THEN** it is accepted, and the concept is recorded as invalidated for that round

#### Scenario: Design feedback reaches the next concept

- **WHEN** a round's Playtest fails with feedback invalidating the design
- **THEN** a Concept turn runs before Make runs again
- **AND** that turn's packet carries the standing concept and that feedback
- **AND** the Make round that follows is bound to the revised concept

#### Scenario: Build-only feedback leaves the design standing

- **WHEN** feedback invalidates the build but not the design
- **THEN** the next Make packet names the standing concept unchanged
- **AND** no Concept turn runs for that round

### Requirement: The Make stage packet carries the round's concept

The standing concept SHALL reach Make through the Make stage packet, and the sealed Make result SHALL bind the concept it was built from as `concept_sha256`. The packet SHALL name the concept's identity, its tree, and the role of every image in it; the sealed result SHALL carry that identity forward alongside its other upstream bindings.

Concept is a mandatory stage, so a Make round without a concept does not exist. A Make turn prepared for a round with no standing concept SHALL be refused, and a Make result carrying no concept binding SHALL be refused — there is no longer any path by which Make builds from a title and a summary alone.

A Make result naming a concept whose bytes changed since the gate sealed them SHALL be refused. A Make result naming a concept other than the one its packet bound for that round SHALL be refused, so a design from another round cannot be replayed into this one.

#### Scenario: The round's concept reaches Make

- **WHEN** the host prepares the Make turn for a round
- **THEN** the packet names the standing concept, its identity, and its tree
- **AND** the sealed Make result records that same identity

#### Scenario: A Make round without a concept is refused

- **WHEN** a Make turn is prepared for a round in which no concept was sealed
- **THEN** the turn is refused and the run does not reach Make
- **AND** no Make result lacking a concept binding is accepted

#### Scenario: A stale concept is refused

- **WHEN** a Make result names a concept whose bytes have changed since it was sealed
- **THEN** the Make gate refuses the round

#### Scenario: A concept from another round is refused

- **WHEN** a Make result names a concept other than the one that round's packet bound
- **THEN** the proposal is refused and no gate is consumed

### Requirement: Make builds to the concept

The standing concept SHALL be the primary reference for the product's form, proportion, construction, and component breakdown. The Wish objective remains the statement of what the person asked for, and the brief's millimetre facts remain the binding physical constraints; where the images and the brief's numbers disagree, the numbers govern, because a picture is an impression of a shape and a millimetre is a commitment. Make SHALL NOT silently seal a product that is a different design from the one visualized.

#### Scenario: The concept governs form

- **WHEN** a Make turn runs against a standing concept
- **THEN** the product it seals follows the concept's silhouette, proportions, and distinctive features

#### Scenario: The brief's numbers outrank the pictures

- **WHEN** an image and the brief's stated envelope, wall thickness, or clearance imply different geometry
- **THEN** Make builds to the brief's stated numbers

#### Scenario: The component breakdown carries through

- **WHEN** a product is sealed for a round
- **THEN** its component list matches the components named in the concept's brief

#### Scenario: Make cannot build the visualized design

- **WHEN** the concept cannot be realized as printable geometry
- **THEN** the turn records a waiting or failed outcome carrying a need that says so
- **AND** no product that quietly departs from the concept is sealed
