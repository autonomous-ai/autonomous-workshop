- **Make now fetches the same guidance more cheaply.** Every tool call re-sends
  the whole session and the product budget counts that re-sent input, so each
  empty poll and each repeated read is paid at full context size. The
  2026-09-11 Spark Make (`wish-20260911-082350-cf24a6fb`) spent 16 of its 75
  tool calls on empty polls at 100-140k tokens each, and read three slices of
  `stage_proposal.py` to learn the verification path.
- `references/make.md` gains **Keep the session small**: wait on long commands
  with `yield_time_ms: 30000` and no interleaved `sleep` (131 recorded empty
  `write_stdin` polls at that yield waited up to 30.0 s), wait on a child with
  one long `wait_agent`, do not re-read a stable reference unless a compaction
  dropped it, skip the later-stage `playtest.md` and `release-deliver.md`,
  prefer `--help` and finalizer errors over reading tool source, and never
  rerun a finalizer on unchanged bytes.
- No guidance Make relies on is withheld. The `cad` reference triggers,
  `run-cost.md`, `invent.md` and `make-playtest.md` (which carries the current
  build-group and vault-lead contract) stay fully available. Files that can
  change — the newest `STAGE.json`, the run's own sources and fresh reports —
  are always re-read. A host turn prompt or frozen profile that narrows reading
  (early proof, final-product recovery) takes precedence.
- The finalizer example now names the exact verification path,
  `<cad-project>/measure/verification-pipeline.md`.
- `make-round/SKILL.md` carries the same waiting rule for the round command.
- Guidance only: no gate, schema, review allowance or finalizer check changes.
  **Materialized instruction bytes changed**: the `make-round` fingerprint in
  `LOCK.json` is new. Frozen runs keep their materialized instructions; a parked
  token-budget run picks up `make.md` through `workshop resume --refresh-tools`.
