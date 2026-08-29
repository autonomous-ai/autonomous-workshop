# Rainspell Dial CAD project

`rainspell_dial.step.py` is the view-only named assembly. Each `part_*.step.py` is one printable part in its intended orientation with bed datum z=0. The wheel uses its cage-bottom datum so the skirt and guide walls grow upward; the plectrum and cap are inverted onto their broad top faces. `params.py` is the single dimension ledger; `validation.py` checks coupled datums before geometry; `parts/` owns geometry; `assemblies/product.py` owns placement only. No purchased parts, electronics, magnets, ballast, glue, or flexible material are used. Support-free intent is geometric and has not been confirmed by slicing or a physical print.

The combined STEP preserves native component labels but intentionally omits optional per-component presentation colors. The product is specified for one ordinary rigid filament, and omitting OpenCascade color records makes fresh isolated assembly generation byte-reproducible instead of allowing process-dependent style-record ordering.

Assembly procedure: insert and seat the rib deck, turn it 12° to its indexed stops; load the plectrum laterally into the wheel cage; slide the rigid keeper outward to its stop; seat the wheel; press, rotate 22.5°, and release the cap 1 mm into its pockets. Motion evidence is in `measure/motion.json`; physical fit and retention remain unverified.

Make-stage wheel refinement: the sealed Invent hub's 0.15 mm radial relief step was below the resolvable feature size of the declared 0.4 mm nozzle, and a closed upper annulus blocked deliberate keeper service. The generated wheel therefore retains the exact Ø14.5 journal bore and full 4 mm lower bearing land, then uses a 210° rounded C-profile from z=25.0 to 36.4. This removes the sub-nozzle ledge, provides a cap-controlled keeper path, and remains one connected printable wheel; it does not establish physical bearing behavior.

Rebuild with `python <cad-skill>/scripts/gen --write` on the combined and six part entries. Final verification uses `verify_project . --fresh --exports --unpowered --motion-manifest measure/motion.json --strict-fit`.

Nominal assembled envelope is 120 × 120 × 51.65 mm at maximum follower travel. All meshes are generator-produced; none is post-repaired.
