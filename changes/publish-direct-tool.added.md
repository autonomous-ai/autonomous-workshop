- Add `tools/publish_direct.py`, which publishes a CAD project built outside
  Workshop (a `--cad-dir` project or a packed `--archive`) through the
  unchanged Spark path: the same schema 6 carrier, Factory adapter, effect
  ledger and readback. It runs as a dry run by default, which prints the
  exact handoff and reads no credential. `--live` needs the Inventor's own
  credential and refuses re-import. It records that no Wish or gate ran
  (`docs/PUBLISH_DIRECT.md`). `build_release_handoff` and
  `make_output_release_product` expose the offline handoff and the Spark
  page derivation without changing either.
