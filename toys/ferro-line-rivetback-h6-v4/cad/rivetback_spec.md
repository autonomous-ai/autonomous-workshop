# Rivetback H-6 V4 build specification

Project directory: `artifacts/make/r0001/product/rivetback_h6_v4/`

## 1. Overall read

This is a source-preserving successor to an existing fixed-pose multi-part
mecha hexapod. Four references were inspected: one photograph, two isometric
V4 renders, and one front V4 render. `[observed]` The source and V4 renders
govern geometry; the photograph governs style. `[observed]` Bilateral and
three-leg-per-side repetition are explicit in the source. `[observed]`

The unmistakable signature is a low charcoal six-legged underframe carrying
three longitudinal layers of faceted industrial-yellow armor, with pale knee
conduits, exposed round collars, hex-recess pin heads, twin dorsal spines, and
six blunt-pointed black feet. `[observed]` The canonical successor has no
weapon, cannon, muzzle, turret, pedestal, or sensor crown. `[observed]`

## 2. Top view — plan down -Z

The source builds a 242.0 mm left-right assembled span and a 147.611 mm `[observed]`
fore-aft span. `[observed]` A clipped 68.0 × 76.0 mm chassis sits centrally.
`[observed]` Three yellow base plates run along Y: fore depth 36.0 mm at
[observed] Y=29.0 mm, center depth 28.0 mm at Y=-3.0 mm, and aft depth 30.0 mm at
Y=-32.0 mm. `[observed]` Their faceted outlines and gaps must remain distinct.

Six roots repeat at source-defined angles 32°, 0°, -32°, 148°, 180°, and
-148°. `[observed]` Each leg grows radially through yoke, upper beam, lower
beam, and foot. `[observed]` Hidden geometry is limited to keyed sockets and
plate mounts documented in section 6. `[observed]`

## 3. Front view — elevation along +Y

The source-built total height is 77.7 mm. `[observed]` The chassis assembly
datum is Z=30.0 mm and the leg roots are at Z=38.0 mm. `[observed]` Yellow
[observed] Base plates sit at Z=46.0 mm, with secondary dorsal shells 7.2 mm higher.
`[observed]` The front view shows a wide planted stance, dark structure below
yellow armor, separated left/right leg layers, circular root collars, and twin
aft dorsal spines. `[observed]` No frontal weapon mass is permitted.

## 4. Side view — elevation along +X

No aligned orthographic side view is supplied; the side read is reconstructed
from the two V4 isometrics and source. `[inferred]` The body is low and long,
with three armor zones above a 16.0 mm-high chassis. `[observed]` The upper leg
vector is +32.0/-7.0 mm and the lower vector is +18.0/-25.0 mm. `[observed]`
[observed] The 24.0 mm foot ends in a safely blunt wedge rather than a needle point.
`[observed]` Overhang risk is governed by each part's preserved print pose and
the 45° deterministic gate. `[assumed]`

### 4b. Visible components

The object visibly comprises one charcoal chassis; three faceted yellow base
plates; three raised dorsal shells; two aft dorsal blades; six dark hip yokes;
six dark upper beams; six yellow upper armor plates; six dark lower beams; six
yellow slotted lower armor plates; six pale crescent conduits; six black wedge
feet; and twelve dark-steel locking pin heads. `[observed]` Wrong counts break
the engineered repetition; missing dorsal shells flatten the layered armor;
missing conduits remove the reference's curved counterpoint; and any crown-like
central mass breaks the explicit unarmed silhouette.

## 5. Size and scale

The scale anchor is the authoritative staged source, not pixel measurement.
`[observed]` Source-built envelope: 242.0 × 147.611 × 77.7 mm with tolerance
±0.10 mm. `[observed]` Unique-part build volume: 180 × 180 × 180 mm.
`[assumed]` Nozzle: 0.4 mm. `[assumed]` Minimum structural wall gate: 0.8 mm.
`[assumed]` Preferred visible relief: at least 1.2 mm. `[assumed]`

