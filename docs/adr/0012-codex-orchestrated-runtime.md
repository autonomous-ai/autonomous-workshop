# ADR 0012: Codex-orchestrated agent runtime

- Status: Accepted
- Date: 2026-08-26
- Owners: Workflow, Runtime, and lifecycle component maintainers

## Context

Autonomous Workshop is intended to run on a world-class coding agent that a
contributor authenticates locally. The current implementation reaches Codex
through bounded, ephemeral structured-output calls embedded in substantial
Python stage agents. Those calls helped establish contracts and deterministic
tests, but they reduce Codex to a response generator: Python constructs large
state prompts, owns cognitive loops, and exposes only a narrow read-only turn.

The Autonomous Vibe predecessor demonstrated a more useful boundary. A small
host can own a fixed workflow and deterministic artifact review while one
native coding-agent session owns repository inspection, skills, editing, shell
tools, rendering, and self-correction. Workshop needs that boundary without
giving model output authority over gates, secrets, or external effects.

This decision refines ADR 0002 rather than superseding it. `workflow` remains
the only lifecycle sequencer; stage packages continue to own public contracts
and deterministic gates. Codex becomes the cognitive/tool-using implementation
behind those seams.

## Decision

### Target runtime

One Wish uses one persistent native Codex session. The trusted Workshop host
creates or records the session id, resumes it across Match, Invent, Make,
Playtest, Instructions, and Deliver, and retains the ability to substitute a
different native coding-agent adapter later. Session memory improves
continuity, but durable workspace checkpoints, exact-byte manifests, and
verified receipts remain authoritative.

The host provides the product-run constitution from
`.agents/product-run/AGENTS.md`, the repo-scoped `autonomous-workshop` skill,
and the current
stage/capability envelope. Codex uses its native repository tools, shell, web
search, image/render inspection, and applicable skills to perform research,
creation, and repair. Required research uses the runtime's native search mode
and leaves source provenance in the workspace. Workshop will not implement a
parallel Python browsing, planning, or multi-agent framework.

Substantive outputs live as bounded files in the assigned run workspace. Codex
returns a small checkpoint envelope containing status, paths/hashes, gate
references, needs, and a proposed transition. Large concepts, manifests,
source snapshots, CAD descriptions, or review batches are not passed stage to
stage as chat JSON.

### Ownership boundary

The outer Workshop host owns:

- Wish/run identity, lifecycle order, bounded Make–Playtest rounds, leases, and
  durable checkpoints;
- sandbox and capability selection for each phase;
- public contract validation, exact-byte artifact sealing, deterministic CAD
  and simulation gates, and invalidation rules;
- authorization checks, idempotent effect intents, credential isolation,
  external adapters, reconciliation, and verified receipts;
- classifying waits, failures, unknown outcomes, and safe bounded recovery.

Codex owns:

- understanding the Wish and inspected repository state;
- Match reasoning, concept exploration, research, design, implementation,
  native tool/skill use, artifact inspection, and bounded repair;
- AI-player judgment and evidence-linked feedback, without overriding
  deterministic observations;
- writing concepts, product files, source notes, and Instructions into the run
  workspace;
- reporting compact needs and proposing, never authorizing, the next
  transition.

Model prose and self-scores are untrusted inputs. Only the host can advance a
gate. Wish text, fetched pages, tool output, and artifacts are treated as data
and cannot expand instructions or authority.

### Effects and people

Codex does not receive effect credentials and does not directly create remote
Factory state, publish, purchase, manufacture, ship, or contact a carrier. It
may prepare a local draft or effect request. The host performs an authorized
effect through a narrow idempotent adapter, reconciles remote state, and binds
the receipt to exact artifact hashes.

Public publication, spend, manufacture, postage, shipping, and other
irreversible or customer-visible actions require explicit human authorization.
An ambiguous external result is reconciled before any retry; if it cannot be
proved complete or absent, the run stops in an unknown/needs-human state.

