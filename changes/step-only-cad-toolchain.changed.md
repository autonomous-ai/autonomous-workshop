- Resynced the vendored CAD skills to `autonomous-product-to-cad` `39a63f7`
  and adopted its removal in full: **STEP is now the only geometry format
  Workshop writes, seals or ships.** `scripts/export`, `meshlib`, `cadprint`,
  `repair_mesh` and the `check_mesh`/`check_thickness`/`check_overhang` gates
  are gone, so no stage may call a product printable or print-ready.
  `render_product` and `motion_presentation.py` tessellate the exact STEP in
  memory instead of reading an STL; the local `--print-preflight` mode and its
  `print_preflight_sha256` review binding are removed (signature review schema
  6 -> 7, motion evidence 1 -> 2); `make-round` reports a per-part build
  verdict instead of a wall verdict; the host CAD gate collapses to the single
  `digitally-verified-not-print-ready` tier and refuses a print-ready claim;
  Release publishes a digitally verified exchange solid whose printability is
  unverified; sealed products carry `parts/<name>.step` and no
  `assembled.stl`. The three.js host renderer and the Factory part keying
  tessellate sealed STEP into throwaway staging bytes. Frozen runs keep their
  materialized skills, proof instructions and `deep-economics-v1..v13`; new
  runs freeze `deep-economics-v14`. See ADR 0062.
