## Purpose

Defines the durable, authorized host-effect protocol that turns validated pre-render Concept instructions into exact sealed image bytes without exposing credentials to the native session.

## Requirements
### Requirement: Concept rendering requires explicit run authority and host-only credentials

Before any Concept source or reference image is transmitted, Workshop SHALL persist authorization for the current product run that names Concept image generation, the configured provider profile, and the private data classes that may be sent. Selecting a newly marked Forge or Quest route SHALL record that disclosed prospective authority at run creation. Credentials SHALL be loaded lazily by the host only after the native turn exits and MUST NOT enter the workspace, stage packet, prompt, subprocess environment, proposal, public archive, or status output.

#### Scenario: An authorized marked run reaches rendering
- **WHEN** a validated pre-render Concept belongs to a run with matching Concept-render authority
- **THEN** the host may prepare the exact effect intent using host-private credentials
- **AND** no credential becomes readable by the native session

#### Scenario: Authority is absent or mismatched
- **WHEN** rendering lacks matching run authority for the selected provider profile or transmitted data
- **THEN** no network request occurs
- **AND** the run waits at its owning Invent checkpoint with a need naming the missing authority

### Requirement: Every image operation has a durable pre-transmission identity

The host SHALL write an immutable effect intent before transmitting each role. Its stable idempotency identity SHALL bind the run, checkpoint and subject, pre-render Concept identity, role, exact instruction, ordered reference hashes, output path, provider profile, model, and request format. Re-entering the same operation SHALL resolve the same identity; changing any bound input SHALL require a different operation and SHALL NOT overwrite prior state.

#### Scenario: A role is attempted twice with unchanged inputs
- **WHEN** resume reaches a role whose complete request vector is unchanged
- **THEN** Workshop resolves the same durable operation identity
- **AND** it reconciles existing state before deciding whether transmission is allowed

#### Scenario: A prompt or reference changes
- **WHEN** any instruction, reference byte, provider profile, model, or stage binding differs
- **THEN** the prior operation cannot satisfy the new request
- **AND** a new intent is required after the new source passes validation

### Requirement: Roles execute in validated dependency order

The host SHALL render exactly the required overall and component roles in the deterministic reference order declared by the validated Concept instructions. A role SHALL receive only its exact instruction and already completed reference bytes. Missing, changed, extra, unsafe, oversized, malformed, or provider-incompatible inputs SHALL stop before that role is transmitted, and partial output MUST NOT be accepted as a sealed Concept.

#### Scenario: A role depends on earlier images
- **WHEN** its validated instruction names completed prior roles
- **THEN** the request binds and transmits those exact returned bytes in declared order
- **AND** it cannot reference a later or incomplete role

#### Scenario: Rendering stops after a partial set
- **WHEN** one required role cannot be completed or reconciled
- **THEN** completed role receipts remain durable but no sealed Concept is produced
- **AND** Make remains unreachable

### Requirement: Completion is proved by authenticated receipts and exact bytes

For every completed role, Workshop SHALL persist a bounded receipt that binds the intent, provider and operation identities, authenticated completion readback when the provider supports it, response metadata, exact returned image hash, and canonical output path. Returned content SHALL be bounded, format-checked, and written atomically as a regular in-root file before sealing. A command exit, HTTP success alone, local path, or model claim MUST NOT prove completion.

#### Scenario: Provider completion is verified
- **WHEN** authenticated response or readback proves one operation completed and returns one permitted image
- **THEN** Workshop atomically writes those exact bytes and records their hash-bound receipt
- **AND** sealing reopens the same bytes independently

#### Scenario: Returned bytes are invalid
- **WHEN** the response is missing, oversized, malformed, unsafe, redirects outside the pinned origin, or differs from authenticated readback
- **THEN** the role is not completed
- **AND** no receipt claims usable image bytes

### Requirement: Ambiguous effects reconcile before retry

If transmission may have occurred but completion or absence cannot be proved, Workshop SHALL mark the operation outcome unknown, retain its immutable intent and any provider operation identity, and stop at the owning Invent checkpoint. Resume SHALL perform authenticated reconciliation before any resend. Blind retry is forbidden; when the provider cannot prove completion or absence, the run SHALL remain unknown and require human resolution.

#### Scenario: The connection drops after transmission
- **WHEN** the host cannot prove whether the provider accepted or completed the operation
- **THEN** the effect becomes unknown and the run waits at `invent`
- **AND** the same request is not resent merely because resume was invoked

#### Scenario: Reconciliation proves absence
- **WHEN** authenticated provider state proves the operation did not occur and the provider contract permits the same idempotent request
- **THEN** Workshop may retry under the same intent and idempotency identity
- **AND** the retry remains bounded by the effect protocol

### Requirement: Effect evidence makes no product or quality claim

Concept image receipts and sealed image hashes SHALL prove only what exact provider operation returned which bytes. They MUST NOT claim that an image is aesthetically good, semantically consistent, buildable, printable, physically tested, manufactured, or valid product evidence.

#### Scenario: A complete image set is sealed
- **WHEN** every role has a reconciled receipt and exact bytes
- **THEN** the effect evidence proves role completeness and byte identity only
- **AND** no Playtest, Release, manufacture, or delivery gate may treat it as product evidence
