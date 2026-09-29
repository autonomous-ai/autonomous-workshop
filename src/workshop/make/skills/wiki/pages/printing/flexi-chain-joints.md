---
title: Flexi chain joints
tags: [print-in-place, flexi, chain, joint, yaw, articulated, loop]
aliases: [flexi toy joint, crossed loops, interlocking loops, chain link joint, segment joint, flexi joint, yaw range, wiggle range, flexi legs, flexi segment gap, articulated dragon joint, flexi rex joint]
sources:
  - "experience: sections of a published print-in-place flexi toy's segment joints, measured along each axis and normal to the faces"
  - "experience: a flexi chain's legs met their neighbours at full yaw though every joint was clear at rest; separate beads read as stacked discs"
  - https://3dcentral.ca/articulated-3d-prints-how-flexi-toys-work/
related: [print-in-place-mechanisms, fdm-minimum-feature-sizes, fillet-chamfer-pitfalls, loft-organic-bodies, mechanism-verification]
updated: 2026-09-28
---

# Flexi chain joints: two crossed loops


A segmented flexi toy can join each pair of segments with two closed loops
threaded through each other at right angles, one grown from each segment,
on the body's centre line in the lower half of its height. The toy prints
lying on its belly. Name the front segment F, the rear R; Y runs along the
body and Z is up.

| element | grows from | shape | how it prints |
|---|---|---|---|
| **tongue** | F, at the bed | a bar running rearward from F's lower front face | first layers; its tip lies in a round notch in R's front face |
| **post** | the tongue's tip | a vertical column | vertical walls; takes `xy` to the ring round it |
| **arch** | the post's top | a bar returning forward into F, above the ring | the top of F's loop hole is round or pointed and only a few mm long, so it is a short bridge or an overhang |
| **ring** | R, at mid height | a flat eye round the post; its front bar crosses under the arch and over the tongue | the front bar's section is a teardrop pointed **down**, so its underside is a ≤ 45° overhang printed over the tongue across a `z` gap |

Tongue, post and arch close F's loop in the Y–Z plane; R's ring is closed in
the X–Y plane; each passes through the other's hole. Nothing can pull out
without breaking a loop, and there is no pin head to print or snap off.

- **Motion.** Yawing about the post is the wiggle. The loop clearances also
  let the segment pitch about the ring's front bar and roll a little. The
  **segments' facing end faces** stop all three, not the loops: the yaw range
  is set where their faces meet ([[#end-faces-for-a-set-yaw-range]]). Give
  those faces a gap as well; they are the largest mating area in the joint.
- **Gaps.** `xy` between post and ring hole; `z` above and below the ring's
  front bar; the tongue in its bed-level notch opened wider than either
  (elephant's foot: [[print-in-place-mechanisms#the-bed-closes-gaps-elephants-foot]]). Where a 45° bed chamfer cannot be cut (a lofted
  belly: [[fillet-chamfer-pitfalls#a-bed-chamfer-on-a-lofted-belly]]), cut every
  face that meets another body on the bed back at the bed and taper it to its
  place over two layers, with the joint's own tools grown and tapered. Slanted teardrop faces are overhangs, not
  bridges. One published flexi toy, sectioned along each axis and normal to
  its faces, leaves about 0.36–0.45 mm round the loops in every direction
  and about 0.25 mm between segment end faces high above the bed. That is
  `print_in_place_gap` "loose" in `xy` and "tight" in `z` at a 0.2 mm layer,
  the band that design ships with.
- **Sizes.** Every loop bar must be printable on its own: its section is at
  least the minimum pin ([[fdm-minimum-feature-sizes#features-pins-and-gaps]]),
  and the post, the one bar of F's loop that stands free between tongue
  and arch, is the thickest of them.
  Scale the loops with the segment, not with the gap: the gap stays at the
  printer's number however large the toy is.
- **Check.** Every joint is a pair of bodies that must separate. Run the
  minimum-distance check per pair
  ([[print-in-place-mechanisms#verify-in-cad-the-minimum-distance-not-no-interference]]), and slice the joint on its
  centre plane (X) and at the ring's height (Z) to see each loop close round
  the other's bar. Then turn R to its full yaw both ways about the post and
  repeat the overlap and distance, and move R 3 mm back, up and down: each of
  those must meet F, or the loops do not hold it.

## End faces for a set yaw range

Draw the end faces from the post, not from the segments' outlines. Make R's
front a round nose centred on the post, radius `post_r + xy + ring_t` (the
ring's front bar is the nose), and F's rear a concave arc on the same centre,
one end-face gap wider. Past the arc each end face is a **ray from the post**:
F keeps what lies within `θF` of straight ahead, R what lies beyond
`θR = θF + yaw + margin`. A ray from the post turns into a ray from the post,
so R turned by up to `yaw` never reaches F, at any height, and the nose slides
in its arc at the same gap all the way. The tongue's and the arch's notches in
R are the hull of the bar turned to `±(yaw + margin)`, grown by `xy`. Every cut
is a vertical prism, so each gap is an `xy` gap.

```python
assert abs(THETA_R - (THETA_F + YAW + MARGIN)) < 1e-9 and THETA_R < 90
assert NOSE_R == POST_R + GAP_XY + RING_T
```

The price is a wedge-shaped gap at each side, about `w · (yaw + margin)` (in
radians) wide at half-width `w`. The first contact comes where the rays meet,
a little past `yaw`, which the bisection check finds.

## Anything that sticks out of a segment swings

A leg, fin or spike on a segment turns with it about both of its posts, and
each neighbour turns about its own. A point at radius `r` from a post moves
`r · sin(yaw)` sideways at full yaw, so a leg whose root sits near a joint
meets the neighbour even though the two are apart at rest. Give a segment that
carries a leg room between its joints for the root's width plus that swing on
each side (lengthen the segment rather than shrinking the yaw), point the leg
out rather than towards a neighbour, and prove it with the yaw check above run
on each segment with everything that grows from it.

## Crescents beside the fans

With a round nose on R, the tongue's and the arch's fans leave two crescents of
nose beside them, and each runs out to nothing at its front: a sliver wall the
thickness gate fails and the slicer drops. Cut each crescent off where it is
thinner than about 1 mm (solve `sqrt(nose^2 - s^2) - fan_half(s) = 1` for the
distance `s` ahead of the post). The thick part still carries the ring over the
tongue as a short bridge.

## One body, cut; not a string of beads

Build the chain's outside as one smooth loft and cut it into segments, its
section pinching to the same size either side of each joint. Separate beads
(one ellipsoid per segment, each trimmed by the joint's faces) leave the
larger bead's flat end face showing as a ring at every joint, and the toy reads
as a stack of discs. Cut from one body, the two faces of a joint are the same
size and only the gap line and the side wedges show.
