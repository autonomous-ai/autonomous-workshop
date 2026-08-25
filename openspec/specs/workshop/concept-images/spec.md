## Purpose

The concept image set is the concrete visual answer to an abstract Wish: a locked brief of physical facts plus a group of images that all depict one and the same design, sealed so that what Make is shown cannot drift from what Make was handed.

## Requirements

### Requirement: A concept locks its design facts before it draws

A `ConceptImages` SHALL carry a `ConceptBrief` of the design's decided physical facts, and those facts SHALL be settled before any image is produced so that every image is drawn against the same numbers. The brief SHALL record what the object is, its category, its approximate envelope in millimetres, its wall thickness in millimetres, its distinctive features, its intended print orientation and support use, its component breakdown, any fit target it must accommodate, and the assumptions Concept made where the Wish was silent.

The brief is the design's complete description, and it SHALL be complete independently of any image. Text does not occlude: a component hidden behind another in every external view is still fully stated in the brief. Accordingly the brief SHALL describe each component in its own right — its form, its bounding dimensions in millimetres, where it sits in the assembly, and how it meets its neighbours — in enough detail to draw that component without reading its shape off another image.

#### Scenario: The brief carries the numbers the geometry hangs on

- **WHEN** a `ConceptBrief` is produced
- **THEN** it states an envelope of three positive millimetre dimensions and a positive wall thickness
- **AND** where the design must fit or hold something, it states that target's own dimensions and the clearance around it

#### Scenario: Every component is specified, not merely named

- **WHEN** a `ConceptBrief` names a component
- **THEN** it states that component's form, its bounding dimensions in millimetres, its placement in the assembly, and its interfaces to adjoining components
- **AND** a component carrying only a name and purpose is rejected

#### Scenario: Hidden geometry is specified in the brief

- **WHEN** a component is not visible in any external view of the assembled design
- **THEN** the brief still states its form, dimensions, placement, and interfaces in full

#### Scenario: Silence in the Wish becomes a recorded assumption

- **WHEN** the Wish does not determine a fact the brief must state
- **THEN** Concept decides it and records the decision in the brief's assumptions
- **AND** the brief is never left with an invented number presented as if the Wish supplied it

#### Scenario: A brief missing required facts is refused

- **WHEN** a `ConceptBrief` is constructed without an object, an envelope, a wall thickness, or at least one component
- **THEN** construction fails with a contract error

### Requirement: A concept provides the overall views, an exploded view, and one view per component

A `ConceptImages` SHALL contain exactly one image for each of the overall roles `front`, `top`, `bottom`, and `exploded`, and exactly one image for each component named in its brief. Each image SHALL be a distinct regular file inside the concept root, referenced by a relative path that escapes neither the root nor the permitted image formats.

The `exploded` view SHALL show every component of the design separated along its assembly axes, each one wholly visible and none hidden behind another. It exists so that no component has to be drawn from a view that does not show it.

#### Scenario: The required overall views are present

- **WHEN** a `ConceptImages` is constructed
- **THEN** it names an image for `front`, for `top`, for `bottom`, and for `exploded`
- **AND** a set missing any of those four is rejected

#### Scenario: The exploded view shows every component unoccluded

- **WHEN** the `exploded` image is requested
- **THEN** the request names every component in the brief and asks for each one separated and wholly visible
- **AND** it asks that no component be hidden behind, inside, or overlapping another

#### Scenario: Every component is drawn

- **WHEN** a brief names N components
- **THEN** the concept names exactly N component images, one per component key
- **AND** a component image whose key does not appear in the brief is rejected
- **AND** a brief component with no image is rejected

#### Scenario: Image paths are safe and distinct

- **WHEN** a concept names its images
- **THEN** each path is relative, contains no parent traversal, resolves inside the concept root, and ends in a permitted image suffix
- **AND** no two roles share the same file

### Requirement: Every image in a concept depicts one same design

The images in a concept SHALL be mutually consistent renderings of a single object, not independent interpretations of the brief. Consistency SHALL be carried by two separate anchors, because the two things an image must inherit fail differently:

