## Purpose

Give Release and the Factory product images that show the exact sealed geometry in its sealed colours, rendered by the trusted host with a capable renderer, without moving any rendering into the native session or altering sealed Made bytes.

## ADDED Requirements

### Requirement: Host renders sealed products after the Make gate
The system SHALL, after a Make proposal passes the CAD gate, render a hero image and, when Make declares `presentation.states`, a fixed-camera state strip from sealed Made bytes only (part STLs, assembly-package transforms, STEP colours, declared state STLs) into `artifacts/make/rNNNN/renders/`, and SHALL bind inputs, outputs, renderer identity, and the Made product hash in `renders.json`.

#### Scenario: Two-part toy renders in sealed colours
- **WHEN** the Make gate passes for a package with two coloured occurrences
- **THEN** `renders/hero.png` shows both parts placed by their transforms in their sealed colours
- **AND** `renders.json` lists each input path with its sha256 and each output with its sha256 and dimensions

#### Scenario: Indistinguishable states are not presented
- **WHEN** the declared state STLs render to frames that fail the state-difference rule
- **THEN** no `signature.png` is bound
- **AND** `renders.json` records the strip as unavailable with a bounded reason

### Requirement: Rendering never blocks Release
The system SHALL treat the renderer as optional: when node, playwright, or chromium is missing, or rendering fails or exceeds its bounds, `renders.json` SHALL record `status: unavailable` and Release, the manual evidence contract, and the Factory handoff SHALL behave exactly as before this change.

#### Scenario: Host without the renderer
- **WHEN** `workshop doctor` reports the renderer unavailable and a run reaches Release
- **THEN** the manual may cite only Made snaps
- **AND** the handoff carries no host cover
- **AND** status shows a renderer warning and no error

### Requirement: Manual evidence may cite host renders
The system SHALL accept `product_visuals[].source_path` under `renders/` in `MANUAL-DESIGN.json` when `renders.json` is bound to the current Made product hash and the cited file's sha256 matches, in addition to sealed Made entries.

#### Scenario: Cover uses the host hero
- **WHEN** the manual cites `renders/hero.png` with its bound sha256 on page 1
- **THEN** manual design evidence validates
- **AND** a cited render whose bytes differ from `renders.json` is rejected

### Requirement: Handoff ships the hero as the Factory cover
The system SHALL include the bound hero as `assembled_review/_assembled.png` in the import archive when rendered, so the Factory's cover ranking selects it, and SHALL record `renders_sha256` in the receipt.

#### Scenario: Draft cover matches the manual
- **WHEN** the import succeeds with a rendered hero
- **THEN** the draft's first thumbnail is the host hero
- **AND** the receipt records `renders_sha256`
