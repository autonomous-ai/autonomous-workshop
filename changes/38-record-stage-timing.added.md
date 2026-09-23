- Record the same host-bracketed timing already shown in live progress
  (`run.initialize`, `stage.prepare`, `session.start`/`session.resume`,
  `outcome.process`, `gate.evaluate`, `effect.factory`) into a per-stage,
  per-operation `wish-run-timing.json` under host state, written incrementally
  and independently of sealing so it survives a Run that never completes. The
  record carries a `measured_ms`/`total_ms`/`unmeasured_ms` accounting, mirroring
  the token record's honesty counter, since these seven operations cannot see
  inside an agent session where most Run wall-clock is spent. Presentation
  telemetry only: a recorder fault or an unwritable host-state path never
  fails, slows, or alters a Run, and the live progress stream is unchanged.
