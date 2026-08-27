## Purpose

Defines the trusted, durable, and privacy-preserving boundary for paid remote
Concept image generation and recovery from ambiguous provider outcomes.

## ADDED Requirements

### Requirement: A durable authorized intent precedes every remote request

The host SHALL persist an immutable effect intent before transmitting any
Concept image request. The intent SHALL bind the run, checkpoint, gate subject,
image role, provider destination, model or operation, exact instruction hash,
reference-byte hashes, expected output path, and the durable authorization that
permits the private inputs to be sent to that destination.

Possession of a configured provider credential SHALL NOT constitute
authorization to transmit Wish text, drawing instructions, or reference bytes.

#### Scenario: Authorized intent is durable before transmission

- **WHEN** the host is authorized to request a Concept image
- **THEN** it persists the complete bound intent before sending any request
- **AND** a crash before transmission leaves an auditable unperformed intent

#### Scenario: Credentials exist without transmission authorization

- **WHEN** provider credentials are configured but no matching durable authorization exists
- **THEN** the host sends no Wish text, drawing instruction, or reference bytes
- **AND** the run waits with a need that identifies the required authorization

#### Scenario: Authorization does not cover changed private inputs

- **WHEN** an instruction, reference byte sequence, provider destination, or model differs from the values bound by an authorization
- **THEN** that authorization does not permit the changed request

### Requirement: Every logical request has one stable idempotency identity

The host SHALL assign one stable idempotency key to each logical image request
and SHALL reuse that key across every safe resend of that request. The key and
all request-defining hashes SHALL be persisted before the first attempt. A
changed request SHALL receive a different intent and idempotency key.

The provider transport SHALL either enforce that key remotely or provide
authenticated lookup by a stable provider operation identifier; a transport
supporting neither SHALL be refused for paid Concept image effects.

#### Scenario: Retry reuses the original key

- **WHEN** a verified-safe retry is made for an unchanged logical request
- **THEN** the request carries the original persisted idempotency key
- **AND** no second logical request is created

#### Scenario: Changed request receives a new identity

- **WHEN** any request-defining input changes
- **THEN** the host creates a new intent and a new idempotency key
- **AND** it does not reuse the identity of the prior request

#### Scenario: Unsafe provider capability is refused

- **WHEN** a provider transport supports neither remote idempotency nor authenticated operation lookup
- **THEN** the host refuses to send a paid Concept image request through it

### Requirement: Ambiguous outcomes are reconciled instead of blindly retried

After transmission, the host SHALL persist the provider operation identifier
and attempt state. If a response is lost or completion cannot be verified, the
host SHALL record `unknown-outcome`, SHALL NOT automatically resend the request,
and SHALL attempt authenticated result readback using the persisted request
identity.

The host SHALL resend only after authenticated reconciliation proves that the
provider did not accept or complete the original request, or when the
provider's idempotency contract guarantees that reuse of the stable key cannot
create a duplicate charge or result.

#### Scenario: Response is lost after provider acceptance

- **WHEN** the provider may have accepted a request but the host receives no verifiable result
- **THEN** the host records `unknown-outcome`
- **AND** it does not issue a request with a new key or blindly repeat the call

#### Scenario: Readback recovers a completed result

- **WHEN** authenticated readback proves the original operation completed
- **THEN** the host accepts only the result bound to that operation and intent
- **AND** it creates no replacement request

#### Scenario: Readback proves no effect occurred

- **WHEN** authenticated reconciliation proves that the original request was not accepted or completed
- **THEN** the host may retry using the same logical request identity

### Requirement: Completion produces a verified durable effect receipt

A successful remote image effect SHALL produce a durable receipt that binds the
intent, idempotency key, provider operation identifier, authenticated provider
status, returned-byte hash, completion time, and verification evidence. The
Concept gate SHALL advance only from image bytes and receipts that match the
current gate subject and expected role inventory.

An unverified response, partial role set, mismatched receipt, or
`unknown-outcome` state SHALL NOT advance the Concept gate.

#### Scenario: Verified completion is receipted

- **WHEN** authenticated provider evidence and returned image bytes match the persisted intent
- **THEN** the host writes a durable effect receipt binding their identities and hashes

#### Scenario: Gate evaluation has no remote side effect

- **WHEN** the Concept gate evaluates the completed image set
- **THEN** it performs no provider request
- **AND** it accepts only matching verified receipts and exact returned bytes

#### Scenario: Unknown outcome cannot pass the gate

- **WHEN** any required image role remains in `unknown-outcome`
- **THEN** the Concept gate does not advance
- **AND** status exposes the unresolved effect without claiming failure or success

### Requirement: Recovery is crash-safe and auditable

On resume, the host SHALL derive the next action from durable intent, attempt,
authorization, receipt, and reconciliation records rather than from file
presence alone. Every state transition SHALL be append-only or otherwise
atomically persisted so that interruption cannot turn an uncertain effect into
a fresh request.

#### Scenario: Crash after send and before response persistence

- **WHEN** the host resumes after interruption in the post-send persistence window
- **THEN** it treats the request as potentially performed and reconciles it
- **AND** it does not infer from a missing image file that the request is safe to repeat

#### Scenario: Existing file without receipt

- **WHEN** image bytes exist but no matching verified receipt exists
- **THEN** the host does not treat file presence as proof of a completed effect
