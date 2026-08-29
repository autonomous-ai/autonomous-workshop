# Final visual and package inspection

- Host rejection repair: the prior coloured assembly STEP changed only in nondeterministically ordered presentation-style entities during a fresh isolated export. Per-occurrence display colours were removed because side identity is geometric, not chromatic.
- Independent-process determinism check: two clean assembly generations in separate directories produced byte-identical STEP files with SHA-256 `d7bf1d573c57bf466104b84ec25d509637e6f963482a2eb2ac83c7c0769f7de5`.
- Exact host-mode stability check: two consecutive `verify_project cad --fresh --exports --strict-fit` runs passed; all 29 declared STEP/STL/GLB outputs were byte-identical between runs. Only `measure/verification-pipeline.md` changed, as expected for its run timestamp and timings.
- Assembly source/STEP silhouette drift: PASS; front IoU 0.9999, right 1.0000, top 1.0000 at 420 px and 0.1 mm tessellation tolerance.
- Grid queen source/STEP silhouette drift: PASS; front/right/top IoU 1.0000.
- River queen source/STEP silhouette drift: PASS; front/right/top IoU 1.0000.
- Whole-set silhouettes inspected: `snap/front.png` shows the monotonic pawn-to-king hierarchy and projecting queen decks; `snap/iso.png` shows the complete opening layout without detached pieces.
- Side-language silhouettes inspected: `snap/pieces/queen/iso.png` shows the River round plinth; `snap/pieces/grid_queen/iso.png` and `snap/pieces/grid_rook/iso.png` show the Grid square plinth.
- Root combined STL check: PASS; 18,344 triangles, 9,222 vertices, watertight, manifold edges and vertices, consistent winding, positive 235.78 cm³ volume, 33 connected shells, and 208.0 × 208.0 × 58.6 mm bed envelope.
- Root metadata audit: `assembled.step.json` binds exact SHA-256 values for `assembled.step` and `assembled.stl`; every referenced relative path exists inside the product root.

These are digital geometry and image inspections only. They do not establish a successful physical print, durability, or human play response.
