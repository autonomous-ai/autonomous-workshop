## Why

`workshop wish` now reports privacy-safe native activity, but an operator still cannot tell when a host lifecycle operation began or how long it took. Timestamped operation boundaries and elapsed durations are needed to distinguish slow workspace setup, native turns, proposal verification, gates, and required Release publication without inspecting private run state.

## What Changes

- Extend the existing Wish-run progress subsystem with bounded timing events for high-level host and native-session operations rather than introducing a competing progress channel.
- Emit a UTC timestamp when each measured operation starts and a matching completion or failure event with monotonic elapsed duration.
- Cover new-run initialization and each lifecycle iteration: stage preparation, native-session start/resume, proposal processing, deterministic gate evaluation, and required Factory publication or reconciliation.
- Render timing events alongside existing live native activity on standard output for human-readable runs and standard error when `--json` reserves standard output for the final receipt.
- Apply the same timing vocabulary to `workshop resume`, including recovery of an already-written proposal.
- Keep timing diagnostic and content-free: it cannot advance lifecycle state or prove an effect, and it never includes Wish text, prompts, credentials, artifact content, provider responses, or exception text.

## Capabilities

### New Capabilities

- `workshop/wish-run-progress`: Timestamped, duration-bearing progress for the trusted operations executed by `workshop wish` and `workshop resume`, integrated with the existing privacy-safe live progress behavior.

### Modified Capabilities

None.

## Impact

- `src/workshop/runtime/progress.py`: owns the bounded timing-event value and paired timing primitive beside the existing durable `NativeRunProgress` contract.
- `src/workshop/workflow/native_run.py`: reports actual lifecycle operation boundaries while preserving the existing native activity tracker, checkpoint authority, and native-session behavior.
- `src/cli/main.py`: renders both existing activity and new timing events on the already-selected progress stream without changing the final receipt contract.
- Runtime, workflow, CLI, and end-to-end tests cover ordering, clocks, recovery, failure, redaction, and JSON-output compatibility.
- No new dependency, credential access, gate input, effect path, or authoritative run artifact is introduced.
