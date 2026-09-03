## ADDED Requirements

### Requirement: New fixed-view Concepts seal exactly four overall roles and every component

For a run with the fixed-view capability, the active sealed Concept SHALL contain exactly one image for `front`, `top`, `bottom`, and `exploded`, followed by exactly one isolated image for every stable component key in normalized source order. A missing, extra, duplicate, reordered, changed, or mixed-proposal role SHALL prevent Invent from advancing.

#### Scenario: One-piece Concept is complete
- **WHEN** a normalized Concept declares one stable component and all fixed roles return valid bytes
- **THEN** the sealed image set contains exactly five images in fixed order

#### Scenario: A component image is absent
- **WHEN** one declared component lacks its isolated image
- **THEN** the Concept remains unsealed and cannot reach Make

### Requirement: Fixed images form one simple and coherent reconstruction set

The front image SHALL establish the shared object and appearance. Top and bottom SHALL depict the same object unchanged from their named direct views. Exploded SHALL preserve that object while separating every declared component so no component is hidden. Each component image SHALL show only its named complete part, consistently oriented and visually tied to the exploded set. Every image SHALL use the frozen plain-presentation constraints and MUST NOT substitute a perspective beauty shot, usage scene, annotated drawing, collage, or signature-experience image for a required role.

#### Scenario: Derived view changes the product
- **WHEN** a later role instruction changes a feature, proportion, component, material, or finish rather than only exposing its required view
- **THEN** the instruction set is rejected or revised before it can be sealed

#### Scenario: Exploded view hides a component
- **WHEN** the exploded depiction does not require every stable component to be separated and unobscured
- **THEN** the fixed-view contract rejects the instruction set before component rendering

### Requirement: Fixed Concept images remain non-evidentiary

Fixed Concept images SHALL guide Make's reconstruction of form, proportion, components, interfaces, and assembly. Normalized numerical facts SHALL prevail over conflicting pixels. The images MUST remain outside CAD, printability, signature-review, Playtest, manufacture, and Release evidence, and their exact bytes MUST NOT be copied into the product tree.

#### Scenario: Pixel proportion conflicts with a millimetre value
- **WHEN** a fixed image implies a size that conflicts with the normalized brief
- **THEN** Make follows the normalized millimetre value and treats the pixel proportion as advisory
