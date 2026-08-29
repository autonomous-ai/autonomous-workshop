- Resync the vendored `cad`, `design-reference`, `electromechanical-integration`,
  `image-to-cad`, and `step-parts` skills to
  `autonomous-ai/autonomous-product-to-cad` `4800bbe`, refreshing `LOCK.json`
  and the provenance ledger. `step-parts` is byte-identical to the previous
  snapshot; `cadgen` remains pinned at 0.4.19.
- `design-reference` becomes Internet research guidance and ships no client:
  `design_refs.py`, `catalog_build.py`, `data/sources.json`,
  `references/catalog-schema.md` and its tests are gone, along with the bundled
  Fusion 360 Gallery index and its `.design-reference-cache` download. Research
  results are now cited by URL, revision and license in build-spec section 6d
  instead of being fetched into `<project>/ref/external/`.
- `verify_project` no longer runs a `design_refs verify` gate and no longer
  exempts `ref/external/` from the component-STEP audit, so every STEP under
  `ref/` must carry a `measure/mounts.json` row; `check_power` drops the same
  carve-out from its manifest checks.
- `image-to-cad` reorders Step 5 into decompose, research, then select, and adds
  build-spec section 6g — a frozen per-domain design selection that `cad`
  implements rather than reopening. `electromechanical-integration` gains
  `references/component-selection.md` for the powered-component research that
  feeds it.
- **Materialized instruction bytes changed**: four of the five locked skill
  fingerprints are new, so a run parked before this change must be restarted
  rather than resumed; resume fails closed on the materialized-instruction-hash
  mismatch.
