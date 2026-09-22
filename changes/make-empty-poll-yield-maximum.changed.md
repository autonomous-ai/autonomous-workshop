- **Make waits for a long command in far fewer requests.** Every request
  re-sends the whole session and the product budget counts that re-sent input,
  so a poll that waits one second costs the same as one that waits thirty and
  buys thirty times less waiting. Measured across 37 product rollouts (212M
  observed tokens): empty `write_stdin` polls cost 55.8M tokens, 26% of product
  spend, for 170 minutes of waiting that returned identical bytes either way.
  Each poll carried a median 581 tokens of new content and was charged a median
  92,865.
- **Where `1000` came from.** `yield_time_ms` appears nowhere in a run's
  instructions -- not in `base_instructions`, not in any developer message,
  only in the model's own calls. The one numeric example the code-mode tool
  description carries is the `exec` pragma
  `// @exec: {"yield_time_ms": 10000, "max_output_tokens": 1000}`, and an
  isolated reproduction emitted `yield_time_ms: 1000, max_output_tokens: 1000`
  together, so the value is transposed from the output budget. It is worse than
  passing nothing: the `exec` default is 10000 ms, and an empty poll enforces a
  5000 ms floor regardless. Both files now name that example.
- **The rule now lives where a compaction cannot drop it.** A live Spark run
  followed the guidance while `references/make.md` was in the session, held it
  across one compaction that re-read the file, then reverted to
  `yield_time_ms: 1000` on all five polls after a second compaction dropped the
  file without a re-read. The session's `world_state` re-emits the run-root
  `AGENTS.md` after every compaction and never re-emits a reference file, so
  the constitution carries a short form of the rule and `references/make.md`
  keeps the detail.
- 30000 is the practical ceiling, not 300000. A `write_stdin` poll asking
  60000 was measured returning at 31.0 s, four times in one run, matching the
  30.0 s maximum across the whole corpus. Anything above 30000 is harmless but
  buys nothing.
- The rule also covers `wait`. When an `exec` cell yields a cell id instead of
  finishing, the model must continue that cell, and a `wait` at 1000 or 10000
  wastes a request exactly as a short `write_stdin` poll does.
- The constitution states the cost in runtime-neutral terms before naming the
  Codex tools, and records that a runtime whose shell tool blocks until the
  command exits -- Claude Code's `Bash` -- needs a long timeout and no polling.
  Claude product runs were measured making 3,844 `Bash` calls and zero
  `BashOutput` polls.
- `codex_run_report.py` now reports what empty polls cost and which yield each
  one asked for, so the next run can be checked without re-deriving it.
- Guidance only: no gate, schema, review allowance or finalizer check changes,
  and no change to what a poll returns. **Materialized instruction bytes
  changed**: the run-root `AGENTS.md` and the `make-round` fingerprint in
  `LOCK.json` are new. Frozen runs keep their materialized instructions; a
  parked token-budget run picks up `make.md` through
  `workshop resume --refresh-tools`.
