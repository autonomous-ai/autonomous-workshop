# ADR 0050: Retain structured terminal-failure diagnostics

- Status: Accepted
- Date: 2026-09-06

## Context

The native Codex adapter deliberately does not persist free-form provider error
messages. Those messages are untrusted content and may contain prompts,
credentials, paths, customer data, or other private values. Previously the
adapter used a message only to recognize an allowlisted transient transport
failure and then discarded it. For every other terminal failure, operators saw
only `explicit-terminal-failure`, even when the provider supplied a useful
stable error code or a recognizable cause such as invalid encrypted content.

Discarding unsafe text remains necessary. Discarding all diagnostic meaning is
not acceptable because it makes a stopped run needlessly opaque.

## Decision

For each `turn.failed` or terminal `error` event, the adapter derives one
bounded, non-content diagnosis before discarding the raw message:

- the allowlisted terminal event type;
- a stable cause category;
- a recognized diagnostic signature;
- an optional provider code only when it matches a strict 128-character syntax;
- the UTF-8 byte count of the original message.

Classification examines at most the existing bounded diagnostic prefix. It
does not retain excerpts. Unknown text produces the explicit category and
signature `unclassified`; it does not silently disappear.

Four fixed native literals also have exact diagnoses after case and whitespace
normalization: `in-process app-server runtime is closed` maps to
`native-runtime` / `app-server-closed`; `Luna response exceeded the output limit`
to `native-runtime` / `luna-output-limit`; `Requested an operation in invalid
state` to `native-runtime` / `handshake-invalid-state`; and `invalid JSON in
cached Login token file` to `access` / `cached-login-token-invalid-json`.
These matches require the complete message within the existing diagnostic
bound; surrounding prose or a truncated prefix cannot select them. They add no
retry authority and do not identify the cause of historical unclassified errors.

The bounded native sentence `You've hit your usage limit.` also maps to
`usage-limit` / `usage-limit-exceeded`, with optional following reset guidance.
The sentence must begin the normalized terminal message; quoted or embedded
mentions and messages beyond the diagnostic bound do not select this diagnosis.
Account-specific URLs and reset times are discarded with the remaining text.
This distinguishes the native account limit from Workshop's product-token
budget without changing retry policy or either limit.

The adapter includes safe category, signature, and code fields in the raised
terminal-failure summary and writes the complete structured diagnosis to the
host-private `0600` `codex-turn-failure.json` record. That record advances to
schema version 2. Existing schema-v1 records remain valid historical evidence,
but their discarded provider messages cannot be reconstructed.

This diagnosis is telemetry, not recovery authority. Only the existing exact
transport allowlist can make a native turn automatically recoverable. A new
classification cannot advance a stage, alter a gate, or authorize an external
effect.

Codex 0.153.4 also emits top-level `error` events during its own transport
reconnection. A credential-free loopback fixture returned a truncated response,
observed `Reconnecting... 1/2 (stream disconnected before completion: stream
closed before response.completed)`, then saw the same process and thread retry,
complete and exit zero. A second fixture verified the same behavior with the
suffix `idle timeout waiting for SSE`. Workshop now continues reading only
these exact bounded notice forms, with positive decimal attempt/limit counters
and attempt no greater than limit. Extra error fields, other reasons and
`turn.failed` remain terminal. The notice records only `native-reconnecting` as
its event class;
it creates no terminal diagnosis or failed activity and persists no message.

This adds no host retry: Codex owns the reconnection within its current turn.
The existing identity, completion, usage, cleanup and failure requirements still
apply, including when the stream ends without completion. The synthetic
100-byte and 89-byte notices prove the event-handling defect; they do not identify
the discarded messages of historical 39-byte unclassified failures.

## Consequences

Operators can distinguish common access, request, context, rate-limit,
provider-service, transport, and recognized native-runtime failures without
exposing arbitrary provider text. Known signatures can be expanded deliberately
with tests. Unrecognized failures remain fail-closed but are visibly
`unclassified`, with a safe code and message size when available.

Historical failures that predate schema version 2 cannot gain a more specific
diagnosis because Workshop no longer has their raw terminal messages.