### Transitional structured calls

`CodexStructuredRunner` and existing Python stage agents remain transitional
adapters while the persistent-session host is implemented. They must stay
bounded, schema-validated, read-only, secret-isolated, and unable to perform
external effects. They may use native search only when the phase requests it
and proves a search event. A single bounded retry is allowed only for an
explicit provider transport failure before any effect; partial responses are
never accepted or resumed as completed artifacts.

New cognitive policy should be added to the repo skill or native-agent prompt,
not expanded into another Python reasoning loop. New Python should implement a
contract, deterministic tool/gate, checkpoint, sandbox boundary, or effect
adapter. Transitional calls will be removed as equivalent native-session stage
paths become covered by integration and end-to-end tests.

## Alternatives considered

### Keep one structured model call per action and reward step

Rejected as the target because it repeatedly serializes large state, discards
native session continuity, and forces Python to reimplement work the coding
agent already performs well. It remains an explicitly temporary migration
mechanism.

### Let Codex run the entire lifecycle and all effects directly

Rejected because prompt content or model error could bypass phase order,
artifact identity, authorization, idempotency, or reconciliation. Cognitive
ownership does not imply trust or effect authority.

### Use session transcript as the durable run state

Rejected because sessions can be truncated, unavailable, or inconsistent with
files changed by tools. Content-addressed workspace artifacts and host events
are auditable and portable across agent runtimes.

### Build custom Python search, tool, and sub-agent frameworks

Rejected because they duplicate the native coding-agent runtime, increase
surface area, and make later engine substitution harder. Python remains useful
for narrow deterministic operations and trusted boundaries.

## Consequences

Codex can do most creative and diagnostic work with the same native tools a
developer uses, while Workshop stays small and fail-closed. A run keeps context
across stages without depending on chat-sized state transfer. The filesystem
protocol and outer gates also form a practical adapter seam for Claude Code,
OpenCode, or another future engine.

The host must add durable native-session creation/resume, phase capability
modes, compact checkpoint envelopes, and end-to-end recovery tests. Stage
implementations will temporarily exist in both shapes. Maintainers must resist
turning the target skill into a copied Python framework or turning the host
into a permissive shell wrapper.

## Compatibility and migration

This ADR does not rename the installed `workshop` command or current public
Python contracts. Existing `workshop wish`, `workshop status`, and
`workshop resume` behavior remains supported during migration; current resume
limitations remain until a persistent-session path is implemented and tested.
Protocol terms in the skill are not promises that corresponding per-stage CLI
commands already exist. `workshop wish` and `workshop resume` remain outer
host commands, not tools exposed inside the Codex session; current versions may
publish by default. The target host must record suitable authorization before
using that behavior, and a safer default can be introduced through the normal
CLI compatibility process.

Migration proceeds by placing the shared repository guidance, separate
product-run constitution, and product-run skill first,
then adding a host session adapter, then exposing existing CAD, simulation,
sealing, validation, and effect code as narrow tools. Each stage moves from
large ephemeral structured calls to workspace artifacts in the resumed native
session only after its contracts and failure behavior remain equivalent.

## Verification

- Validate the repo skill structure with the skill-creator validator.
- Prove one end-to-end Wish reuses or resumes one native session across all
  stages while the durable checkpoint survives process restart.
- Prove stage messages stay within a compact cap and substantive output is
  referenced from hash-bound workspace files.
- Prove Codex subprocesses cannot receive effect secrets or perform effect
  operations, while authorized host adapters can and return reconciled
  receipts.
- Prove every phase transition fails closed for changed bytes, missing or stale
  evidence, denied authorization, exhausted round budgets, and unknown effects.
- Prove Make feedback creates a new revision and invalidates/re-runs downstream
  gates before Instructions or Deliver can advance.
- Prove explicit transient provider failure has at most one bounded recovery
  attempt and never duplicates an external effect.
