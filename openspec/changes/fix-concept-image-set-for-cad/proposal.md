## Why

The adaptive Concept visual plan lets Invent decide which images to request, so Make can receive expressive or interaction-led images while lacking the predictable orthographic and isolated-part references needed for straightforward CAD reconstruction. New Forge and Quest runs should instead produce one fixed, visually plain reference set whose roles and dependency order are known before Invent authors any image instruction.

## What Changes

- Add a new frozen Concept-view capability for newly created marked Forge and Quest runs. Invent no longer chooses the role inventory; the contract derives exactly `front`, `top`, `bottom`, `exploded`, and one isolated image for every stable concept component.
- Replace the adaptive 2-to-20 role plan for those runs with a bounded instruction document keyed to the host-derived roles. Invent still owns the design and the role-specific depiction instructions, while the finalizer owns role enumeration, canonical paths, ordering, hashes, and normalized projections.
- Standardize the rendering language using the useful prompt rules from `panda-social-cc-agent`: one same object across views, clear direct camera angles, neutral flat presentation, no scene/text/dimensions/logos/watermarks/people/hands/props, and preservation of shape, proportion, construction, material, and finish across referenced images.
- Generate in a fixed dependency order: front first; top and bottom from the front anchor; exploded from all three overall views and the complete component brief; then each isolated component from the exploded view plus its exact textual component facts.
- Require the exploded image to show every stable component separated and unobscured, and each component image to show exactly one complete component at a consistent scale and orientation suitable for later CAD reconstruction.
- Keep millimetre facts, interfaces, and other physical constraints in the normalized brief authoritative over pixels. Concept images remain non-evidentiary design direction and cannot satisfy CAD, printability, Playtest, manufacture, or Release proof.
- Preserve frozen `invent-concept-v1` and adaptive `invent-concept-v2` runs byte-for-byte. The new fixed-view behavior is additive and selected only by a new immutable capability marker and matching contract version.

## Capabilities

### New Capabilities

- `workshop/fixed-concept-view-authoring`: Defines the fixed CAD-reconstruction image inventory, the reduced Invent-authored instruction surface, deterministic role derivation, prompt constraints, and frozen compatibility with earlier Concept authoring versions.

### Modified Capabilities

- `workshop/concept-stage`: Selects and binds the new fixed-view authoring capability inside the existing Invent boundary without adding a stage, Goal, turn, or transition.
- `workshop/concept-images`: Requires exactly the four fixed overall views plus one isolated image per stable component, with CAD-legible presentation and same-design reference chaining.
- `workshop/concept-image-integration`: Executes the fixed role graph and exact prompts through the existing durable host-owned image-effect boundary.
- `workshop/make-concept-adherence`: Gives Make a predictable fixed-role summary and explicit reconstruction guidance while preserving normalized brief authority and all existing proof gates.
- `workshop/deterministic-e2e-fidelity`: Covers fixed-role derivation, prompt/reference ordering, exact sealing, revision, wait/resume, and frozen v1/v2 compatibility.
- `workshop/effort-aware-codex-mock-session-e2e`: Requires real and deterministic Codex runs to author the reduced fixed-view input and reach Make through the unchanged same-session lifecycle.

## Impact

- Affects Concept authoring schemas and typed contracts, the Invent packet and installed finalizer interface, materialized product-run references, capability/profile selection, Concept effect planning and receipts, normalized Make packets, recovery and revision inputs, deterministic fixtures, packaging locks, and authenticated acceptance evidence.
- Does not change lifecycle topology, provider authority, credential isolation, external-effect semantics, CAD formats, Make verification, blind signature review, Playtest, Release, or Factory publication.
- Provider cost becomes deterministic at `4 + component_count` images per Concept round. A component-count bound must prevent the fixed set from exceeding the provider/effect safety ceiling before any transmission.
