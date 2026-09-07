# Soren Voss — bounded Make contribution

Read the exact `.codex/agents/soren-voss.toml`, its bound inventor skill, WISH.json, and current STAGE.json. The Wish deliberately asks for a minimal acceptance-trial object. A plain circular-segment rocker honors that intent; no ornament, added mechanism, or purchased component is warranted.

## Physical promise

Place the cylindrical arc on a level desk, flat chord uppermost. Give the top a small sideways nudge across its 71 mm span. The low center of mass rises during rocking, so gravity urges it toward the centered pose. Desk contact and material losses are expected to dissipate motion, but actual settling time and friction have not been physically tested. The object is manually energized and has one intended rocking degree of freedom.

## Analytical design basis

Use a uniform solid lower circular segment of radius R=40 mm with horizontal chord 18 mm below the curvature center, extruded 28 mm. Its overall dimensions are 71.4423 × 28 × 22 mm. With a=sqrt(R²−18²), segment area A=R² acos(18/R)−18a=1123.4690 mm². Volume is 31457.1326 mm³. The centroid distance below the curvature center is d=2a³/(3A)=27.0473 mm, placing it 12.9527 mm above the desk at rest. Assuming uniform PLA density 1.24 g/cm³ gives a calculated nominal mass of 39.01 g; this is not a measured print mass.

For ideal rolling contact through angle θ, centroid height is R−d cos θ and gravitational energy increase is mgd(1−cos θ). Therefore θ=0 is a strict stable minimum and the restoring generalized torque is −mgd sin θ. At 20° tilt, the centroid rises 1.6312 mm. The circular arc permits ideal rolling contact up to ±63.2563° before the chord endpoint reaches contact; this mathematical boundary is not a recommended operating tilt. Use gentle nudges within about ±20° and manually reset if overturned. The flat top and flat ends permit other stationary placements, so never describe it as self-righting from every pose.

## Printing and use

Print on either flat extrusion end, with the 28 mm extrusion vertical: each layer repeats the same supported segment footprint and there are no designed overhangs or internal voids. Specify a solid print/100% infill to preserve the uniform mass basis as closely as practical. Real material distribution, extrusion accuracy, surface texture, desk slope, and friction remain physical validation limits. Keep the primary contact arc smooth; remove any brim or seam burrs carefully. No assembly or hardware is needed.

Keep the silhouette restrained and expose the broad curved underside and chord clearly in the preview. End-edge softening is optional only if remeasured in exact CAD; avoid changing the analytical cross-section without updating mass properties. All numerical results above describe the unmodified prism, not any subsequently filleted variant.

## Required verification and truthful boundary

Root should compare exact CAD volume and centroid with these predictions, verify one connected valid solid, inspect the exact printable mesh and flat-end orientation, and evaluate collision-free arc contact and monotonic COM rise over the intended ±20° range. A rigid-body energy calculation establishes restoring geometry, not physical settling, print success, durability, or human response. Spark does not run Playtest. This contribution does not claim CAD inspection or independent render review and invokes no finalizer.

Calculation provenance: numerical formulas evaluated using JavaScript Math in the native functions runtime. Bounded Python probes failed due unavailable system developer tools and denied execution of the materialized venv interpreter; no dependency on Python is needed for this analytical assessment.
