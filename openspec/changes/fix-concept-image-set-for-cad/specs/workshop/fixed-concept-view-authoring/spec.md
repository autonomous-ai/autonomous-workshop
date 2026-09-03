## Purpose

Defines a versioned Invent authoring contract whose Concept image roles are fixed for CAD reconstruction while creative design content remains owned by the native agent.

## ADDED Requirements

### Requirement: Fixed-view Invent does not choose its image inventory

For a run with the fixed-view capability, Invent SHALL author the consolidated Invent source and one fixed-view instruction document. The required role sequence SHALL be derived from the stable component keys as `front`, `top`, `bottom`, `exploded`, followed by exactly one `component:<key>` role for each component in source-array order. The authored instruction document MUST cover exactly that fixed role set and MUST NOT add, omit, rename, or select roles; JSON object member order is non-semantic.

The total image count SHALL equal `4 + component_count` and MUST NOT exceed the frozen 20-image safety ceiling. An oversized component inventory SHALL be rejected before any image-effect intent or transmission.

#### Scenario: Multipart source declares the exact fixed set
- **WHEN** a valid Invent source declares components `shell`, `core`, and `cap`
- **THEN** its accepted instruction document covers front, top, bottom, exploded, shell, core, and cap in that exact order
- **AND** the Concept declares exactly seven image effects

#### Scenario: Invent adds a perspective or signature role
- **WHEN** an instruction document includes any role outside the derived fixed set
- **THEN** the Invent finalizer rejects it before provider transmission

#### Scenario: Fixed set exceeds the safety ceiling
- **WHEN** the stable component count would require more than 20 total Concept images
- **THEN** normalization rejects the source and no image-effect intent is created

### Requirement: Authored instructions target simple CAD reconstruction

Every fixed-view instruction SHALL be complete when combined with the normalized physical brief and the frozen role prompt. The front, top, and bottom instructions SHALL depict one complete unchanged object from direct orthographic-like camera directions. The exploded instruction SHALL name every stable component and require each to be separated, unobscured, and aligned along an understandable assembly relationship. Each component instruction SHALL depict exactly one complete isolated component and SHALL carry that component's form, measurements, placement, interfaces, and assembly relationship from the normalized source.

All roles SHALL share a plain neutral presentation, consistent orientation and scale, legible silhouette and edges, and no text, dimension annotations, logos, watermarks, people, hands, unrelated props, decorative scene, dramatic lighting, reflections, or depth-of-field effects. Numerical brief facts SHALL remain authoritative when pixels disagree.

#### Scenario: Overall instructions are accepted
- **WHEN** the three overall-view instructions use direct camera directions, preserve the same design, and contain the required plain-presentation constraints
- **THEN** structural validation accepts them as CAD-reconstruction directions

#### Scenario: Component instruction lacks interface facts
- **WHEN** an isolated component instruction does not carry the component's declared mating interfaces
- **THEN** validation rejects the instruction document before rendering

### Requirement: Fixed-view authoring is an additive frozen capability

The fixed-view contract SHALL be selected only by an immutable new-run capability marker and matching finalizer bytes. Frozen fixed-role v1 runs and adaptive v2 runs MUST retain their original authored inputs, schemas, image roles, effect identities, recovery behavior, and Make packets when resumed.

#### Scenario: Adaptive v2 run resumes after installation
- **WHEN** a checkpoint bound to `invent-concept-v2` resumes under a host that supports fixed views
- **THEN** it continues to validate and render its original adaptive role plan
- **AND** no fixed role is injected or required
