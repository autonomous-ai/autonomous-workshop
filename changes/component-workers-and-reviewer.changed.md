A new Spark Make no longer repairs every Component in the root Manager
(ADR 0077). The Manager spawns one `component-worker` agent per Component with
only that Component's source, reference, camera, contract rows, nozzle and
shape-repair limit, and asks one reused `component-reviewer` thread per
Component when a worker reports build and print passing; disagreements go back
to the same worker. Only the reviewer views component images, and workers
never edit shared helpers. The host materializes both roles as sealed custom
agents in `.codex/agents/`; the reviewer runs at `low` reasoning effort and
the worker inherits the root's. `make_round` polls and `wait_agent` now wait
at 300000 ms. A component round's visual packet no longer binds other
Components' own source and STEP, so parallel workers cannot stale each
other's pending review. Assembly rounds, the blind review and final verification stay
with the root. Frozen runs keep their materialized protocol. Not yet validated
by a live run.
