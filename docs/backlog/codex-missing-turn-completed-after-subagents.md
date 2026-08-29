# Suspected Codex `turn.completed` omission needs an isolated reproduction

- Status: Open compatibility investigation; not reproduced by retained samples
- Priority: Medium
- Temporary behavior: Exact-proposal handoff or identity-bound same-session retry

## Original observation

The authenticated mock-session run appeared to show Codex finishing useful
work without returning the documented JSONL `turn.completed` event. Workshop
therefore temporarily accepted a new exact regular `agent-outcome.json` as a
liveness marker, or retried a markerless incomplete invocation in the already
checkpointed exact session. Normal proposal parsing and host gates remained
authoritative.

The observation was initially attributed to native subagent cleanup. That
causal claim is not supported by the retained rollouts.

## 2026-08-29 investigation

The retained successful Forge session and failed Quest session show:

- every actual Codex turn has both an internal `task_complete` record and a
  public wrapper-observed `turn.completed` event;
- neither session invoked a native subagent;
- Quest's first Make proposal wrote `agent-outcome.json`, emitted its terminal
  event, and was then rejected by the deterministic host CAD gate; and
- no later Quest repair turn reached Codex.

The immediate failures came from the test-only pass-through wrapper. It stored
turn packets as `.mock-session/packets/<checkpoint>.json`. A normal deterministic
Make rejection preserves the lifecycle checkpoint but changes `STAGE.json`'s
subject and adds rejection feedback. The repair invocation therefore collided
with the first packet snapshot and exited before launching the real Codex
child. The launcher treated that pre-turn wrapper exit as a recoverable missing
terminal and consumed the remaining bounded attempts.

The harness now snapshots by checkpoint plus subject. The production launcher
also requires a valid thread identity event from the invocation before an
otherwise unknown markerless incomplete exit is recoverable. This prevents a
wrapper or preflight failure from being mislabeled as Codex terminal behavior.

## Temporary compatibility behavior

The fail-open remains for now, as requested, until an isolated characterization
can confirm or reject the upstream behavior:

- a new exact regular in-run `agent-outcome.json` may release control only after
  bounded grace and safe process-session reaping;
- the marker is liveness-only and cannot satisfy a stage gate;
- without a proposal, retry requires an observed valid native thread identity
  and the exact persisted session;
- checkpoint, subject, Goal, mutation lock, and native-turn ceiling remain
  unchanged; and
- malformed events, explicit failed turns, pre-identity failures, unsafe
  cleanup, and invalid marker types fail closed.

## Resolution criteria

Remove or retain the compatibility path only after:

1. an isolated real-Codex test records raw `codex exec --json` stdout, process
   status, marker timing, Goal timing, and the internal rollout for the same
   turn;
2. that test separately covers root-only and native-subagent finalization;
3. repeated runs establish whether a finalizer-written marker can genuinely
   precede a missing or materially delayed `turn.completed`; and
4. Spark, Forge, and Quest authenticated acceptance pass after the harness
   repair path is exercised.
