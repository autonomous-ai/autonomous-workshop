## ADDED Requirements

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
