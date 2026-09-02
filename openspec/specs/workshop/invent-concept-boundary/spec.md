## Purpose

Defines how newly versioned Forge and Quest runs make Concept a mandatory, exact, host-sealed sub-boundary of their existing Invent stage without adding lifecycle work.

## Requirements
### Requirement: New Forge and Quest runs freeze the active Invent Concept protocol

Workshop SHALL enable the active Invent Concept boundary only when a new Forge or Quest run freezes its exact capability bytes. The frozen route SHALL remain Forge `Wish -> Invent -> Make -> Release` or Quest `Wish -> Invent -> Make -> Playtest -> Release`; Concept MUST NOT appear as a stage, Goal, native turn, checkpoint, transition, pass-through artifact, or independent wait state. Spark and runs lacking the capability SHALL retain their prior contracts and artifact sets.

#### Scenario: A marked Forge run is created
- **WHEN** a new Forge run freezes the active Invent Concept capability
- **THEN** its Invent attempt includes the compound Concept boundary
- **AND** its enabled stage sequence remains `invent`, `make`, `release`

#### Scenario: Spark or an older run resumes
- **WHEN** a Spark run or a run without the frozen capability reaches its first creative stage
- **THEN** no active Concept artifact or gate is required
- **AND** its immutable protocol is not upgraded from installed host code

### Requirement: One Invent Goal authors assignment, invention, and pre-render Concept source

The existing Forge or Quest Invent Goal SHALL select the Inventor, research and choose the invention, and author the complete route-aware pre-render Concept source before invoking one compound Invent finalizer. The finalizer SHALL accept only the exact authored creative source and the five canonical Concept source documents, validate their structure and provenance, preserve their exact bytes, and propose them together with the assignment and Invented contracts. It MUST NOT render images, read credentials, perform an external effect, or advance the checkpoint.

#### Scenario: The compound finalizer succeeds
- **WHEN** the Manager supplies exact assignment/invention source and a complete structurally valid pre-render Concept tree for the current packet
- **THEN** one Invent proposal binds the assignment, Invented contract, preserved creative source, and pre-render Concept identity
- **AND** control returns to the host from the same Invent Goal and native turn

#### Scenario: Authored Concept source is invalid
- **WHEN** the pre-render tree is missing, malformed, stale, structurally incomplete, outside its canonical root, or detached from the exact assignment and Invented source
- **THEN** the finalizer fails without writing a ready outcome
- **AND** the Manager remains inside the same Invent Goal to repair authored bytes

### Requirement: Concept authors receive complete field-by-field source schemas

The frozen agent-facing Invent Concept capability SHALL provide canonical
skeletons for all five native-authored source documents: `brief.json`,
`research.json`, `prompts.json`, `descriptor.json`, and `derived_wish.json`.
For every document, it SHALL identify all required nested fields and value
constraints, the exact cross-document component and source references, the
required role dependency order, and canonical hash inputs where a hash is
authored. It SHALL distinguish pre-render descriptor leaves from host-sealed
image leaves. The capability MUST NOT require an agent to inspect validator
implementation or obtain repeated finalizer rejections to discover a required
field. It MUST NOT expose host-private credentials, provider state, raw
receipts, or semantic host judgments.

#### Scenario: A Manager prepares a first pre-render Concept proposal
- **WHEN** the Manager reads the packet-bound Invent Concept capability
- **THEN** it can identify the complete structural shape of all five authored
  JSON documents and their cross-file bindings from that capability alone
- **AND** it knows that image hashes are host-added after rendering rather than
  authored in the pre-render descriptor

### Requirement: The host seals Concept before Invent advances

After receiving a ready compound proposal, the host SHALL independently reopen the assignment, Invented, creative-source, and pre-render Concept bytes; repeat provenance and structural validation; complete and reconcile the authorized image effect; construct the sealed Concept from exact returned bytes; and record one passed Invent gate that binds every accepted identity and effect receipt. The checkpoint MUST NOT advance to Make until the complete sealed Concept passes those checks.

#### Scenario: Invent completes with exact rendered bytes
- **WHEN** the proposal and all host-rendered roles validate and reconcile against the current stage subject
- **THEN** the accepted Invent artifacts include the assignment, Invented contract, creative source, pre-render source, sealed Concept, and exact Concept image files
- **AND** the Invent gate evidence binds the sealed Concept and effect receipt identities before transitioning to Make

#### Scenario: Source changes after finalization
- **WHEN** any assignment, Invented, creative source, or Concept source byte changes before the host gate completes
- **THEN** the host refuses the proposal as stale or tampered
- **AND** no image effect is started from unverified source

### Requirement: Invent rejection and waiting remain truthful

Agent-authored contract or structural failures SHALL use a bounded same-Invent rejection that preserves the checkpoint and supplies deterministic feedback to the same session. A missing credential, unavailable authorized renderer, reconcilable outage, or unknown image-effect outcome SHALL persist a waiting condition on the owning Invent checkpoint with the pending proposal and effect state. Neither path SHALL synthesize a Concept, substitute placeholders, create a Concept checkpoint, or consume the lifecycle revision budget.

#### Scenario: Host source validation rejects a proposal
- **WHEN** independently reopened authored Concept source fails a deterministic rule
- **THEN** the exact proposal is quarantined and the same Invent Goal receives bounded actionable feedback
- **AND** no provider request or lifecycle transition occurs

#### Scenario: Rendering cannot safely complete
- **WHEN** required host credentials are absent or an image operation has an unresolved outcome
- **THEN** the run waits at `invent` with its exact proposal and effect ledger preserved
- **AND** resume reconciles that state before any retry

### Requirement: Re-Invent creates a fresh Concept revision

When the existing Make-to-Invent or Quest concept-revision edge invalidates Invent, the next Invent attempt SHALL receive the exact prior assignment, Invented, sealed Concept, effect receipt, and revision evidence. It SHALL author and seal a fresh Concept for the new round, reject stale standing-Concept or revision identities, archive superseded exact bytes, and consume only the one shared lifecycle revision already charged by the backward edge.

#### Scenario: A build-blocking Concept contradiction returns to Invent
- **WHEN** Make supplies valid evidence under the existing Make-to-Invent capability
- **THEN** the next Invent packet binds the prior sealed Concept and revision request
- **AND** a ready replacement must carry the current round and exact revision identities

#### Scenario: A prior-round Concept is replayed
- **WHEN** a compound Invent proposal cites a standing Concept, revision input, or round other than the current packet
- **THEN** the host rejects it without starting an effect or advancing the run
