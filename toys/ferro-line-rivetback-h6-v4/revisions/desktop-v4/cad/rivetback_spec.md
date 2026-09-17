# RIVETBACK H-6 V4 CAD brief

## Reference and design intent

- Model: original multi-part static mecha hexapod display kit, revision V4.
- Input: `C:\Modifi AI\spiderbot.png`, used as a style and proportion reference.
  The image has no dimensioned scale, so all dimensions are inferred. `[assumed]`
- Units and frame: millimetres; X left/right, +Y forward, +Z up, ground near Z=0.
- Visual intent: low matte-black spider chassis; long yellow beetle-like armor;
  layered, pointed and faceted prow; twin dorsal spines; six exposed segmented
  legs; slotted yellow shin blades; pale conduit loops; pointed black feet.
- Weapon policy: no cannon, muzzle, pedestal, or weapon/sensor cluster in the
  canonical V4 assembly.
- Target assembly envelope: approximately 242.0 X x 147.6 Y x 77.7 Z mm. `[assumed]`

## Parts and joints

- Canonical assembly: 61 labeled occurrences across 15 unique printable roles.
- Project entries: 19 `part_*.step.py` generators; four legacy weapon/sensor
  generators are retained for compatibility but are unused by V4.
- Three base carapace plates and three separate secondary dorsal shells create
  visible armor layering and black shadow gaps.
- Dorsal shells use downward-open keyed sockets. Matching keys grow from the
  base plates at the print-bed edge.
- Six legs repeat the hip yoke, upper beam/armor, lower beam/armor, conduit, and
  foot geometry through parameterized placements.
- Structural joints use keyed rectangular tenons and mortises, reinforced by
  two removable Allen-style through-pins per leg: 12 pins total.
- Pin shaft: 3.2 mm nominal diameter, 18 mm nominal length; round head: 8 mm `[assumed]`
  diameter with a hexagonal recess. `[assumed]`
- Joint behavior: rigid fixed-pose assembly. The circular fastener language is
  inspired by the reference, but these are not unconstrained ball joints.

## Manufacturing assumptions

- Process target: supportless FDM, 0.4 mm nozzle, 0.2 mm layer reference, `[assumed]`
  180 x 180 x 180 mm build volume. `[assumed]`
- Minimum structural wall gate: 0.8 mm; intentional visible details target `[assumed]`
  1.2 mm or greater where practical. `[assumed]`
- Small armor pegs use `SMALL_PEG_CLEARANCE_MM` 0.20 mm/side clearance. `[assumed]`
- Hip keys use `HIP_CLEARANCE_MM` 0.25 mm/side clearance. `[assumed]`
- Structural tenons use `TENON_CLEARANCE_MM` 0.25 mm/side clearance. `[assumed]`
- Lock pins use `PIN_CLEARANCE_MM` 0.20 mm/side clearance. `[assumed]`
- Dorsal keys use 0.25 mm/side clearance. `[assumed]`
- Each printable part has an explicit bed orientation. The combined assembly is
  a review artifact and is not intended to fit the print bed as one piece.

## Truth boundary and validation

- No articulation, walking, electronics, physical print, insertion force,
  retention force, fatigue life, or printer-specific fit is claimed.
- Required release checks: explicit generation, numeric-spec audit, topology,
  assembly validity, conclusive interference scan, strict-fit audit, bed bounds,
  mesh conversion, thickness, overhang/bridge gates, and multi-view snapshot
  review.
- Colors: industrial yellow `#D9A514`, charcoal `#191B1C`, pale conduit,
  and dark steel fasteners.
