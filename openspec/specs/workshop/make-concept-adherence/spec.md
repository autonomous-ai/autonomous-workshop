## Purpose

Defines what Make receives from Concept and what following a concept actually obliges it to do — which parts of the concept are binding, what the Workshop checks at the boundary, and how a rejected build revises the design rather than only the geometry.

## Requirements

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
