# Direct render review

The exact generated geometry was inspected after the shape-final `r3-rounded-arch-ends` revision. Revision `r4-deterministic-monochrome-step` changes only source-level presentation colours, leaving those inspected silhouettes and all geometry unchanged.

- `review/closed-top.png` — direct top silhouette of the closed source assembly. Result: clean cloud boundary with no lightning or rainbow protrusion. This specifically rechecks the defect found in the first closed-state render, where the lightning tail escaped the upper-left lobe.
- `review/rainbow-part-top.png` — direct silhouette of the final rainbow print target. Result: recognizable semicircular band, broad hub/bridge, rounded arch endcaps, and no isolated body.
- `review/lightning-part-top.png` — direct silhouette of the lightning print target. Result: broad backed zig, round load-spreading junctions, square socket, and guide-pin root visible as connected geometry.
- `review/deployed-iso.png` — direct silhouette view of the deployed assembly for overall stack/envelope inspection.
- `review/deployed-scene-top.png` — direct top silhouette of the exact two coupled motif layers at the deployed endpoint, with the cloud temporarily omitted from the review view. Result: the rounded arch and broad lightning zig are both complete and legible in their assembled relative positions.
- `review/poses.json` — the exact camera record used for final source/STEP review.

The final source-vs-sibling-STEP comparison reported IoU `1.0000` for front, right, and top. The motif-only view is a presentation inspection derived from the same exact assembly placements; it does not remove or alter product geometry. The shipped CAD is intentionally monochrome to make fresh STEP bytes deterministic; optional print colour is not a geometry claim. Silhouette rendering does not show colour or interior relief and does not prove physical fit, torque, wear, or successful printing. Those remain explicitly unclaimed.