- **Geometry comes from the brief**, which is complete and cannot occlude. Every image request SHALL carry the brief's physical facts, and a component request SHALL additionally carry that component's own specified form, dimensions, placement, and interfaces.
- **Appearance comes from the image anchor.** Every image after the first SHALL be produced with earlier images of the set supplied as visual references, and SHALL be asked to preserve their material, finish, palette, surface treatment, and form language — properties that are global to the object and therefore observable no matter which parts a given view happens to hide.

A request SHALL NOT instruct the model to reproduce a component's shape "as it appears in" a reference image unless that component is wholly visible in a reference supplied with that request. Where the shape is not visible, the specification governs and the reference supplies appearance only.

#### Scenario: Images are produced in an order that accumulates references

- **WHEN** a concept is produced
- **THEN** `front` is produced first, from the brief alone
- **AND** `top` and `bottom` are produced with `front` supplied as a reference
- **AND** `exploded` is produced with `front`, `top`, and `bottom` supplied as references
- **AND** each component image is produced with `exploded` and `front` supplied as references

#### Scenario: Other overall views are asked for as edits

- **WHEN** the `top` or `bottom` image is requested
- **THEN** the request identifies the references as the same object and asks for it unchanged from a different angle
- **AND** the request preserves the references' shape, proportion, features, material, and finish, changing only the viewpoint

#### Scenario: A component view is specified, not read off an occluded image

- **WHEN** a component image is requested
- **THEN** the request carries that component's specified form, dimensions, placement, and interfaces from the brief
- **AND** it asks for the component shown alone, matching the way it appears in the exploded view
- **AND** it inherits material, finish, and form language from the references rather than the component's shape

#### Scenario: A component hidden in the overall views is still drawn faithfully

- **WHEN** a component is occluded in `front`, `top`, and `bottom`
- **THEN** its image is still produced, from its brief specification and its appearance in the exploded view
- **AND** the request does not ask the model to infer its shape from a view that does not show it

#### Scenario: The locked facts reach every image

- **WHEN** any image in the set is requested
- **THEN** the request carries the brief's physical facts as constraints to be respected exactly

#### Scenario: The set shares one presentation treatment

- **WHEN** any image in the set is requested
- **THEN** the request asks for a neutral flat design-study presentation with no dramatic lighting, staged scene, reflections, or background props
- **AND** it excludes text, dimensions, logos, watermarks, people, and hands

#### Scenario: An inconsistent set is not returned

- **WHEN** any image a later request depends on cannot be produced
- **THEN** no dependent image is produced and the concept fails

### Requirement: The exploded view is checked against the brief before components are drawn

Because every component image depends on it, the `exploded` view SHALL be checked for component completeness before any component image is produced. The check SHALL confirm the exploded view depicts as many distinct separated parts as the brief names. A concept whose exploded view does not account for every component SHALL be regenerated once and then fail rather than proceed.

#### Scenario: A complete exploded view proceeds

- **WHEN** the exploded view depicts a distinct separated part for every component in the brief
- **THEN** component image generation proceeds

#### Scenario: An incomplete exploded view is regenerated once

- **WHEN** the exploded view accounts for fewer parts than the brief names
- **THEN** it is regenerated once with the missing components named explicitly
- **AND** if it is still incomplete the concept fails rather than drawing components from it

### Requirement: A concept says what each of its images is, outside the pixels

Every image in a concept SHALL be identified by role — `front`, `top`, `bottom`, `exploded`, or the key of a named component — and that identification SHALL NOT depend on reading the image. A concept SHALL be self-describing on disk: its root SHALL contain a descriptor file recording the brief and the role of every image, and each image's filename SHALL match its role, so that a reader with only the directory can tell the views apart.

Roles SHALL NOT be captioned into the image pixels. Concept images are supplied as references to an image model that is asked to preserve what it sees, so text inside a reference is text the next image may inherit. The same reasoning already bars text, dimensions, logos, and watermarks from every concept prompt.

#### Scenario: The concept root describes itself

