## ADDED Requirements

### Requirement: Make receives an explicit fixed-view reconstruction map

For a fixed-view sealed Concept, the Make packet SHALL expose a bounded ordered role summary containing front, top, bottom, exploded, and each `component:<key>` image with its exact path and hash. The routed Make guidance SHALL identify the overall views as direct shape references, the exploded image as the assembly and part-identity reference, and each component image as the isolated form and interface reference for its matching stable component key.

#### Scenario: Make starts from a fixed multipart Concept
- **WHEN** the host prepares the Make packet
- **THEN** the role summary deterministically maps every required component key to exactly one isolated image
- **AND** Make does not infer role meaning from filenames, image order, or pixels alone

### Requirement: Fixed views simplify reconstruction without weakening Make proof

Make SHALL reconcile the fixed images with the authoritative normalized brief and construct fresh CAD and product renders. The fixed image inventory MUST NOT waive component equality, fit and interface checks, exact state proof, early form/mechanism review, blind signature review, integrated CAD verification, Concept-pixel exclusion, Quest Playtest, Release verification, or publication requirements.

#### Scenario: Fixed images are visually clear but CAD proof is missing
- **WHEN** Make supplies the complete Concept view set but omits required CAD or signature evidence
- **THEN** the Make finalizer refuses the proposal under the unchanged proof gates
