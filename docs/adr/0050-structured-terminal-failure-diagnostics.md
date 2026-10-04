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

## Consequences

Operators can distinguish common access, request, context, rate-limit,
provider-service, and transport failures without exposing arbitrary provider
text. Known signatures can be expanded deliberately with tests. Unrecognized
failures remain fail-closed but are visibly `unclassified`, with a safe code
and message size when available.

Historical failures that predate schema version 2 cannot gain a more specific
diagnosis because Workshop no longer has their raw terminal messages.

## Amended: a session that ends early is a visible stop (2026-10-04, #94)

`workshop status` derives a bounded `stop_category` for every run that is not
complete. A native session that failed to start or ended without completing
left the checkpoint `active`, so status kept reading `active`, and a budget
stop record written before a cap-raising resume still read `budget`.

When a host invocation ends with an exception while its checkpoint is still
`active`, the host writes `native-session-stop.json`: the product, Wish and
exact checkpoint hashes, and one cause, `usage-limit` or `session-ended`. It
holds no provider text. The next invocation clears it before any native work,
and any later checkpoint makes it stale. While it is current, the receipt's
visible `status` is `waiting`; the durable checkpoint, gates and budget
accounting are unchanged.

`usage-limit` is a new bounded stop category, not `transport`: a provider
usage limit is not an automatically recoverable transport failure, and a
resume succeeds only after the limit resets. The Claude adapter raises a
typed usage-limit failure for a rejected `rate_limit_event` or an error turn
whose signature is `rate-limited`; a Codex `rate-limit` diagnosis names it
only when a current stop record shows the invocation ended. The receipt adds
a fixed host need saying to resume after the limit resets.

A "product token limit reached" record is current only while used tokens are
at or over the current limit. Then `budget` still wins, because no resume can
pass it. Below the limit the record is stale and the newer cause wins.
Like every diagnosis here, a stop category cannot advance a stage, alter a
gate or authorize an effect.
