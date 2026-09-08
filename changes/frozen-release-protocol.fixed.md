- Bind each Release packet and gate to the immutable run-local finalizer so a
  run's Release contract follows its materialized toolchain: manual-first runs
  require NativeRelease schema v2 (Quest) or v3 (Spark and Forge) with
  `MANUAL.pdf`. A legacy `MANUAL.md` run can still be read and validated as
  schema v1, but the host refuses to finish it as a current Release; it needs
  an explicit migration through today's gates.
