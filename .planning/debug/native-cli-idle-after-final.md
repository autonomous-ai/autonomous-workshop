---
status: investigating
trigger: '"The native CLI then remained idle instead of returning cleanly to the host, so the durable host status had not yet advanced from Invent to Concept when the parent conversation was interrupted." Investigate this issue'
created: 2026-08-26
updated: 2026-08-26T11:18:00+07:00
---

# Debug Session: Native CLI Idle After Final

## Symptoms

- expected_behavior: After the product-run agent finalizes Invent, completes its native Goal, and emits its final response, the Codex CLI process exits promptly; the Workshop host consumes `agent-outcome.json`, validates it, and advances the durable checkpoint from Invent to Concept.
- actual_behavior: The agent emitted a successful final Invent response and the finalizer wrote valid `invented.json` plus `agent-outcome.json`, but the Codex CLI process stayed alive and idle. The Workshop host remained blocked reading native stdout until its timeout, and `workshop status` continued to report `active at Invent`.
- error_messages: `workshop: native Codex session did not complete: Codex native session timed out`. An intentional Ctrl-C during a later exact-session resume showed the host blocked in `src/workshop/runtime/codex.py`, method `_stream`, at `for raw in process.stdout`.
- timeline: Reproduced on 2026-08-26 during Wish `wish-20260826-095135-f3a83007`. The Invent final response was recorded at 2026-08-26T10:25:29Z; the native process remained alive until the host timeout. Whether older versions worked is unknown.
- reproduction: Run `uv run workshop wish "Have the ABO create a new game for 2 players that combine chess and azul"`; let Match finish and Invent finalize; observe the successful Invent final response in the native rollout, then observe the Codex process remain alive, `codex.py:_stream` remain blocked on stdout, and durable status remain Invent until timeout. Exact recorded native thread: `01a03d7b-7c04-7dc3-9643-921dde4e5076`.

## Current Focus

- hypothesis: The reproduced hang occurred on a revision where `_stream` iterated stdout until EOF even after `turn.completed`; the current terminal-event break/reap logic may be a subsequent local change rather than behavior present during the failure.
- test: Compare `src/workshop/runtime/codex.py` and its tests against Git state/history, then inspect the exact run's rollout tail to verify whether `turn.completed` was emitted before the host timed out.
- expecting: Confirmation requires both a code diff showing the EOF dependency was removed after the failure and rollout evidence showing a valid terminal event preceded the idle period.
- next_action: Inspect Git status/diff/log for the terminal handling and locate the exact run workspace plus rollout files for thread 01a03d7b-7c04-7dc3-9643-921dde4e5076.
- reasoning_checkpoint:
- tdd_checkpoint:

## Evidence

- timestamp: 2026-08-26T11:18:00+07:00
  checked: Current `CodexNativeSessionLauncher._stream` implementation
  found: The current loop breaks immediately on `turn.completed`, waits only 0.25 seconds for normal process exit, then terminates and reaps a still-live CLI process.
  implication: Current source explicitly mitigates the reported EOF hang; Git state/history must establish whether this logic postdates the reproduction.

- timestamp: 2026-08-26T11:18:00+07:00
  checked: Runtime completion ordering
  found: `start()` and `resume()` return only after `_stream()` returns; the workflow cannot read or validate `agent-outcome.json` while `_stream()` remains blocked.
  implication: Any EOF wait inside `_stream()` directly explains why a valid proposal can exist while durable lifecycle state remains at Invent.


## Eliminated


## Resolution

- root_cause:
- fix:
- verification:
- files_changed:
