## Why

Concept image generation currently performs a paid, credential-bearing remote
effect inline during gate evaluation. A lost response can therefore cause a
blind retry and duplicate charge, while configured credentials can cause
private Wish or reference content to leave the trusted boundary without a
separate durable authorization record.

This is a real trust-boundary gap, but it is recorded as **low-priority
backlog** rather than a blocker for the current native-runtime migration.

## What Changes

- Move the Concept image provider call behind the host's durable external-effect
  boundary instead of executing it as an unrecorded side effect of gate
  evaluation.
- Persist an immutable effect intent and stable idempotency key before any
  provider request is sent.
- Persist authenticated provider identifiers and reconcile ambiguous outcomes
  before retrying; record either a verified receipt or an explicit
  `unknown-outcome` state.
- Require durable authorization for transmitting private Wish text and
  reference bytes, independent of whether provider credentials happen to be
  configured.
- Make the Concept gate consume verified effect artifacts and receipts without
  itself performing the remote request.

## Capabilities

### New Capabilities

- `workshop/concept-image-effect-safety`: Defines the durable intent,
  idempotency, reconciliation, receipt, unknown-outcome, and private-data
  authorization boundary for Concept image generation.

### Modified Capabilities

None.

## Impact

- Affects the Concept image integration, workflow host composition, gate/effect
  ordering, durable run state, status reporting, and failure recovery.
- Requires provider transports to support authenticated result readback or an
  explicit non-retriable unknown-outcome path.
- Adds tests for crash windows, duplicate suppression, reconciliation, and
  authorization refusal.
- Does not authorize implementation now; this change remains low-priority
  backlog until explicitly selected for apply.
