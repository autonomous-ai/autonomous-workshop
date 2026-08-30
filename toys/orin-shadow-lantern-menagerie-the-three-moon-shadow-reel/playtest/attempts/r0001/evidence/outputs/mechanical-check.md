# Mechanical check — reset, closure, motion, and containment

Binding: Made product artifact
`3c7abf41a4aed6005216e14ad42c5c027e7560ff8cd887f3c991917141d1f7cd`;
assembled STEP SHA-256 `f58a818f...`; CAD source SHA-256 `66a0fd56...`.
The fit and motion checks were replayed from a work-area copy, leaving sealed
Made bytes unchanged.

## Passing digital evidence

- The fit audit passed: 0.30 mm spindle radial clearance; 0.30 mm front and
  rear reel gaps; 0.40 mm hook-stem/slot clearance on each audited axis; 0.35
  mm stand-socket radial clearance; and 5.90 mm hinge setback.
- The kickstand cleared both shells and reel over 29 deployed-to-folded samples.
- The reel cleared the rear shell and deployed stand over 73 samples spanning
  360 degrees. The manifest explicitly excludes intended compliant detent
  contact and does not include the front shell as a reel obstacle.
- The accepted assembly evidence reports four named occurrences and no
  final-pose clash above the 1 mm3 tolerance.

## Reproducible implementation failures

1. The reset rim is defined by `56.6 + 0.4*cos(12*angle)`, so it repeats exactly
   every 30 degrees. No asymmetric double-V home geometry exists.
2. The unflexed nose spans world Z 2.40–3.05 mm. Fox/owl pocket floors are at
   Z 3.30 mm and rabbit at Z 3.55 mm. The nose therefore fully relaxes in every
   pocket; the 0.60/0.85 mm depth difference cannot create differential leaf
   travel or a uniquely deeper rabbit click. Nose and pocket radii are both
   1.5 mm, leaving zero nominal lateral entry clearance.
3. Each shell barb is an unchamfered 4.2 x 6.0 mm `Box`, while its slot is only
   3.6 x 5.4 mm. The 0.6 mm interference on both axes has no modeled cam ramp,
   contradicting the sealed chamfered-hook/45-degree-ramp requirement. The fit
   audit measures the 3.2 x 5.0 mm stem against the slot, not barb insertion.
   A clear final assembly pose does not establish that the sharp larger barb
   can traverse the smaller receiver.
4. Clear stand travel does not establish a load-bearing deployed stop, folded
   retention, over-travel resistance, center-of-mass/tipping margin, friction,
   or contact safety.

## Result

**FAIL — implementation improvement in Make.** Add a genuinely asymmetric
visible home mark; give detent entry radial clearance and choose protrusion and
pocket floors that preserve measurable fox/owl deflection while rabbit releases
about 0.25 mm farther. Add broad printable cam ramps/chamfers to the shell
closure and audit insertion plus retained state. Extend deterministic evidence
for detent engagement and stand endpoints.

No digital result proves snap strain, retention force, detent feel, tipping,
pinch safety, printed compliance, strength, or cycle life; these remain
physical Playtest items after the geometry is repaired.
