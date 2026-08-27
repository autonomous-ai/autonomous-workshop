## Context

See `proposal.md` for motivation. The current Concept path validates authored
inputs and then calls the remote image adapter from inside gate evaluation. It
uses bounded retries and skips roles whose output file already has bytes, but
neither mechanism settles the crash window after provider acceptance and before
local persistence. The trusted host already owns external effects, durable
state, authorization, receipts, and reconciliation; this change applies that
boundary to Concept images.

This is intentionally **low-priority backlog**. The design records the safe
destination architecture without changing the delivery priority of active
Workshop work.

## Goals / Non-Goals

**Goals:**

- Make a remote image call recoverable without duplicate requests or charges.
- Separate structural gate evaluation from credential-bearing effects.
- Make privacy authorization explicit, durable, narrow, and auditable.
- Preserve the rule that only the host performs authenticated external effects.

**Non-Goals:**

- Choosing a default image provider or model.
- Adding image-quality judgment or model-authored gate evidence.
- Treating a receipt as evidence of visual correctness, printability, or human
  response.
- Implementing this backlog as part of its creation.

## Decisions

### D1 — Use the host effect ledger before the provider call

Each role becomes a logical external effect. Before transmission, the host
persists a canonical intent containing all request-defining hashes and a stable
idempotency key. The intent is immutable; changed inputs create a new intent.

This follows the existing host-owned Factory boundary instead of inventing a
Concept-only retry mechanism. Checking for an existing output file is retained
only as an integrity signal, never as proof that the provider effect completed.

Alternative: keep bounded inline retries and role-file skipping. Rejected
because neither distinguishes “not sent” from “provider charged, response
lost.”

### D2 — Split validation, effect execution, and final gate evaluation

The host first deterministically validates the agent-authored brief, research,
and drawing instructions without spending. It then records authorization and
intent, executes or reconciles the external effect outside gate evaluation,
and finally evaluates the Concept seal from exact image bytes plus verified
receipts.

The final gate remains deterministic and performs no network operation. A
waiting or unknown effect therefore cannot be hidden inside a gate exception or
accidentally repeated by reevaluating the gate.

Alternative: retain the provider call inside the gate so one decision sees the
whole tree. Rejected because a gate may be reevaluated and is not the durable
effect authority. The final gate can still see the whole tree after receipts
exist.

### D3 — Provider transports must support safe recovery

A transport must offer provider-side idempotency for the stable key,
authenticated operation lookup, or both. The host persists the earliest stable
provider operation identifier available. A transport with neither capability
is unsuitable for paid effects and fails before transmission.

If the connection is lost after send, the state becomes `unknown-outcome`.
Automatic retry is forbidden until authenticated readback proves no effect
occurred, except when replaying the same key is covered by the provider's
documented idempotency guarantee.

Alternative: retry all timeouts because most are transient. Rejected because a
timeout describes the host's knowledge, not the provider's execution state.

### D4 — Authorization is separate from credential availability

Authorization binds the data hashes, provider origin, model or operation,
purpose, run, and checkpoint. Credentials answer whether the host *can* call a
provider; authorization answers whether it *may* transmit these private bytes.
Changing any bound value requires fresh authorization.

The initial policy surface may authorize the complete declared image role set
for one Concept subject rather than prompting per role, provided every role and
reference hash is covered before the first call.

Alternative: treat configuration of `concept-images.env` as consent. Rejected
because a reusable secret is operational capability, not informed permission
for each private payload or destination.

### D5 — Receipts bind provider evidence to exact local bytes

A completion receipt binds the immutable intent, stable request identity,
authenticated provider status, provider operation identifier, output hash, and
completion timestamp. The gate requires one matching receipt per role and
re-hashes every referenced file.

Receipt presence proves only that the external operation and byte transfer were
verified. It does not prove image quality or any physical property.

## Risks / Trade-offs

- **Some providers lack idempotency or authenticated readback** → Refuse those
  transports for paid Concept effects instead of pretending retries are safe.
- **Unknown outcomes can park a run indefinitely** → Expose the exact unresolved
  operation and reconciliation need; never trade correctness for automatic
  progress.
- **Authorization adds user or policy friction** → Permit one narrowly bound
  authorization to cover the declared role set while keeping payload hashes and
  destination explicit.
- **Separating the effect from the gate changes lifecycle ordering** → Add
  crash-window and transition tests that prove no stage advances before all
  receipts verify.
- **Provider status can later change or disappear** → Persist authenticated
  readback evidence and exact returned bytes when reconciliation succeeds.

## Migration Plan

1. Add versioned durable schemas for intent, attempt, authorization,
   reconciliation, receipt, and `unknown-outcome` state.
2. Add a provider transport contract for idempotency and authenticated readback.
3. Route Concept image calls through the host effect ledger while leaving the
   existing gate unable to advance without the new receipts.
4. Split pre-effect structural validation from the final deterministic seal.
5. Migrate only resumable runs with no image attempt in flight. Park runs with
   existing unreceipted images for explicit reconciliation or restart.
6. Remove inline retries and file-presence-as-completion after recovery tests
   pass.

Rollback must not discard intents or receipts. If the new path is disabled,
affected runs remain parked rather than falling back to the unsafe inline call.

## Open Questions

- Which supported providers expose both stable idempotency and authenticated
  result readback, and what evidence each transport can persist without storing
  additional sensitive response data?
