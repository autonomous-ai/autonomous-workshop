## Purpose

Defines the native authoring surface and deterministic normalization boundary for a simplified compound Invent/Concept capability without weakening downstream Concept or Make evidence.

## ADDED Requirements

### Requirement: New marked runs author exactly two Invent inputs

A newly marked Forge or Quest run using the simplified capability SHALL freeze an immutable capability version under which the native Manager authors exactly one consolidated Invent source and one visual plan before invoking the existing Invent finalizer. The capability SHALL NOT require the native session to author a separate brief, research record, descriptor, derived Wish, manifest, hash record, image byte, or CAD artifact.

The consolidated source SHALL remain the sole agent-authored authority for Inventor selection, ranking, design intent, signature interaction, anti-generic signature, physical brief, stable components, interfaces, build-critical constraints, decisive Make proof target, applicable research, deliberate decisions, assumptions, and unresolved risks. The visual plan SHALL remain the sole agent-authored authority for presentation treatment and image instructions.

#### Scenario: Initial v2 Invent is complete
- **WHEN** a new marked Forge or Quest Invent attempt authors a contract-complete consolidated source and adaptive visual plan
- **THEN** the one Invent finalizer can validate both inputs without requiring another agent-authored Concept source file

#### Scenario: Agent writes generated plumbing
- **WHEN** the native session attempts to supply a descriptor, derived Wish, source manifest, canonical hash record, or rendered image as an additional authored input
- **THEN** the simplified finalizer refuses the unexpected authoring surface

### Requirement: Consolidated Invent content is build-decisive but not CAD

The consolidated source SHALL decide enough physical information for Make to implement the product without repeating concept exploration. Every stable component SHALL have one immutable key and SHALL state its purpose, physical form, dimensions or applicable build-critical measurements, placement, interfaces, and role in the signature interaction. The source SHALL trace the intended interaction through those components and SHALL name the smallest exact mechanism or form proof that can falsify the concept at the start of Make.

The source MUST NOT contain STEP, STL, build123d, mesh, slicer, verifier, or other CAD implementation bytes. Exact geometry construction, source-level joints, printable variants, repeated occurrences, and verified tolerances remain Make work.

#### Scenario: Make can start without redesign
- **WHEN** the sealed normalized brief reaches Make
- **THEN** Make can identify every stable product component, interface, binding physical constraint, and decisive early proof without inventing a missing mechanism

#### Scenario: Invent attempts to prove CAD
- **WHEN** the authored source claims that Concept prose or provider images prove geometry, fit, printability, or physical performance
- **THEN** the source is refused or corrected before the Invent gate can pass

### Requirement: The visual plan is adaptive and signature-centered

The visual plan SHALL contain a nonempty shared presentation treatment and an ordered set of at least two and no more than 20 uniquely identified roles, with exactly one produced Concept image per role. It SHALL contain exactly one `primary-form` role and at least one `signature-experience` role. Every other role SHALL name a concrete communication need such as a second product state, assembly relationship, hidden interface, alternate form-critical view, or isolated component.

Each role SHALL carry its complete agent-authored instruction and an ordered list of earlier role ids used only as appearance references. The finalizer SHALL reject cycles, forward references, duplicate ids, an optional role without a named need, or an instruction that delegates a component's shape to reference pixels instead of its normalized brief.

#### Scenario: One-piece transformation needs two images
- **WHEN** a one-piece concept is fully communicated by its held form and transformed state
- **THEN** the plan contains `primary-form` and `signature-experience` without a fabricated exploded or isolated-component role

#### Scenario: Multipart concept needs assembly communication
- **WHEN** component interfaces or assembly order cannot be understood from the primary and signature roles
- **THEN** the Manager adds a need-bound assembly or isolated-component role and references only already-declared appearance anchors

#### Scenario: Visual plan reaches the capability ceiling
- **WHEN** a contract-complete visual plan contains exactly 20 justified roles
- **THEN** the finalizer may accept all 20 roles and the host may produce exactly 20 Concept images

#### Scenario: Visual plan exceeds the capability ceiling
- **WHEN** a visual plan contains 21 or more roles
- **THEN** the finalizer rejects the plan before any image-effect intent or provider transmission

### Requirement: Deterministic normalization adds no design judgment

After both authored inputs are complete, the finalizer SHALL deterministically derive the normalized physical brief, bounded research projection, routed-Wish preservation record, canonical image descriptor paths, source manifest, hashes, and pre-render Concept contract. Every derived value SHALL be either an exact copy, a lossless projection, a canonical path, or a canonical identity of agent-authored or host-bound bytes.

The finalizer and host MUST NOT add a component, constraint, source, finding, prompt, image role, physical fact, or design decision. If deterministic normalization cannot produce a complete unambiguous contract, the proposal SHALL fail for native repair rather than receive a host default.

#### Scenario: Canonical path and hashes are derived
- **WHEN** an accepted visual role id and instruction are normalized
- **THEN** its safe output path, manifest entry, and identities are derived without another native-authored file

#### Scenario: Required design content is absent
- **WHEN** normalization finds an unnamed component interface, missing signature instruction, ambiguous constraint, or untraceable research claim
- **THEN** Invent remains active and no Concept image effect starts

### Requirement: Frozen compatibility and bounded recovery remain exact

Runs that froze `invent-concept-v1` SHALL retain their exact six-authored-file protocol, fixed image roles, finalizer bytes, packet fields, and Make reader. Spark, unmarked runs, and older effort profiles SHALL acquire no simplified Concept requirement.

For a new simplified deep run, bounded Invent recovery SHALL first finalize unchanged complete authored inputs. If either input is absent or structurally incomplete, recovery SHALL make the smallest source-handoff edit that completes the two-input contract and invoke the finalizer next; it MUST NOT restart roster ranking, research, or concept exploration before that attempt.

#### Scenario: Historical marked run resumes
- **WHEN** a frozen v1 run resumes after Workshop has installed the simplified capability
- **THEN** it continues with its exact v1 files, roles, hashes, and Make behavior

#### Scenario: Simplified recovery finds complete inputs
- **WHEN** the consolidated source and visual plan already exist for the current checkpoint
- **THEN** recovery invokes the current finalizer before reading, researching, delegating, or refining
