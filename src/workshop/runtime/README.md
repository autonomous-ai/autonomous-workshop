# Runtime

Owns native Manager engine adapters (Codex default; experimental Claude Code
and Grok Build), scrubbed execution environments, the
durable Factory effect ledger, and the canonical Factory `Receipt`. It contains
no creative stage policy, product registry, event stream, lease scheduler,
budget engine, publication service, or general retry framework.

The whole-run host holds one kernel-backed exclusive mutation lock while a
Wish is started or resumed. This is contention fencing, not an agent scheduler;
the kernel releases ownership automatically if the process exits or crashes.

`EffectLedger` is a private SQLite outbox for exactly `factory-import` and
`factory-publish`. It binds the canonical request and exact pack, handoff,
product, Release, and Playtest hashes; records intent before send; fences a send
with a random token; distinguishes succeeded, rejected, and unknown outcomes;
and never reopens an unknown effect for a blind retry. Factory integrations may
reconcile a proven success through authenticated readback.

Public API: `workshop.runtime`. Integrations produce Receipts but do not own the
contract.
