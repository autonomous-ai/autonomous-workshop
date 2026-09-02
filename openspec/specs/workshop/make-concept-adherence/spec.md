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

### Requirement: Marked Forge and Quest Make require the standing sealed Concept

For a run with the active Invent Concept capability, every Forge or Quest Make packet SHALL bind the exact accepted sealed Concept contract, whole-tree identity, manifest, derived Wish, brief, descriptor roles, effect receipt, and their artifact paths. It SHALL also expose `required_product_component_keys` as the ordered exact copy of the sealed brief's stable component keys. The Make proposal and sealed Made result SHALL carry the same Concept identity. A missing, stale, changed, cross-round, or substituted binding SHALL be refused. Spark and unmarked runs SHALL retain their existing Made shape.

#### Scenario: Make begins after active Invent
- **WHEN** the host prepares Make for a marked Forge or Quest round
- **THEN** its packet names the exact standing sealed Concept and effect receipt
- **AND** it directly names the stable product component keys without requiring the Manager to infer them from nested contracts
- **AND** the expected Made contract requires that Concept identity

#### Scenario: Make proposes a different Concept
- **WHEN** the product names a Concept other than the one bound by its packet
- **THEN** the proposal is refused without consuming the Make gate

### Requirement: Make independently rehashes Concept and matches its components

Before accepting a marked Forge or Quest product, the Make finalizer and host gate SHALL independently rehash the complete sealed Concept tree and require exact correspondence between stable brief component keys and the product's declared component inventory. Missing or extra components, changed Concept bytes, or product metadata that cannot identify each counterpart SHALL refuse the product. The host SHALL decide this correspondence from exact declarations and MUST NOT ask a model to infer components from pixels.

#### Scenario: Product and brief component sets match
- **WHEN** every brief component key has exactly one product counterpart and no extra product component exists
- **THEN** the deterministic correspondence check passes

#### Scenario: Product omits or adds a component
- **WHEN** the product inventory differs from the sealed brief's stable component keys
- **THEN** Make is refused with the missing or extra keys named

### Requirement: Marked Make authors receive the complete product metadata contract

The routed Make reference SHALL show a canonical `product.json` skeleton for a
marked Concept packet, identify `required_product_component_keys` as its exact
source, and distinguish stable Concept component keys from
implementation-specific CAD variants and repeated physical instances. It SHALL
state that each required key appears exactly once
and that aliases, variant suffixes, duplicates, omissions, and extras are
invalid. A Manager MUST NOT need to inspect finalizer implementation, read an
unrouted compatibility reference, or discover the marked metadata shape only
after completing final CAD verification.

#### Scenario: A Manager starts marked Make
- **WHEN** it reads the stage-routed Make reference and current packet
- **THEN** it can write conforming product metadata before detailed CAD work
- **AND** the distinction between Concept components, implementation variants, and repeated physical instances is explicit

#### Scenario: A protected cache directory remains empty
- **WHEN** native CAD tooling leaves a sandbox-protected byte-free `__cadgen__` directory
- **THEN** routed Make and CAD guidance tell the Manager to leave it for the finalizer and trusted host
- **AND** the Manager does not report that empty directory as a product blocker

### Requirement: Concept governs design without contaminating product bytes

Make SHALL use the sealed Concept's brief as authority for numerical physical constraints and its images as design direction for form and relationships. It SHALL NOT silently accept a materially different design. The complete product tree SHALL be checked against every sealed Concept image byte at every depth, and any identical Concept image content in the product tree SHALL be refused; faithful geometry and newly rendered product views remain allowed.

#### Scenario: Product follows the design with new renders
- **WHEN** geometry follows the brief and visual direction but product renders are generated from the actual product
- **THEN** Concept adherence does not reject them merely for visual similarity

#### Scenario: A Concept image is copied into the product
- **WHEN** any product file has bytes identical to a sealed Concept image
- **THEN** the Make gate refuses the product regardless of path or filename

### Requirement: Build-blocking Concept defects return through Invent

If exact evidence proves that the sealed Concept itself prevents any conforming printable build, the existing marked Make-to-Invent edge SHALL bind the standing Concept identity and receipt in addition to the Wish, assignment, Invented, source, and evidence tree. Normal CAD defects remain Make's responsibility. A valid backward edge SHALL invalidate the active Invent result, Concept, Make, and all downstream artifacts under the one shared lifecycle revision budget.

#### Scenario: Concept is internally impossible to build
- **WHEN** Make proves a contradiction between binding Concept constraints that prevents every conforming product
- **THEN** the host may return the marked run to Invent with exact Concept-bound evidence

#### Scenario: A repairable CAD defect occurs
- **WHEN** the product can conform to the Concept after geometry or implementation repair
- **THEN** Make remains active and cannot use the Invent revision edge
