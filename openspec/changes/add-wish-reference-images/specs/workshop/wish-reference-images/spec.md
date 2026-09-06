## Purpose

Let a person hand a run the pictures that define the product, with the same binding, immutability, and disclosure discipline as the Wish text.

## ADDED Requirements

### Requirement: A Wish may declare reference images
The system SHALL accept an optional ordered `references` list on a Wish of at most eight entries, each naming one PNG, JPEG, or WebP image as `ref-NN-<slug>.<ext>` with its media type, byte size, pixel size, and SHA-256, numbered in the order given; entries SHALL be unique by bytes, at most 12 MiB each and 48 MiB together, and between 16 and 16384 pixels per side and at most 50 megapixels. A Wish without references SHALL keep byte-identical canonical JSON.

#### Scenario: Two images attached in order
- **WHEN** `workshop wish --ref side.jpg --ref front.png "..."` starts a run
- **THEN** `WISH.json` lists `ref-01-side.jpg` then `ref-02-front.png` with their hashes and pixel sizes
- **AND** the run root contains both files read-only under `wish-references/`

#### Scenario: Unsupported or unreadable file
- **WHEN** a `--ref` file is a GIF, an animated WebP, empty, oversized, or not an image
- **THEN** the command fails with a message naming the file
- **AND** no run workspace is created

### Requirement: Reference bytes are immutable run inputs
The system SHALL materialize every declared reference as a read-only immutable input under `wish-references/`, budget those bytes separately from constitution and skill inputs, and at every checkpoint SHALL fail closed when a declared reference is missing or changed or when an undeclared file sits under that directory. The Codex and Grok sandboxes SHALL treat the directory as read-only.

#### Scenario: Reference edited inside the run
- **WHEN** any byte of a materialized reference changes
- **THEN** the next checkpoint load raises a state conflict naming the reference

#### Scenario: Files without a declaration
- **WHEN** reference bytes are supplied that the Wish does not declare, or a declared reference has no bytes
- **THEN** run creation is rejected before a workspace exists

### Requirement: The agent is told where the references are
The system SHALL list declared references in every `STAGE.json` as `wish_references` (path, sha256, media type, width, height), and the product-run constitution and workflow skill SHALL direct the agent to read them with the `image-to-cad` skill as untrusted visual evidence.

#### Scenario: Invent packet
- **WHEN** a run with references prepares its Invent stage
- **THEN** `STAGE.json.inputs.wish_references[0].path` is `wish-references/ref-01-...`

### Requirement: Public disclosure follows the Wish wording
The public toy archive SHALL always list reference names, hashes, media types, and pixel sizes in `wish/wish.json` with a `reference_disclosure` field, and SHALL write the image bytes under `wish/references/` only when the exact Wish wording is disclosed.

#### Scenario: Default archive
- **WHEN** the archive is written without exact Wish disclosure
- **THEN** `wish/wish.json` lists the references with `reference_disclosure: withheld`
- **AND** no file exists under `wish/references/`

#### Scenario: Disclosed archive
- **WHEN** the archive is written with exact Wish disclosure
- **THEN** `wish/references/<name>` holds the exact bytes for every reference
