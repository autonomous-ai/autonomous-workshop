## 1. Reconcile With Latest Progress Architecture

- [x] 1.1 Resolve the pre-update merge conflicts in favor of the latest main-branch lifecycle and durable native-progress behavior; verify no Concept-stage/image-effect code or obsolete progress callback remains and the focused upstream progress tests pass unchanged.
- [x] 1.2 Update the changelog fragment to describe the timing extension to existing live progress and verify it does not claim a new authoritative artifact or restored effect.

## 2. Timing Contract

- [x] 2.1 Add the immutable bounded timing-event value beside `NativeRunProgress` in `src/workshop/runtime/progress.py`; verify unit tests accept only validated product/stage/operation/state/timestamp fields, require elapsed milliseconds only for terminal events, and reject arbitrary or sensitive metadata.
- [x] 2.2 Add the paired timing-span primitive using UTC wall time and a monotonic duration clock; verify deterministic tests cover ordered start/completed events, nonnegative duration across wall-clock change, failed events without exception text, no-op behavior without an observer, and re-raising the original exception unchanged.

## 3. Trusted Workflow Instrumentation

- [x] 3.1 Add an optional timing observer to `start_native_run` and `resume_native_run` without changing the existing activity observer; verify callers that omit timing retain their current results and durable `NativeRunProgress` bytes.
- [x] 3.2 Instrument `run.initialize`, `stage.prepare`, and `session.start`/`session.resume` at their actual workflow boundaries; verify new Wish, resumed session, repeated stage, wait, failure, and already-written-outcome paths emit the correct spans without adding native turns or retries.
- [x] 3.3 Instrument `outcome.process` and nested `gate.evaluate` around current Match, Invent, Make, Playtest, and Release evaluators; verify checkpoint transitions, gate receipts, proposal cleanup, rejection recovery, and exception behavior remain unchanged.
- [x] 3.4 Instrument required Factory publication/reconciliation inside terminal Release as `effect.factory`; verify missing credentials, unavailable/ambiguous publication, success, and resumable pending-proposal replay preserve Release authority and emit no credentials, provider response, exception text, or user-authored content.

## 4. CLI Rendering

- [x] 4.1 Extend the current throttled live-activity renderer to render and flush timing events, then bind both observer methods for `_wish` and `_resume`; verify existing activity throttling/messages remain intact and terminal timing lines include `elapsed_ms`.
- [x] 4.2 Extend CLI and end-to-end tests to verify human-readable runs put live progress on stdout, `--json` puts all live progress on stderr while stdout remains exactly one parseable receipt, recovered outcomes omit session timing, and Wish/context/secret values never appear in timing lines.

## 5. Acceptance

- [x] 5.1 Run focused runtime-progress, CLI, native-host, and native full-run tests, then the full offline test suite, `openspec validate add-wish-timing-logs --strict`, `tools/scan_secrets.py`, and `git diff --check`; verify all checks pass and no generated run workspace, private artifact, or unrelated user change is added.
