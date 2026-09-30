- Resync the vendored `cad`, `design-reference`,
  `electromechanical-integration`, `image-to-cad`, `product-design`,
  `step-parts` and `wiki` skills to `autonomous-ai/autonomous-product-to-cad`
  `b149710`. `verify_project --likeness-entry LABEL=ENTRY` scores a reference
  that shows one piece of a set against that piece. A multi-colour print entry
  may define `gen_print_union()` for the print gates to measure. `measure_image`
  handles a CAD viewer's gradient backdrop. Review renders light both sides of
  a face. The wiki gains pages on push-to-turn indexers and carved figures on
  split prints.
- **A build spec lists what is not printed.** Section 6h names every bought
  part, fastener and consumable with quantity and order name, and
  `check_spec_format`, which `verify_project` runs in every mode, fails a spec
  that has a section 6 but no 6h.
- **A print union must be the plate's own material.** Workshop's `printlib`
  refuses a `gen_print_union()` whose volume or bounding box differs from the
  regions `gen_step()` exports. The print gates, and the host's print-ready
  rerun, therefore never measure a stand-in.
- **Materialized instruction bytes changed**: the `cad`, `image-to-cad`,
  `product-design` and `wiki` fingerprints move. A run parked before this
  change must be restarted rather than resumed. A refreshed run or a
  `workshop fix` whose spec predates 6h must add that subsection before its
  final verification passes.
