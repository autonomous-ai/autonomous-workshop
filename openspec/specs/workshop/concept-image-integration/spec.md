## Purpose

The host-side adapter that turns the drawing instructions a concept authored into the actual image set that concept ships. It is transport and verification only: it carries what the native session specified to an image provider, checks what comes back, and seals it — so the Workshop can visualize a design without the host ever deciding what the design looks like, and without a credential ever reaching the agent.

## Requirements

### Requirement: Concept provider execution remains unavailable while dormant

No Concept image adapter SHALL be executable in this change. Importing, parsing, or evaluating Concept contracts MUST NOT load provider configuration, read a credential, open a network connection, transmit private bytes, write effect state, or invoke an external effect. A future adapter may run only through a durable authorized host-effect boundary implemented before the compound creative-stage Concept boundary is activated.

#### Scenario: Dormant evaluation runs with provider credentials configured
- **WHEN** the contract parser or structural evaluator is invoked
- **THEN** it does not inspect or use those credentials
- **AND** it performs no provider request

#### Scenario: Rendering is requested before the effect boundary exists
- **WHEN** a caller attempts to execute Concept rendering through Workshop
- **THEN** the capability is unavailable and no transmission occurs

### Requirement: Active Concept rendering uses only a durable host adapter

For marked Forge and Quest runs, Workshop SHALL invoke a configured image provider only through the durable Concept image-effect capability. The adapter SHALL accept validated host-prepared requests, target a pinned HTTPS origin and explicit provider profile, forbid cross-origin redirects, bound request and response sizes and time, return provider operation metadata plus exact image bytes, and expose authenticated reconciliation when the provider contract supports it. It MUST NOT inspect the workspace broadly, compose prompts, choose roles, write lifecycle state, or seal a Concept.

#### Scenario: The adapter receives one role request
- **WHEN** the host dispatches an authorized validated role
- **THEN** the adapter transmits only the bound instruction and exact ordered references to the pinned provider profile
- **AND** provider credentials remain confined to the host adapter

#### Scenario: Provider configuration is unavailable
- **WHEN** an active Concept effect has no valid pinned origin, provider identity, model, or credential
- **THEN** the host performs no request and records a resumable Invent wait

### Requirement: Provider behavior cannot weaken effect safety

An adapter SHALL declare whether its provider supports request idempotency, durable operation identity, authenticated completion readback, and authenticated absence proof. The host SHALL use only guarantees the adapter can prove. A provider lacking enough information to resolve an ambiguous transmitted request MUST leave that operation unknown rather than using generic retries, response guessing, or local-file existence as reconciliation.

#### Scenario: Provider exposes an operation identity
- **WHEN** a request is accepted with a durable provider operation id
- **THEN** the receipt binds it and resume uses it for authenticated readback

#### Scenario: Provider cannot reconcile an ambiguous request
- **WHEN** transmission may have occurred and the adapter has no authenticated status or absence proof
- **THEN** the run remains waiting with an unknown outcome
- **AND** the adapter does not resend the request

### Requirement: The adapter preserves reference order and returned bytes

The adapter SHALL preserve the validated role order and exact reference ordering, request exactly one final image per role, and return only bytes actually supplied by the provider. It SHALL reject missing image data, multiple final images, unrecognized content, unsafe metadata, oversized content, and responses whose declared or sniffed media type is not permitted.

#### Scenario: One valid image is returned
- **WHEN** the provider response contains exactly one bounded permitted final image
- **THEN** the adapter returns those exact bytes and operation metadata to the host effect boundary

#### Scenario: The provider returns malformed output
- **WHEN** a response has no image, multiple images, invalid encoding, or forbidden content type
- **THEN** the role is not completed and no output path is claimed
