- Add `tools/publish_direct.py`, which publishes a CAD project built outside
  Workshop (a `--cad-dir` project or a packed `--archive`) through the
  unchanged Spark path: the same schema 6 carrier, Factory adapter, effect
  ledger and readback. It runs as a dry run by default, which prints the
  exact handoff, the gate evidence and every reason `--live` would refuse,
  and reads no credential. `--live` requires fresh gate evidence:
  `measure/direct-publish-evidence.json` binds a `verify_project --fresh
  --print-gates` run (`--verify`) to the exact source and STEP bytes, and
  every failing gate must be owner-declared with `--known-gate-failure`.
  `--live` also needs the Inventor's own credential, refuses an archive
  packed for another Inventor, and refuses re-import. It prints a
  `publication-record` with the receipt's identity hashes and records that
  no Wish ran (`docs/PUBLISH_DIRECT.md`). `build_release_handoff` and
  `make_output_release_product` expose the offline handoff and the Spark
  page derivation without changing either.
