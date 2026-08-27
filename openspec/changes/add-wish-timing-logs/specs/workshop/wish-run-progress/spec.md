## Purpose

Make long-running Wish executions diagnosable from live command output by identifying the current trusted operation and the time consumed without exposing private native-agent or product content.

## ADDED Requirements

### Requirement: Wish timing extends existing live progress
The system SHALL preserve the existing privacy-safe native activity and durable current-turn progress behavior while emitting timing events for high-level operations during `workshop wish` and `workshop resume`. Timing events SHALL use the same command progress stream as live activity and SHALL NOT create an independent lifecycle, checkpoint, or gate authority.

#### Scenario: Native liveness remains available
- **WHEN** a native Codex turn emits supported activity while a timed session operation is active
- **THEN** the command continues to report the bounded native activity
- **AND** durable current-turn progress continues to be maintained under its existing trust rules

#### Scenario: Timing does not replace status
- **WHEN** an operator later requests run status
- **THEN** status continues to derive lifecycle state from the authoritative checkpoint and liveness from the trusted durable progress snapshot
- **AND** no timing event is treated as evidence that a stage or effect succeeded

### Requirement: Wish runs emit timestamped operation boundaries
The system SHALL emit a timing event before entering each applicable high-level operation during `workshop wish` and `workshop resume`: run initialization for a new Wish, stage-input preparation, native-session start or resume, agent-outcome processing, deterministic gate evaluation, and optional Factory publication when attempted. Each event SHALL identify the product id, lifecycle stage, fixed operation name, state, and an ISO-8601 UTC timestamp, and SHALL be flushed promptly.

#### Scenario: A new Wish reports initialization
- **WHEN** a user starts `workshop wish`
- **THEN** the command emits a timestamped start event for run initialization before initialization begins
- **AND** it emits a matching terminal event when initialization ends

#### Scenario: A native turn is visible while it runs
- **WHEN** an active lifecycle stage requires a native Codex turn
- **THEN** the command emits a timestamped start event identifying the stage and whether the session is starting or resuming before invoking the native runtime
- **AND** existing bounded activity updates can appear before the matching terminal event

#### Scenario: Host work is distinguishable from native time
- **WHEN** the host prepares stage input, processes an agent outcome, evaluates a deterministic gate, or attempts optional Factory publication
- **THEN** timing events identify that operation separately from the native-session operation

#### Scenario: Proposal recovery is timed without another native turn
- **WHEN** `workshop resume` finds an already-written valid agent outcome for the current checkpoint
- **THEN** it emits timing for preparation, outcome processing, and any applicable gate or publication operation
- **AND** it does not emit a native-session start or resume operation for that recovered outcome

### Requirement: Terminal timing events report elapsed duration
For every started timing operation, the system SHALL emit exactly one matching terminal event with state `completed` or `failed`. The terminal event SHALL report a nonnegative elapsed duration measured with a monotonic clock and SHALL retain the same product id, stage, and operation as its start event.

#### Scenario: An operation completes
- **WHEN** a measured Wish-run operation returns normally
- **THEN** its matching terminal event has state `completed`
- **AND** it reports the operation's elapsed duration

#### Scenario: An operation fails
- **WHEN** a measured Wish-run operation raises an error
- **THEN** its matching terminal event has state `failed`
- **AND** it reports elapsed duration without exception text
- **AND** the original error continues through the existing failure path

#### Scenario: Wall time changes independently of elapsed time
- **WHEN** the system wall clock changes during a measured operation
- **THEN** event timestamps reflect UTC wall time
- **AND** duration remains nonnegative because it is derived from a monotonic clock

### Requirement: Progress preserves CLI output compatibility
The system SHALL write live activity and timing events to the command's selected progress stream. A human-readable invocation SHALL use standard output, while an invocation using `--json` SHALL use standard error and reserve standard output for exactly the final JSON receipt.

#### Scenario: JSON output remains parseable
- **WHEN** a user runs `workshop wish --json` or `workshop resume --json`
- **THEN** all live progress is written to standard error
- **AND** standard output contains only the final JSON receipt

#### Scenario: Human-readable output includes timing
- **WHEN** a user runs a Wish command without `--json`
- **THEN** live activity, timing events, and the final human-readable receipt are written to standard output

### Requirement: Timing is bounded, private, and non-authoritative
Timing events SHALL use only validated product and lifecycle identifiers, fixed operation and state values, UTC timestamps, and elapsed duration. They SHALL NOT include Wish objective or context, prompts, native event content, artifact content, paths, environment values, credentials, authorization secrets, provider responses, or exception text. Timing emission SHALL NOT alter lifecycle transitions, checkpoint hashes, native-session identity, retries, budgets, gate evidence, effect authorization, or publication status.

#### Scenario: A Wish contains a sensitive value
- **WHEN** a Wish objective or context contains a sensitive value
- **THEN** live progress identifies the run by product id without reproducing that value

#### Scenario: Optional publication fails with private response content
- **WHEN** Factory publication raises an error containing provider details
- **THEN** the timing event records only the failed fixed operation and elapsed duration
- **AND** existing publication reconciliation and Release validity remain authoritative

#### Scenario: A progress sink fails
- **WHEN** writing live diagnostic progress fails
- **THEN** the failure cannot create a successful checkpoint, gate, or external-effect receipt
