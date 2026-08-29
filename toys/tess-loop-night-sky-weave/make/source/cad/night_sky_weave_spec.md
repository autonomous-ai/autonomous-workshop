# Night-Sky Weave CAD brief

- Model: nine-piece loose modular tile assembly with a review-only 3×3 reference layout.
- Task type: new multi-part, STEP-first product CAD.
- Units: millimetres.
- Coordinate convention: XY is the print bed; +Z is tile thickness; assembly origin is the center of the 3×3 mosaic.
- Inventory: three Crescent, three Comet, and three Star tiles.
- Tile envelope: 31.5 × 31.5 × 5.6; 4.0 corner radius.
- Reference storage mosaic: 98.5 × 98.5 × 5.6, using 2.0 clear gaps; it is not a combined print target.
- Edge grammar: four centered 1.8-wide recessed gates on both faces. Every gate has the same anchor and width so all families, rotations, and flips meet exactly.
- Tactile grammar: family-specific spaced dimple constellation plus one, two, or three corner pips; short rounded edge gates remain separate from the center field, and every material land clears 0.8 mm.
- Reversibility: top and bottom receive the same family grammar with a quarter-turn phase change; each 1.2-deep recess leaves a 3.2 continuous core and a tactile step above the 0.8 mm wall gate.
- Manufacturing assumptions: common rigid FDM filament, 0.4 nozzle, 0.20 layers, broad face down, no supports or hardware. Bottom gates are at most 1.8-wide short bridges.
- Paths: `night_sky_weave.step.py` is the review-only combined storage field; `part_crescent.step.py`, `part_comet.step.py`, and `part_star.step.py` are the actual print entries, each sliced at quantity three.
- Validation targets: exact tile/mosaic envelopes, nine solids in the review assembly, three copies per printable family entry, 2.0 display gaps, coincident gate anchors, 3.2 core, one connected body per print target, strict fit on a 220×220×220 bed, manifold meshes, and wall-thickness gates.
- Assumptions: loose placement—not a locking joint—is the intended connection; physical delight and handling remain untested.

No standard mechanical elements, bought parts, electrical loads, or image-derived geometry are present.
