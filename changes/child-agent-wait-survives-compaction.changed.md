- **Waiting on a child agent now follows the same rule, in the same surviving
  place.** The constitution already carried the command-waiting rule because
  `world_state` re-emits the run-root `AGENTS.md` after every compaction and
  never re-emits a reference file. Waiting on a *child* was left behind in
  `references/make.md`, so it had the defect the command rule was moved to
  escape: the guidance disappears at the first compaction that does not re-read
  that file, which is exactly when the independent-critic phase is running.
- The constitution now says to wait for a child with one `wait_agent` at a long
  timeout, and never with repeated short waits, `list_agents` polling, or a
  `sleep` between them.
- Measured across 37 product rollouts: `wait_agent`, `list_agents` and `sleep`
  cost 12.3M tokens over 136 requests, 5.8% of product spend. Most child waits
  are already sensible (`timeout_ms` 60000 on 139 calls, 180000 on 33), so the
  waste concentrates in the 43 calls at 10000 and in 82 `sleep` calls that both
  files already forbade.
- Guidance only: no gate, schema, review allowance or finalizer check changes.
  **Materialized instruction bytes changed**: the run-root `AGENTS.md` is new.
  Frozen runs keep their materialized instructions.
