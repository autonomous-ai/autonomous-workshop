# Runtime

Owns native Manager engine boundaries, allowlisted execution environments, the
durable Factory effect ledger, and the canonical Factory `Receipt`. It contains
no creative stage policy, product registry, event stream, lease scheduler,
budget engine, publication service, or general retry framework.

The closed Manager registry currently exposes Codex by default, Claude Code,
and the exact Grok Build `1.0.5 (5115b46bc909)` adapter. Each adapter is thin:
it translates the shared start/resume, native Goal, project projection,
attestation, and checkpoint contracts into one vendor CLI without moving
reasoning, subagent orchestration, or stage policy into Python. Canonical
Inventor and skill sources are projected into `.codex`/`.agents`, `.claude`,
or `.grok` only for the selected run.

Claude and Grok Build have deterministic adapter and projection coverage, but
their live private-Wish acceptance remains pending. Grok acceptance must still
demonstrate the native Goal, projected Inventor, sandbox, and child-shell
`XAI_API_KEY` isolation boundaries with the pinned real CLI; mocked streams or
configuration files are not live security evidence.

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
