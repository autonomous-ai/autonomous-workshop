- Resync the vendored `cad`, `design-reference`, `image-to-cad`, and
  `step-parts` skills to `autonomous-ai/autonomous-product-to-cad` `5d1e24a`,
  refreshing `LOCK.json` and the provenance ledger. The CAD runner gains a
  `verify_project --self-check` fixture suite and an explicit
  `--powered`/`--unpowered` classification for `--image-derived` final runs;
  the thickness, fit, layout, mount, and motion gates stop reporting an
  inconclusive result as a skip; the image workflow gains a likeness-gate
  history with audited acceptance for a stalled loop and splits its `SKILL.md`
  into three new references. `cadgen` remains pinned at 0.4.19.
- Vendor and lock the upstream `electromechanical-integration` skill, which
  specifies power, control, wiring, and lighting for a functional electrical
  load and adds the `check_power` gate that the `cad`, `design-reference`, and
  `image-to-cad` skills already name. It joins `PRODUCT_RUN_DOMAIN_SKILLS`, so
  it is materialized into every product run, and its name is reserved against
  Inventor extension collisions. `verify_project` resolves its gate as a
  sibling materialized tree; a project that declares no `measure/power.json`
  still records a skip.
- **Materialized instruction bytes changed**: every locked skill fingerprint is
  new and one more skill is materialized, so a run parked before this change
  must be restarted rather than resumed; resume fails closed on the
  materialized-instruction-hash mismatch.
