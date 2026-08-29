# Lantern Menagerie CAD brief

- Model: four-part hand-powered cast-shadow theatre assembly.
- Task type: new parametric STEP-first assembly from the sealed Invent contract.
- Units: millimetres.
- Coordinate convention: part entries print broad-face-down in XY with +Z
  thickness. The assembly uses X left/right, Y gate vertical, Z light axis with
  phone behind +Z and wall ahead -Z, then rotates upright for the exported view.
- Printed parts: front shell, rear shell, open-carrier shadow reel, kickstand.
- Overall target: at most 114 mm wide, at most 130 mm high, under 13 mm folded
  body depth; deployed rear footprint about 82 mm.
- Optical geometry: paired 44 mm portals centred 31 mm above the reel axis;
  rabbit/fox/owl positive opaque profiles at 0/120/240 degrees; 114 x 3.2 mm
  reel; 3.2 mm minimum silhouette ties; full 360-degree sweep.
- Functional interfaces: 7.8 mm reel bore owns a 7.2 mm spindle derived with
  `cadfits`; 0.3 mm axial gaps; four large shell hooks with derived receiver
  slots, a one-sided 0.6 mm flex/retention shoulder, and 0.4 mm leading-face
  clearance on each axis; rabbit home releases 0.25 mm more nominal leaf travel
  than fox/owl through a chamfered nose and symmetric conical pocket ramps; 6 mm
  stand trunnions are captured at the rear and carry paired deployed-stop tabs.
- Manufacturing assumptions: FFF, 0.4 mm nozzle, 0.2 mm layers, common rigid
  filament, flat support-conscious part stances, 220 x 220 x 220 mm bed.
- Assembly: place reel and kickstand between shells and engage the four
  one-time shell locks. Snap compliance, detent force, printed fit, and cycle
  life remain physically unverified.
- Validation targets: four printable solids; assembly bounds; STEP validity;
  no hard-part interference at rabbit home/deployed stand; reel and stand
  clearance sweeps plus shell pullout and two endpoint stops; exact key-state
  projections, all four distance-band corners, bounded yaw/pitch views, and a
  5-degree full-cycle contact sheet; mesh, bed, standard/fine 0.4 mm thickness
  gates; RGB 1024 px render.
- Sealed-contract reconciliation: the Invent text's 114 mm reel and 48 mm axle
  height would put the reel below a tabletop. Make keeps the 114 mm reel and
  moves the axle 58 mm above the table within a shorter 119 mm architectural
  frame. The non-obstructing aiming cue is implemented as rim ticks and the two
  portal-edge bites, because solid 18/8 mm concentric rings inside a through
  portal would block the promised light path.

Round-3 reset cue placement: the through-cut fixed arrow occupies the shell's
right midline, entirely outside the detent leaf and optical portal, and points
to the reel's only double-V at rabbit home.

Round-3 Playtest repair: the fox restores a pointed polygonal muzzle, low
triangular ears, and angular brush; the owl uses a strongly horned head,
exterior-open wing notches, separated feet, and a broad perch without facial
holes. All three states receive the full five-case alignment challenge. A deep
front home arrow and a six-tile raised rear beam arrow make reset and phone
side visible and tactile.
The detent uses a 0.95 mm-radius nose tip and symmetric 0.70 x 0.18 mm pocket
ramps; each shell lock is a +X-only cantilever shoulder with an exact
maximum-compression closure proxy. The stand is 112 degrees and targets the
sealed approximately-82 mm deployed depth. Compliant-envelope and nominal-fit
evidence remains digital and does not prove printed force or cycle life.