- **WHEN** a concept is produced
- **THEN** its root contains a descriptor file recording the brief and a role-to-path entry for every image in the set
- **AND** the descriptor names exactly the images the set contains, with no entry pointing at a missing file and no image absent from it

#### Scenario: Filenames carry the role

- **WHEN** a concept names its image files
- **THEN** each overall image's filename identifies its role
- **AND** each component image's filename identifies the component key it depicts

#### Scenario: The role is never read off the picture

- **WHEN** a consumer needs to know which view an image is
- **THEN** it can determine this from the record, the descriptor, or the filename
- **AND** no consumer is required to interpret the image contents to identify it

#### Scenario: No captions are burned into the images

- **WHEN** any image in the set is requested
- **THEN** the request excludes text, dimensions, logos, and watermarks
- **AND** the produced images carry no role caption in their pixels

#### Scenario: A descriptor that disagrees with the files is refused

- **WHEN** a concept's descriptor names a role whose file is absent, or omits an image present in the set
- **THEN** the concept is rejected with a contract error

### Requirement: A concept is sealed to its exact bytes

A `ConceptImages` SHALL be sealed by a content-addressed manifest over its root, yielding a `concept_sha256` that identifies the exact brief and image bytes. Because the descriptor file lives in the root, the brief and the role assignments are covered by the same seal as the pixels: a concept cannot have its images relabelled without changing its hash. The concept SHALL be re-checkable, and any use of a concept whose bytes changed after it was sealed SHALL be refused.

#### Scenario: Sealing produces a stable identity

- **WHEN** a concept is sealed
- **THEN** it exposes a `concept_sha256` derived from its descriptor and every image file in its root

#### Scenario: Relabelling changes the identity

- **WHEN** a sealed concept's descriptor is edited to assign an image a different role
- **AND** the concept is re-checked
- **THEN** the check fails, because the descriptor is sealed alongside the images

#### Scenario: Tampering is caught at the next boundary

- **WHEN** a file under a sealed concept root is added, removed, or modified
- **AND** the concept is re-checked
- **THEN** the check fails with an artifact error

#### Scenario: Symlinked content is refused

- **WHEN** a concept root or any image path within it is a symlink
- **THEN** the concept is rejected

### Requirement: Concept art directs the build but never evidences it

A concept image is an **instruction**, not **evidence**. It says what should be built; it cannot attest to what was built. Both statements about a concept hold at once and do not compete: Make is required to build to the concept, and the concept is forbidden from standing in for a picture of the result.

This prohibition SHALL hold at the level of bytes, not merely of types. It is not enough that a concept record is its own distinct contract — the pixels themselves SHALL NOT reappear as product proof, however they were copied there. The closer Make comes to building what the concept shows, the more plausible the substitution becomes and the more it would conceal: a divergence between what was designed and what was actually made is exactly what a product record exists to reveal.

Customer-facing page media is generated by Factory from the sealed Make model, so no creator-supplied image mapping exists for a concept to occupy. The byte-level prohibition therefore lands at the Make boundary and on the sealed Instructions tree that Factory receives.

#### Scenario: Concept pixels cannot reappear as product proof

- **WHEN** a file in a `Made` product has the same bytes as any image in the concept the product was built from
- **THEN** it is rejected, regardless of its filename, role, or location

#### Scenario: No concept bytes reach the Factory handoff

- **WHEN** the Instructions tree is sealed for a product built from a concept
- **THEN** no file in that sealed tree has the bytes of any image in that concept

#### Scenario: Creator-supplied page media cannot be configured at all

- **WHEN** an integration supplies Instructions with an image provider, concept-backed or otherwise
- **THEN** it is rejected before the run starts, because Factory owns page media

#### Scenario: A faithful build does not license the substitution

- **WHEN** a product is built so closely to its concept that the concept images resemble it
- **THEN** the concept images are still refused as product proof
- **AND** the product record must still describe the artifact that was actually produced

#### Scenario: Concept images are labelled as concept art

- **WHEN** a concept image records its provenance
- **THEN** that provenance marks it as concept art
- **AND** it is distinguishable from a render of an actually-built artifact