The assembled review model intentionally exceeds the bed in X. `[observed]`
Only individual unique parts are print targets; no one-plate full-kit claim is
made. Physical print success, insertion force, retention, durability, and
printer compensation remain unverified.

## 6. Decomposition and selected design

The selected exterior construction is the staged V4 Tier-3 build123d project:
15 unique printable roles and 61 labelled assembled occurrences. `[observed]`
The nearest rejected alternative is a fused single-piece spiderbot, which
would exceed the bed, erase the yellow-over-charcoal part hierarchy, and remove
the keyed assembly experience.

The selected mechanical design is a rigid keyed tenon/mortise kit reinforced
by printed locking pins. `[observed]` The nearest rejected alternative is free
ball-joint articulation, absent from the source and incompatible with the
fixed-pose Wish. Electrical topology, lighting, and bought devices are N/A.
The custom printed pins are preserved source geometry, not purchased hardware.

Printed roles: `chassis_core`, `carapace_fore`, `carapace_center`,
`carapace_aft`, `dorsal_fore`, `dorsal_center`, `dorsal_aft`, `hip_yoke`,
`upper_leg_beam`, `upper_leg_armor`, `lower_leg_beam`, `lower_leg_armor`,
`energy_conduit`, `foot`, and `joint_lock_pin`. `[observed]`

Interfaces: carapace peg X clearance 0.20 mm/side and Y clearance 0.76 mm/side; `[observed]`
Hip key 0.25–0.275 mm/side; hip-to-upper and upper-to-lower tenons 0.25 mm/side; `[observed]`
Dorsal key 0.25 mm/side; foot receiver 0.25 mm/side in Y/Z with an exact 5.5 mm `[observed]`
depth stop; and pin radial clearance 0.20 mm/side. `[observed]`

No catalog or design-reference source substitutes for the authoritative V4.
Legacy cannon, muzzle, hub-pedestal, and sensor modules were deliberately not
copied into this product because they are unused by the canonical assembly and
contradict the Wish. `[observed]`

## 7. Per-feature build operations and verification

- Chassis: `clipped_prism` extrusion, additive lugs/collars/tongues, then
  subtractive root and armor sockets; centered XY local frame; risk is socket
  wall/overhang margin.
- Base armor: faceted `Polygon` plan extrusions, subtractive panel slots, then
  additive chassis pegs and dorsal key; risk is preserving dark inter-plate gaps.
- Dorsal armor: `yz_prism` profile intersected by a faceted plan mask, with a
  downward-open socket; aft blades are additive prismatic features; risk is
  blade handling and square-key orientation.
- Leg beams: `xz_prism` structural profiles with cylindrical collar language,
  keyed box tenons/mortises, armor slots, and transverse pin bores; risk is
  actual paired-face clearance.
- Leg armor: beveled `xz_prism` shells with subtractive slots and paired pegs;
  [observed] Risk is losing the 1.0 mm visual stand-off.
- Conduit: annular `Circle` difference clipped by a polygonal wedge and
  [observed] Extruded 3.0 mm; risk is confusing the pale loop with a claw.
- Foot: intersection of side and plan prisms plus heel, subtracting the keyed
  receiver; risk is the exact-depth stop and pointed silhouette.
- Lock pin: cylinder shaft, conical transition, round head, and subtractive
  six-sided recess; risk is upright head overhang and recess openness.
- Assembly: `AssemblyHelper` placements only, with direct sRGB `Color` on every
  leaf occurrence; risk is stale or forbidden legacy occurrences.

Proportion assertions: assembled L:W:H is 242.0:147.611:77.7 mm ±0.10 mm; `[observed]`
there are 61 occurrences, six complete legs, three base plates, three dorsal
shells, six conduits, six feet, and twelve pins; forbidden role count is zero.
`[observed]` Likeness references are `custom=ref/ref-02-reference-angle-v4.png`,
`iso=ref/ref-03-iso-v4.png`, and `front=ref/ref-04-front-v4.png`, each at a
0.90 delivery floor. `[assumed]` The photograph is qualitative because its
background prevents a trustworthy deterministic silhouette extraction.
