## ADDED Requirements

### Requirement: Current Make remains Concept-free

Current Make packets, finalizers, gates, Made contracts, rejection recovery, and Make-to-Invent revision SHALL remain unchanged. Spark SHALL continue to seal folded assignment, Invented, and Made provenance in Make; Forge and Quest SHALL continue to consume the exact Invent output. No current Make boundary SHALL require, accept, infer, or emit a dormant Concept identity, descriptor, image role, or image byte.

#### Scenario: Current Make packet is prepared
- **WHEN** Spark, Forge, or Quest enters Make
- **THEN** the packet contains only the inputs required by the frozen current route
- **AND** it contains no dormant Concept binding

#### Scenario: Current Made contract is sealed
- **WHEN** Make passes its existing host gate
- **THEN** its identity fields and CAD requirements are unchanged
- **AND** no Concept hash is emitted

### Requirement: Current revision routing bypasses dormant Concept

Quest Playtest feedback SHALL continue to use the current implementation-repair edge to Make and fundamental-revision edge to Invent. Forge and Quest Make-to-Invent revision SHALL keep its existing evidence-bound behavior. Concept MUST NOT become an invalidation target. A later merged-boundary activation SHALL route both design- and invention-level revision to Invent for Forge/Quest, distinguish their feedback there, and update the shared lifecycle revision budget without adding a Concept edge.

#### Scenario: Quest requires a fundamental revision
- **WHEN** valid feedback crosses the current fundamental-revision boundary
- **THEN** the route returns to Invent under its existing rules
- **AND** it does not enter dormant Concept

## REMOVED Requirements

### Requirement: Make is told which image is which
**Reason**: Current Make receives no Concept images.
**Migration**: Keep roles in dormant descriptors and extend Make's packet only after the owning creative stage seals the merged Concept boundary.

### Requirement: Building to the concept does not put concept pixels in the product
**Reason**: Current Make does not consume Concept, so adding a pixel gate would alter a live boundary prematurely.
**Migration**: Keep dormant Concept bytes outside current product wiring and restore adherence checks only when Make is versioned to consume them.

### Requirement: The Workshop verifies the concept binding at the Make boundary
**Reason**: Current Made contracts have no Concept identity.
**Migration**: Merged-boundary activation must version the owning creative-stage receipt, Made binding, and exact rehash together.

### Requirement: A failed Playtest revises the design, not only the build
**Reason**: ADR 0016 currently routes fundamental feedback to Invent, not Concept.
**Migration**: Preserve Make for build-only feedback and use Invent for both design- and invention-level feedback after merged activation, without changing frozen older runs.

### Requirement: The Make stage packet carries the round's concept
**Reason**: No current round has a standing Concept.
**Migration**: Add this input only through a new frozen route capability whose owning Invent or folded Make boundary sealed that Concept.

### Requirement: Make builds to the concept
**Reason**: Current Make builds from the exact Invented provenance or Spark's folded creative work.
**Migration**: Keep current inputs authoritative until merged-boundary activation defines sealed Concept precedence.
