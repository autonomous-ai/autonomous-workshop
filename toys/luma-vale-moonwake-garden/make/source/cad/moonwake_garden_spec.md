# Moonwake Garden — Make round 2 CAD brief

## Product and coordinates

- Model: three-part hand-powered rotary optical toy; STEP-first Tier-2 assembly.
- Units: millimetres.
- Source: sealed `artifacts/invent/r0002/invented.json`, artifact SHA-256 `5586d08aff1c1916dc9d78ff6864e0022343f43a1d48ec07c9771a5a55aa5e34`.
- Coordinate system: rotor axis at the origin; XY is the broad print/front-view plane; +X is the thumb side, +Y is top, and +Z is toward the decorated face. World angles run counter-clockwise from +X.
- Output paths: combined generator `moonwake_garden.step.py`; printable entries `part_rear_chassis.step.py`, `part_sector_rotor.step.py`, and `part_front_garden_mask.step.py`; sibling STEP/STL exports; root copies `assembled.step` and `assembled.stl`.
- Envelope [observed]: 84 × 76 × 6 mm with 10 mm plan corner radii.
- No standard or purchased components are present. All three pieces are printed in one opaque material; no step.parts lookup is applicable.

## Parts, datums, and fits

1. Rear chassis [observed]: broad rear datum z=0; 1.8 mm base; R32 optical field; 9 mm hub; three 2.4 mm radial stems at world 30°/150°/270°; 6.0 mm spindle; three 2 × 4 × 0.3 mm thrust pads at R31.5. The guide is R35.4–37.4 from z=1.8 to3.6, except for its right rear bay and detent isolation. Four collars at (±34,±27) seat the front at z=3.6. Split snap stems are 3.2 mm with 3.8 mm maximum conical heads and 0.8 mm splits. The spindle/base transition uses the sealed R1.0 root profile and retains the 6.0 mm running diameter.
2. Rotor [observed]: 70.0 mm diameter ×1.2 mm; 6.6 mm bore derived from the 6.0 mm spindle plus 0.30 mm per-side clearance with `cadfits.slot_for`; lower face z=2.1 and upper face z=3.3 in assembly. The 70.8 mm guide ID is derived from the rotor plus 0.40 mm per-side clearance. Normal rim web is3.50 mm.
3. Front garden mask [observed]: underside z=3.6; structural thickness1.6 to z=5.2; 1.2-wide vines rise0.4 and terminate in rounded caps 0.35 beyond each pointed petal's half-length, avoiding cusp knife edges; the central moon rises0.6; snap heads define the maximum z=6.0. Snap holes3.4 and head reliefs3.9 are derived once from the corresponding male diameters.

The four 3.8 mm-envelope split snap heads retain a true 45-degree lead from a 0.35 mm axial maximum-diameter land to a printable 2.6 mm blunt pilot. Each side rises from a 1.0 mm stem into a 1.2 mm-wide, blunt, R0.1-cornered head prong rather than a slit cylinder. Its solved 1.823 mm Cartesian cap and rounded corner put the exact furthest plan point at R1.894111, wholly inside the sealed R1.900 maximum and leaving0.055889 mm radial clearance to the R1.950 relief; the sealed 0.8 mm split remains open. The 5.0 mm spacer collars retain a flat seating land inside an R0.4 outer-top fillet. Each 2.4 mm rear spoke overlaps the R32 field boundary by2.0 mm to prevent a cusp at its base-frame union. Full-height 4.8 mm round local bosses support the exact 2 x 4 x 0.3 thrust-pad envelopes, whose R0.4 corners avoid unsupported sharp tips. The continuous R32 field arcs and guide-ID top arc use0.2 mm chamfers, with the two detent-crossing fragments left unchamfered and their vertical junctions rounded instead. The detent free-cap is an exact 0.8 mm centreline arc whose radial boundary is coincident with the annular slot end, eliminating the prior chord/arc wedge. The 19 mm rear thumb bay begins at R31 and uses a polar throat that crosses the guide transversely. Its layered breakthrough and detent-junction edges receive bounded plan fillets; no running fit surface is offset below the top entry chamfer.
4. Axial fit [observed]: the front underside at3.6 minus rotor top at3.3 gives0.30 mm total running clearance. The rotor is supported at z=2.1 by the thrust pads, not by the rear plate.
5. Print stance [observed]: each part is generated broad-face-down with bed datum z=0. Build bed declaration: `--bed 220x220x250`.

