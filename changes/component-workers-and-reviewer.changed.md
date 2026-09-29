A new Spark Make no longer repairs every Component in the root Manager
(ADR 0077). The Manager spawns one `component-worker` agent per Component with
only that Component's source, reference, camera, contract rows and nozzle; the
worker repairs from the round summary and never views images. One reused
`component-reviewer` thread per Component gives the visual check the Manager
records once a round's checks pass, and judges acceptance when an image stalls
out below the 0.90 floor (ADR 0075); disagreements go back to the same worker.
Workers never edit shared helpers. The host materializes both roles as sealed
custom agents in `.codex/agents/`; the reviewer runs at `low` reasoning effort
and the worker inherits the root's. `make_round` polls and `wait_agent` now
wait at 300000 ms. `make_round` keeps its pass rule; a component round's
visual packet no longer binds other Components' own source and STEP, so
parallel workers cannot stale each other's pending review. Assembly rounds, the blind
review and final verification stay with the root. Frozen runs keep their
materialized protocol. Not yet validated by a live run.
