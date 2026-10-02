Motion checking reuses immutable placed operand preparation and supports bounded
process workers for coupled nominal sweeps through `WORKSHOP_MOTION_WORKERS`
(default 1). Parallel results retain original pose and pair ordering, the full
sample table, collision thresholds, Boolean consistency checks, whole-cycle
drive evidence and retention closure. Worker failure or deadline expiry remains
inconclusive; outstanding workers are terminated and reaped on early exit.
