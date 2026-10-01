- Resync the vendored `cad`, `design-reference`,
  `electromechanical-integration`, `image-to-cad`, `product-design`,
  `step-parts` and `wiki` skills to `autonomous-ai/autonomous-product-to-cad`
  `b67636e`. Only one wiki page moved upstream. `modeling/element-libraries.md`
  adds "Other build123d libraries": dry-run an install before running it,
  because pip backtracks to an old build123d rather than failing. It also gives
  verdicts for `gflabel`, `gfthings`, `gridfinity_build123d`, `bd-vslot` and
  `capistry`. Those verdicts were measured on Python 3.14. On Workshop's 3.11
  venv, `gflabel` installs cleanly and `capistry` does not resolve; neither
  difference can downgrade the toolchain. `PROVENANCE.md` records the measured
  results.
- **Materialized instruction bytes changed**: the `wiki` fingerprint moves. A
  run parked before this change must be restarted rather than resumed.
