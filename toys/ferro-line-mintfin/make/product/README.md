# Mintfin axolotl dragon

Mintfin is a 180 mm desk toy with nine interlocked body sections, coral gills and fins, and three interchangeable faces: happy, sleepy and angry.

## Files and colors

The requested STL/3MF print set is preserved as engineering evidence in `../engineering/prints/` beside this product folder. The published product package is built from the sealed STEP files.

- `../engineering/prints/Mintfin-chain.3mf`: complete articulated creature, arranged as one build item.
- `../engineering/prints/Mintfin-faces.3mf`: three separate face plates.
- `../engineering/prints/Mintfin-hinge-coupon.3mf`: three clearance-test pairs.
- Matching STL files contain the same shapes, and individual face STL files are also supplied. STL does not store the four-color assignments.

Use four PLA colors with an AMS/MMU: **mint** body, **coral** gills and fins, **cream** belly and face, **charcoal** eyes, claws and horns. The 3MF files contain named volumetric color regions and standard material colors. Assign these regions to the corresponding four filament slots in your slicer; automatic AMS slot mapping is not verified. Keep all regions together as parts of one object. No paint, glue or purchased hardware is needed.

## Print the coupon first

Use the same filament and settings intended for the creature. The coupon uses the same pin and bearing geometry as its joints. Count the rim notches on each test pair:

| Rim notches | Radial clearance |
|---|---:|
| One | 0.35 mm |
| Two | 0.45 mm |
| Three | 0.55 mm |

Let the plate and parts cool fully before removal or flexing. Hold both handles of each pair and try a gentle turn. Do not force a stuck joint or pry it with a tool. Select the smallest clearance that releases and turns freely. The supplied creature uses **0.45 mm**. If the two-notch pair does not release cleanly, adjust the shared CAD clearance parameter and regenerate the creature before printing it; scaling an STL changes every dimension and is not a clearance adjustment.

## Print settings and arrangement

Suggested starting settings for a standard FDM printer:

- 0.4 mm nozzle; 0.20 mm layers.
- Three walls; 20% infill.
- Supports off; no brim between moving parts.

These settings require checking on your printer. **Keep every chain segment in the delivered arrangement. Never auto-arrange, separate or independently move its interlocking sections.** Their relative positions create the captured joints during printing. Keep the flat undersides on the bed.

Print all three faces separately from the chain, with their flat backs down and expressions facing up. Preserve the faces' latch tabs and slots. Check fit with a complete face before repeatedly swapping expressions.

## Release and change the face

After the print cools, support neighboring body sections close to a joint and ease them through a small turn by hand. Work along the chain one joint at a time. Stop if a joint resists; do not twist the creature by its tail, horns or gills.

To remove a face, gently squeeze its two exposed arm tips inward at the nose and lift the plate. Match the replacement plate to the recessed surface on top of the head, with its release tips toward the nose. Lower it evenly and use gentle fingertip pressure to seat the catches. Stop if it needs force. No magnets or magnet wells are included: this version uses the snap-fit option.

## Verification limits

Digital checks do not establish successful printing, clean joint release, working motion, physical fit or durability. Those outcomes remain unverified on a physical print. This is a small-parts desk toy; keep loose faces away from young children.
