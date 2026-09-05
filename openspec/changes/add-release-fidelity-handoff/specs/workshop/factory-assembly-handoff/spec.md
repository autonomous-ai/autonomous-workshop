## Purpose

Deliver every sealed occurrence of a multi-part toy to the Factory as its own mesh, in the colours Make sealed, using only bytes the host already trusts.

## ADDED Requirements

### Requirement: Factory handoff derives the multipart transport from the sealed assembly-package
The system SHALL accept the cadgen assembly-package sealed at `assembled.step.json` as a source of occurrence identity for the Factory handoff, after the existing Factory-sidecar and native-descriptor forms. For a package with two or more occurrences, each occurrence SHALL resolve to the sealed Made entry `parts/<name>.stl`, and the handoff SHALL transport `assembled.step`, a synthesized Factory sidecar, and `assembled_parts/<name>.stl` for every occurrence, applying the existing shell-count inspection to the assembly and each part.

#### Scenario: Two-part toy is transported as two meshes
- **WHEN** Release hands off a Made tree whose assembly-package lists `owl_follower` and `reversible_nest` and whose `parts/` directory holds one single-shell STL per name
- **THEN** the import archive contains `assembled_parts/owl_follower.stl`, `assembled_parts/reversible_nest.stl`, `assembled.step`, and an `assembled.step.json` in Factory sidecar form naming both parts
- **AND** the receipt records `handoff_transport: multipart` and `occurrence_count: 2`

#### Scenario: Malformed package degrades visibly
- **WHEN** the sealed `assembled.step.json` is not a valid assembly-package, Factory sidecar, or native descriptor
- **THEN** the handoff transports only the root `assembled.stl`
- **AND** the receipt records `handoff_transport: single-mesh` with a bounded reason
- **AND** publication is not blocked

### Requirement: Make guarantees a production STL per occurrence
The system SHALL reject a Made proposal whose assembly-package has two or more occurrences unless `parts/<name>.stl` exists for each occurrence, each part STL is one shell, and `assembled.stl` has exactly the package's occurrence count of shells. The rejection SHALL name the missing or non-conforming part.

#### Scenario: Missing part STL is repaired in-session
- **WHEN** the native session finalizes Make with a two-occurrence package and only one `parts/<name>.stl`
- **THEN** the host gate rejects the proposal naming the missing part
- **AND** the next Make attempt receives that reason in its inputs

### Requirement: Sealed part colours reach the listing keyed as the viewer resolves them
The system SHALL reproduce the Factory viewer's part grouping of the sealed `assembled.stl` (manifold-edge shells, loose facets owned by the shell they face, dense numbering in triangle order), own every group by the sealed production mesh's shape signature and the posed occurrence geometry of the sealed STEP, and send one `assembly_parts` entry per coloured viewer group (order, the slide or `<lead>#i` slot key, owner mesh name, sealed colour) through the existing `factory-part-colors` effect, verified on authenticated readback. A multipart transport SHALL require every occurrence to own at least one viewer group.

#### Scenario: A part that splits into several shells keeps its colour
- **WHEN** a sealed occurrence appears as three shells in `assembled.stl` and the sidecar lists it once
- **THEN** all three viewer groups are keyed with that occurrence's sealed colour, the two past the slide list by `assembled.stl#i`
- **AND** every later group keeps its own owner's colour

#### Scenario: Colours applied to an unrendered draft
- **WHEN** the Factory has not yet rendered the imported draft and reports no meshes
- **THEN** the full keyed table is written and read back as stored on the current version

### Requirement: Make seals a colour on every part
The system SHALL reject a Made proposal whose assembly-package has two or more occurrences unless every occurrence carries a sealed surface colour in the STEP or the package, naming the uncoloured occurrences.

#### Scenario: An uncoloured part is repaired in-session
- **WHEN** the native session finalizes a two-occurrence Make with one uncoloured part
- **THEN** the host rejects the proposal with `make-part-colours-missing` naming that part

### Requirement: One colour convention across sealed formats
The system SHALL report the raw colour channels sealed in a STEP or assembly-package as the sRGB hex a viewer shows, so the hex read from STEP, the GLB material as the shop displays it, host renders, and the Factory `part_colors` agree for the same occurrence.

#### Scenario: STEP and GLB agree
- **WHEN** a part is authored with `Color(0.82, 0.51, 0.18)` and exported to STEP and GLB
- **THEN** `read_step_part_colors` reports `#d1822e`
- **AND** the GLB material displays `#d1822e` in the shop viewer
