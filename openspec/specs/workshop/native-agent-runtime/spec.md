# native-agent-runtime Specification

## Purpose

The host boundary that starts and resumes one native coding-agent session and
decides when one turn has returned control. It preserves the documented JSONL
terminal event as the protocol while bounding an observed missing-event
failure without granting agent-authored bytes lifecycle authority.

## Requirements

### Requirement: External turn completion remains the authoritative boundary

The Workshop SHALL treat the Codex JSONL `turn.completed` event as the
authoritative successful end of a native turn. On receiving it, the host SHALL
stop reading further events, allow a short natural-exit grace, and safely reap
the CLI rather than waiting indefinitely for stdout EOF.

An agent message by itself SHALL NOT imply turn completion, and a clean process
exit without either the authoritative event or the bounded fallback below
SHALL NOT be accepted as a completed turn.

#### Scenario: The documented terminal event completes the turn

- **WHEN** the native event stream emits `turn.completed`
- **THEN** the host accepts the turn boundary and safely reaps the CLI
- **AND** it does not wait for unbounded stdout EOF

#### Scenario: Prose alone does not complete the turn

- **WHEN** the stream emits an agent message but no `turn.completed` and no
  current bound proposal exists
- **THEN** the host does not infer successful completion from that prose

### Requirement: A bound proposal may end a turn after 30 quiet seconds

As a temporary operational fallback, the Workshop MAY end a native turn after
30 consecutive seconds with no external native event only when it has already
received a completed agent message and can read a bounded, strict, regular
`agent-outcome.json` envelope whose checkpoint and gate subject exactly match
the current stage packet. Every subsequent external native event SHALL cancel
and restart that quiet period after the event is handled.

When the quiet period expires, the host SHALL terminate and reap the CLI. It
SHALL then perform the same complete proposal, artifact, hash, checkpoint,
subject, and stage-gate validation used after authoritative completion. The
fallback signal itself SHALL grant no transition or gate authority.

A symlink, non-regular file, oversized file, malformed or duplicate-key JSON,
wrong envelope kind, stale checkpoint, different subject, or absent completed
agent message SHALL NOT arm the fallback.

#### Scenario: A quiet bound proposal returns control

- **WHEN** a completed agent message has been received
- **AND** a bounded strict proposal matches the current checkpoint and subject
- **AND** no external native event arrives for 30 consecutive seconds
- **THEN** the host terminates and reaps the CLI and returns control to the gate
- **AND** the gate independently validates every authoritative byte

#### Scenario: Later progress restarts the quiet period

- **WHEN** any external native event arrives while the fallback timer is armed
- **THEN** the host cancels that timer, handles the event, and starts a new
  30-second period only if every fallback precondition still holds

#### Scenario: A stale proposal cannot trigger the fallback

- **WHEN** `agent-outcome.json` names another checkpoint or gate subject
- **THEN** the fallback is not armed and the turn is not reported complete

### Requirement: The quiet fallback is explicitly temporary

The 30-second quiet-period behavior SHALL be documented as a band-aid for an
observed CLI lifecycle defect, not as a second canonical completion protocol
and not as proof that internal completion was delivered correctly.

A future runtime investigation SHALL determine why a persisted internal
`task_complete` is not translated into the documented external
`turn.completed` event, repair the responsible CLI, Goal-lifecycle, or adapter
boundary, and remove the quiet-period fallback when terminal delivery is
reliable. Workshop SHALL NOT consume the vendor-private internal rollout as a
replacement public protocol merely to avoid that investigation.

#### Scenario: The workaround is not represented as the root-cause fix

- **WHEN** the native completion behavior is documented or reviewed
- **THEN** `turn.completed` is identified as the authoritative boundary
- **AND** the 30-second path is identified as temporary mitigation
- **AND** repair of the missing event translation and removal of the fallback
  remain explicit future work
