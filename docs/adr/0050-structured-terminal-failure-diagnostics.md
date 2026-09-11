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
and attempt no greater than limit. Extra error fields, other reasons and `turn.failed` remain
terminal. The notice records only `native-reconnecting` as its event class;
it creates no terminal diagnosis or failed activity and persists no message.

This adds no host retry: Codex owns the reconnection within its current turn.
The existing identity, completion, usage, cleanup and failure requirements still
apply, including when the stream ends without completion. The synthetic
100-byte and 89-byte notices prove the event-handling defect; they do not
identify the discarded messages of historical 39-byte unclassified failures.

## Consequences

Operators can distinguish common access, request, context, rate-limit,
provider-service, and transport failures without exposing arbitrary provider
text. Known signatures can be expanded deliberately with tests. Unrecognized
failures remain fail-closed but are visibly `unclassified`, with a safe code
and message size when available.

Historical failures that predate schema version 2 cannot gain a more specific
diagnosis because Workshop no longer has their raw terminal messages.