## Repaired detent and optical geometry

- The only rotor window [observed] is R9.0–31.5, local35°–145°. Four R2.0 inward corner fillets are constructed inside that raw polar envelope.
- Notch cut envelopes [observed] use exact 2.4 mm chords on R35 and a deepest R34.45 point at local−45°/+75°/+195°. The +75° cut lies in the sector phase; 34.45−31.5=2.95 mm, which exceeds the sealed2.50 mm minimum by0.45 mm. Other notch-to-sector distances are larger.
- The fixed detent [observed] is an annular cantilever with centerline R36.0, band R35.4–36.6, z=0–3.6, root at world−64.0986°, and free tooth at−45°. The 19.0986° arc is12.0 mm at R36. A full-depth R36.6–37.4 outer slot and a local base opening through the beam footprint remove every plate bridge across the free arc; a1.0 mm root bulb is the sole frame attachment. The1.3 mm tooth lobe centers at R35.4, so its tip is R34.75 and leaves0.30 mm to the R34.45 notch root.
- The rear guide bay [observed] starts at x=31 and is19 mm high. The front does not repeat that rectangle: its contained polar portal is R32–34 and world±12° with four R0.8 inward corners. Its radial margins are0.50 mm to the optical sector and0.45 mm to the deepest rotating notch cut.
- The seven sealed 1.4 mm tangential ×0.8 mm radial grip footprints remain centered at R33.35 and local angles−9° through+9° in3° steps, but Make blends their overlapping control zone into one printable R32.95–33.75, local±10.5° trench with contained R0.3 corners. Separate full-depth capsules leave only about0.35 mm top lands and fail the0.8 mm wall gate. The blended0.30 mm recess preserves all seven centers, stays within the portal, and leaves a continuous0.90 mm floor; it is exposed only at the home pose.

## Face optics and state contract

- Eighteen fixed pointed-lens apertures preserve the sealed coordinates: five Cassiopeia, six Cygnus, and seven Ursa Minor/Little Dipper. Each nominal through aperture is4.8 ×2.2 mm and radial. A ruled0.30 mm-deep expansion adds the actual45° rear-entry chamfer.
- Stable rotor poses are0°,−120°,−240°. The corresponding local notches−45°,+75°,+195° all transform to the fixed world−45° tooth.
- Deterministic completion requires exact nominal-lens containment for all selected petals, zero sector intersection for every nonselected petal, no two complete named beds at any1° full-turn sample, no rear-stem occlusion, and no portal leak through any sector or notch pose.
- The ±20° ray proxy shifts the rotor-plane footprint by0.109191 mm across the0.30 mm gap. It is a geometric isolation check, not evidence of brightness, recognition, or human delight.
- The smallest computed rear-chamfer ligament must remain at least1.8 mm; nominal current value is1.944357 mm.

## Motion and evidence boundaries

- `measure/motion.json` uses `motion_proxy.proxy.py`, whose only change is suppressing the elastic tooth. This makes the 360° rotor clearance question rigidly measurable while leaving guide, spindle, front, and all snap geometry exact. Its non-entry suffix prevents ambiguity in host assembly discovery. It also checks rotor loading and front capture.
- `measure/motion_snap_proxy.json` uses `snap_proxy.proxy.py`, whose conical heads are reduced to the stem envelope solely to check the seating path. Its non-entry suffix prevents ambiguity in host assembly discovery. The exact expanded heads separately block direct withdrawal.
- Neither proxy proves elastic force, flexure strain, retention force, safe service removal, whitening, fatigue, wear, or cycle life. These require same-material physical coupons.
- CAD and mesh checks do not prove a successful print, printer-process fit, optical brightness, pocket comfort, discovery, constellation recognition, or human response. Those remain physical and Quest Playtest evidence.

## Required final checks

- Static Tier-2 layout; source parameter audit; product-specific planar/optical audit.
- Fresh multi-target STEP generation, facts/planes/positioning, per-entry topology validation, and exact assembly interference.
- Bed/footprint/solid fit on all three printable entries; both motion manifests; printable STL mesh checks;0.4 mm-nozzle thickness checks; assembled STEP/STL checks.
- Product-derived isolated, exploded, indexed-state, rear-path, detent, and portal/grip views from the final exact source.
