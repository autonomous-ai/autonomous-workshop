# Orbit Gobbler CAD brief

- Model: a new multi-part, hand-cranked desktop kinetic assembly implementing the sealed C-Mouth Lunar Cam Invent concept.
- Inputs: `STAGE.json`, `artifacts/invent/assignment.json`, and `artifacts/invent/invented.json`; no reference image.
- Units: millimetres.
- Assembly coordinates: origin on the base centre; +X right, +Y rearward, +Z up. Orbit axis is world +Y at `(0, 0, 106)`.
- Overall assembled envelope: 190 W × 80.7 D × 200 H mm; base 190 × 70 × 10 mm; maximum moon sweep Ø164 mm. The corrected height is the exact consequence of the sealed 106 mm orbit height plus the 94 mm frame radius. The extra 10.7 mm depth is the rear pinion sleeve/retainer stack introduced to remove the impossible shaft crossing from the front spoke plane.
- Mechanism: printed 20T pinion drives printed 40T carrier at exact 37.5 mm pitch-centre spacing. A captive radial slider follows a fixed two-wall cosine cam from radius 58 to 70 mm. One carrier orbit equals two crank turns.
- Cycle: 47–83° swallow, 83–360° plus 0–3° visible inner orbit, 3–39° pop, 39–47° outer dwell. The longer half-cosine transitions reduce the nominal peak pressure angle to about 25.1°.
- Construction: 23 printed pieces across 19 unique part types. Separately moving, removable, or oppositely oriented pieces remain separate printable solids. The central-axle and crank-grip retainers share one small snap-clip type because both grooves have the same 6.4 mm core diameter and use the same 14.0 mm OD, 6.8 mm ID, 2.0 mm-thick clip geometry. Their adjacent thrust washers also share one type: both serve 8.0 mm shafts with the Invent-specified 8.4 mm bore, 16.0 mm OD, and 2.0 mm thickness.
- Main print assumptions: 200 × 200 × 220 mm bed, 0.4 mm nozzle, 0.2 mm layers, 4.0 mm nominal structural plate, 0.8 mm absolute two-line minimum.
- Mates: every bore/peg or slot/tab pair derives one side through `cadfits`; no mating pair is typed independently.
- Safety geometry: one stationary C-mouth bezel replaces the two fragile lip pieces and ties both arcs directly into a rounded outer rib plus four overlapping round mounting posts. Moon/bezel axial clearance is at least 1.5 mm and radial swept clearance is at least 4 mm. The 40T gear is covered by a fixed Ø56 eye and the pinion by a Ø32 crank hub shield; running gaps remain probe-accessible and exposed corners are rounded or chamfered in profile.
- Outputs: combined assembly STEP, per-part STEP/STL, root `assembled.step`, root assembly-preview `assembled.stl`, product metadata, motion/spec/fit evidence, and root `assembled.step.json` verification.
- Validation targets: exact 20:40 ratio and 37.5 mm centre distance; 360° phase partition; nominal cosine-cam peak pressure angle below 27°; 12 mm radial travel; 0.45 mm carrier endplay; at least 2 mm axial separation between the front spoke/slider deck and rear gear deck; bed fit; positive-volume closed solids; no assembly clash above trusted tolerance; motion paths; watertight/manifold STL; no wall below 0.8 mm.
- Evidence boundary: CAD and rigid-body checks establish digital geometry only. They do not establish physical print success, friction, torque, retention force, wear, durability, safety certification, or human delight.

## Standard-part search record

The CAD workflow's form trigger required a step.parts search before authoring gears. A query for `spur gear module 1.25 20 tooth` could not reach `https://api.step.parts` because network/DNS is unavailable in this managed sandbox. That result is inconclusive, not a catalog miss. No catalog part was downloaded or dimensioned. The sealed Wish independently forbids purchased hardware, so both gears are authored as parametric printed geometry from module, tooth count, pressure angle, and backlash.

## Dimension provenance

All mechanism dimensions are `[sealed]` from the accepted Invent concept unless a comment in `params.py` marks a Make-level derived value. Clearances derived by `cadfits` are `[derived]`. Cosmetic facet counts and shallow decorative relief are `[assumed]` and do not control motion.

## Make-level risk corrections

Independent Bob review found that the Invent-layer coplanar carrier would sweep its spokes through the pinion, that a D pilot could not execute the specified bayonet rotation, and that separate mouth lips were unnecessarily fragile. The Make geometry therefore preserves the accepted concept while changing implementation: a single support-free carrier has a front spoke/slider deck, central spacer, and complete rear 40T gear deck; the pinion sleeve runs rearward through a derived-clearance frame bore to a rear crank, so no fixed shaft crosses the rotating front spoke plane; bayonet pilots are round with unequal lugs while torque is carried by a D-shaped slider interface; the mouth is one directly fused ribbed bezel; follower slots include 1 mm overtravel at both ends and 5 mm end material; and the central axle, pinion sleeve, and grip post use annular grooves with separate printable horseshoe snap clips instead of thin transverse key slots.
