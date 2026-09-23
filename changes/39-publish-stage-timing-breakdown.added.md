- Extend the sealed Toy Archive's `TIMING.json` to schema version 2, adding a
  `breakdown` of the Run's per-stage, per-operation timing (durations only, no
  absolute wall-clock instants) sourced from the host-state
  `wish-run-timing.json` record introduced for issue #38. The existing schema
  1 fields (Wish intake to publication, including the `unavailable` path) are
  produced identically to before; only `schema_version` and the added field
  change. A `measured_ms`/`total_ms`/`unmeasured_ms` honesty counter is always
  published, even for a Run with no observed spans, rather than an absent
  breakdown. Stage keys reuse the same strings as `TOKENS.json`'s stage
  vocabulary, so the two files join without remapping.
