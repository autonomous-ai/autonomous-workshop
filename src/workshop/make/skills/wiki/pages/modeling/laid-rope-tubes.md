---
title: Laid rope tubes
tags: [rope, cord, twisted, lay, tube, bspline, step, sweep, print]
aliases: [laid rope, twisted rope, three-strand cord, rope model, cord model, rope coil, twisted cord, rope lay, braided look, rope around an object, paws that hold a rod, fist bore, figure on a rope, charm on a strand]
sources:
  - "toolchain: OCP 7.9 Geom_BSplineSurface from a sampled control net, Segment per piece, BRepBuilderAPI_Sewing; STEPControl_Writer sizes compared stage by stage"
  - "experience: a laid three-strand cord as B-spline tubes (two closed coils fused with a seat band, cut by a seat frustum and a bed plane; an open strand cut flat to print lying down)"
  - "experience: a figurine whose two paws clip onto a printed rope and turn on it"
related: [sweeps-and-helices, nurbs-bspline-basics, boolean-pitfalls, occt-topology-and-tolerance, wall-thickness-and-hollowing, overhangs-and-print-orientation, carved-figures-on-split-prints, snap-fit-design]
updated: 2026-10-10
---

# Laid rope tubes

A three-strand cord reads as rope from its lay, and the lay is also what makes
it expensive: every exact cut that crosses a lobe writes a curve of thousands
of poles. Model the lay where it shows and nowhere else.

## A lobed tube from a control net

The section radius is
`r + a cos(k (theta - 2 pi t / lay))`, k lobes turning one full turn per lay
length along the arc length t. Do not sweep a lobed profile; sample the
section round the centre line and use the samples as the control net of one
B-spline surface (periodic round the section, and along a closed loop too).
On a closed loop round the lay count to a whole number so the strands meet
themselves.

- **Split the periodic surface into self-contained pieces.** One periodic face
  round a closed loop broke booleans (a cut came back larger than its target),
  and `ShapeUpgrade_ShapeDivideClosed` fixed that only by writing a STEP
  many times larger. Build the surface once, then make each piece a fresh
  `Geom_BSplineSurface` trimmed with `Segment` (a few pieces along the loop,
  two round the section) and sew the pieces: booleans work and the file stays
  small.

## Plain where it is cut

- **Make the lay vanish where an exact cut, a fused band or a print flat
  meets the rope.** A plane or a frustum cutting a laid lobe meets it along a
  wavy curve, and OCC approximates every such intersection edge with
  thousands of poles (2D and 3D): one seat cut, one filler band and one bed
  flat on two coils tripled the part's STEP, and a print flat cut across the
  lobes of a lying strand left a thin wedge at its edge at every lobe, which
  pushed the wall gate's taper count over budget. Those sides are hidden
  (against the host, on the bed), so fade the lay amplitude to zero over
  them with a smoothstep in the section angle, keeping the lay on the sides
  that show. A cut then meets a plain circle along a smooth curve.
- **Stand the plain side a little proud of the cut.** A plain side exactly at
  `r` on a seat offset by `r` meets the seat tangentially (a near-coincident
  boolean). Bulge it by about 0.1 mm so the seat cuts a narrow flat at an
  angle.
- **A print flat's depth sets the overhang.** A tube lying on a flat cut `d`
  below its axis has its surface normal `acos(d / r)` off straight down at the
  flat's edge; keep that above 45 deg, plus the lobe flank's slope if the lay
  reaches the edge.
- **Reducing the curves afterwards is not a fix.**
  `ShapeCustom.BSplineRestriction` halved such a file but returned a shape
  `BRepCheck_Analyzer` called invalid.

## Hanging a figure on the strand

A figure that hangs on a strand and turns about it (a gravity lever on a
button, a climber on a rope) needs one straight bore along the strand's line,
and that bore is an exact cut on a smooth skin.

- **Hold the strand in one fist per paw, flat-ended.** Make each fist a
  rounded cylinder on the strand's axis with flat ends square to it and an
  edge round smaller than the wall beside the bore, so the bore leaves each
  fist through a flat face. A single bar along both paws, or two blended
  fists, leaves a saddle between them that the bore cuts nearly tangent,
  folding the patches there. Let the strand show between the fists, and blend
  each fist into its forearm with a wide smooth union so it reads as a wrist,
  not a block.
- **Anything that rests on a fist's end uses that end's shape.** A stopper
  knot placed from an ellipsoidal fist's half-length at the bore radius sits
  inside the flat end of a cylindrical one. Derive such gaps from the end the
  fist actually has.
- **Clip on from the hidden side.** A slot from the bore to the face the
  figure hangs against, a little narrower than the strand, lets the paws snap
  on and stay on; size the lips' strain like any snap ([[snap-fit-design]]).

- **Search the line on a height map, then ask the wall gate.** On a relief
  figure built from domed masses, a straight line crosses the creases where
  masses meet, much thinner than either mass (2.7 mm between 6.8 mm domes).
  Rasterise the figure's tessellation to a height map and score candidate
  lines by the surface over the bore; then run the wall gate on the few best,
  because a ring test at bore radius plus two lines is pessimistic (lines it
  rejected for diagonal thinness passed the gate as tapers).
- **A blind bore cannot carry the figure.** The figure's weight needs a
  figure face looking down onto strand material below it: a stopper under its
  lowest bore mouth. A blind bore's floor lies below the strand's tip and looks
  up, so the figure slides off; `check_motion`'s rest condition caught it
  (moving the figure down came back clear).
- **Where the bore leaves a dome, open its top over the last stretch.** The
  skin over a bore thins to nothing as the dome comes down over it; out of a
  foot's sole it failed the wall gate as a 1.1–1.3 mm band. A 30° countersink
  there only widened the band and thinned the foot's sides; a slot as wide as
  the bore, open to the front over the 2.9 mm before the axis leaves the sole,
  left only tapers, and the stopper knot sits against its end.
- **At a narrow entry, open the bore's outer half.** A closed 2.56 mm bore in a
  4.7 mm paw left a 0.13 mm sliver on one side; a 45° countersink and a
  bore-wide groove only moved the sliver. Removing everything outside the
  bore's outer half down to its bottom line (the strand lies in the palm on
  the bore's own floor) passed, its edges tapers. Keep any countersink off a
  face that prints on the bed: through the back it left a feather there.
