# Build spec contract

Write the spec as data or concise Markdown with these sections:

1. Product intent: user, job, interaction, environment, age/safety boundary.
2. Visual intent: three adjectives, silhouette, form hierarchy, landmarks,
   materials/colors, seams, forbidden visual shortcuts, canonical views.
3. Manufacturing envelope: process, printer, bed, nozzle, layer, materials,
   support/post-processing limits, target mass/time/cost.
4. Part inventory: stable ID, quantity, purpose, material, canonical source,
   expected solids/shells, print orientation, assembly placement.
5. Parameters: value, unit, range, provenance (`observed`, `derived`, `assumed`),
   confidence, and dependents. One source owns every mating dimension.
6. Fits and contacts: part pair, contact surfaces, fit class, calibrated target,
   load direction, assembly access, and evidence required.
7. Motion: moving part, axis/path, limits, sampled poses, allowed contacts,
   forbidden collisions, and physical claims not covered by rigid geometry.
8. Splits/connectors: split plane, keys/fasteners/inserts, tolerances, strength
   direction, trapped-volume risk, and assembly order.
9. Release gates: required deterministic checks, independent reviews, slicer
   profile, physical tests, exact typed core measurements from
   [release-evidence.md](release-evidence.md), project-specific stricter
   thresholds, and explicit conditions that result in `held`.

Reject a spec with no scale anchor, unnamed parts, contradictory quantities,
unowned mating dimensions, or an undeclared manufacturing process.
