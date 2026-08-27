## Context

See `proposal.md` for motivation and `specs/workshop/wish-run-progress/spec.md` for observable behavior. The latest main branch already has a privacy-safe progress subsystem: `NativeRunProgress` durably records bounded native-turn activity, `_NativeProgressTracker` binds it to the authoritative checkpoint, and the CLI's live activity renderer reports throttled foreground updates. It does not expose timestamps for host operations or paired durations.

Repository ownership still requires `src/cli/` to own presentation, `src/workshop/runtime/` to own native-runtime contracts and trusted progress data, and `src/workshop/workflow/` to own lifecycle boundaries. The current lifecycle is Wish → Match → Invent → Make ↔ Playtest → Release → Deliver; Concept is no longer a stage, and publication is an optional post-Release Factory effect.

## Goals / Non-Goals

**Goals:**

- Extend the existing live progress facility without replacing its durable current-turn record or native activity vocabulary.
- Make host setup, native invocation, proposal verification, deterministic gates, and optional publication independently measurable.
- Give `wish` and `resume` one fixed timing vocabulary while retaining existing receipts, checkpoint bytes, session behavior, and error paths.
- Make wall timestamps and elapsed durations deterministic in tests.

**Non-Goals:**

- Persisting timing history, changing the existing `native-progress.json` schema, or using timing as status or gate evidence.
- Recording native transcript content or fine-grained timing inside Codex.
- Adding timeouts, thresholds, retries, budgets, telemetry export, verbosity flags, or a second lifecycle engine.
- Restoring the removed Concept stage or image-generation effect.

## Decisions

### 1. Extend the runtime progress subsystem with a timing-event companion

Define a small immutable timing-event value and paired timing-span primitive in `workshop.runtime.progress`, next to `NativeRunProgress`. The event contains only:

- `observed_at`: ISO-8601 UTC wall time;
- `product_id`;
- `stage`;
- `operation`;
- `state`: `started`, `completed`, or `failed`;
- `elapsed_ms`: present only on terminal events.

`start_native_run` and `resume_native_run` retain their existing optional string `activity_observer` and add an optional structured timing observer. This is one progress subsystem with two deliberately different data lifetimes: native activity continues through the existing durable snapshot and foreground callback, while paired timing is foreground-only because historical profiling is not status authority. Keeping the callback separate is source-compatible with existing launcher and library integrations and avoids teaching the durable snapshot about nested operations.

Alternatives rejected:

- Replacing `NativeRunProgress` with an event log would weaken its checkpoint-bound, latest-generation trust model and require a stored-data migration.
- Encoding structured timing into activity strings would make parsing implicit and contaminate the fixed native activity vocabulary.
- Printing from workflow code would violate CLI presentation ownership and break JSON stream selection.

### 2. Use paired spans around a fixed operation vocabulary

The shared runtime helper emits `started`, records a monotonic start value, then emits exactly one `completed` or `failed` event. On failure it re-raises the original exception unchanged and never exposes exception text.

| Operation | Boundary measured |
|---|---|
| `run.initialize` | Validate and materialize a new private run, authorization, and initial checkpoint |
| `stage.prepare` | Build and persist the current `STAGE.json` subject and trusted context |
| `session.start` / `session.resume` | One native runtime invocation only |
| `outcome.process` | Read, validate, dispatch, and apply an `agent-outcome.json` proposal |
| `gate.evaluate` | The stage-owned deterministic evaluator and checkpoint transition |
| `effect.factory` | Optional Factory publication/reconciliation when attempted |

`outcome.process` can contain `gate.evaluate`, and Release processing can contain `effect.factory`. Parent durations are aggregate; child durations attribute the work inside them. Proposal recovery emits preparation and processing spans but no session span because it launches no native turn.

### 3. Preserve durable native liveness exactly

`_NativeProgressTracker`, `SAFE_NATIVE_ACTIVITY_CLASSES`, generation protection, checkpoint rebinding, throttling, and `NativeRunProgress.public_view()` remain authoritative for current-turn liveness. The existing combined activity observer continues to write the trusted snapshot and feed the CLI.

Workflow timing spans call only the optional timing observer. They are not serialized into `native-progress.json`, checkpoints, manifests, receipts, gate decisions, or idempotency keys. This keeps crash-safe current activity useful while avoiding an unbounded or partially trusted timing history.

### 4. Generate timestamps and durations at the actual workflow boundaries

The workflow supplies validated product and stage identifiers when opening a span. UTC wall time supports correlation across logs. A monotonic clock supplies elapsed milliseconds, clamped nonnegative, so wall-clock corrections do not corrupt duration.

Gate timing wraps the actual evaluator dispatch inside outcome processing. Factory timing wraps only the host-owned optional publication call after Release has already been durably accepted. Native timing wraps only the launcher call, while the existing activity callback can continue to emit `reasoning`, `tool`, `subagent`, or heartbeat updates inside that span.

### 5. One CLI renderer presents activity and timing on the selected stream

Refactor the live renderer into a Wish-progress renderer with an activity method preserving current throttling and a timing method rendering and flushing a compact line such as:

```text
[2026-08-27T03:14:15.926Z] wish=wish-one stage=match operation=session.start state=started
[2026-08-27T03:18:02.101Z] wish=wish-one stage=match operation=session.start state=completed elapsed_ms=226175
```

`_wish` and `_resume` construct one renderer from their existing `progress = sys.stderr if args.json else sys.stdout` selection and pass its two observer methods to the workflow. Existing activity messages stay content-free and continue to be throttled. Final JSON remains the only standard-output value in JSON mode.

## Risks / Trade-offs

- **[Risk] Nested spans look additive.** → Document parent spans as aggregate and use explicit leaf operation names.
- **[Risk] Additional lines create output churn.** → Measure only fixed high-level boundaries; retain existing native-activity throttling.
- **[Risk] Instrumentation changes exception or lifecycle behavior.** → The span re-raises unchanged, and tests compare checkpoints, receipts, turn counts, and recovery behavior with observers enabled.
- **[Risk] Sensitive values leak through labels or errors.** → Validate identifiers and enum values in the event contract; never accept arbitrary metadata or format exception text.
- **[Risk] Timing-sink failure is confused with run success.** → Timing remains outside lifecycle state and proof; output failure can fail presentation but can never synthesize a checkpoint, gate, or publication receipt.

## Migration Plan

1. Resolve the pre-update implementation conflicts in favor of the latest main progress and lifecycle architecture.
2. Add the timing event and span beside the existing durable progress contract, with deterministic clock tests.
3. Instrument initialization, stage preparation, session invocation, outcome/gate processing, and optional Factory publication.
4. Extend the CLI renderer and both Wish entry points while preserving stream routing.
5. Run focused and full validation, then retain the old pre-update stash until the integrated result is verified.

No stored-data migration is required because `native-progress.json` is unchanged. Rollback removes timing observer wiring and spans while leaving existing durable progress and run workspaces compatible.
