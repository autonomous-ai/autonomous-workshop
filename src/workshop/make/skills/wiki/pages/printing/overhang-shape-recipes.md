---
title: Overhang shape recipes
tags: [overhang, orientation, support, teardrop, figure, dome, dimple, opening, fan, cone]
aliases: [support-free figure, overhang recipe, fan on edge, chin overhang, raised relief overhang, flat-topped dome, dome ceiling, tilted socket, spherical dimple, bead dimple, carved opening, lantern face, ball on a cone, free fist, bed-face groove, seam groove]
sources:
  - skills/cad/scripts/check_overhang
  - "experience: support-free figurines: a horse chin, raised chest emblems and stacked arm segments all failed check_overhang"
  - "experience: a flat-topped egg crown and a chamfered rim failed the overhang gate until reshaped as described"
  - "experience: bauble dimples on a revolved tree failed check_overhang with a 50 deg tangent roof and passed at 40 deg"
  - "experience: a pixel cabin's roof halves and seam grooves; a voxel gift box's bed-face grooves"
  - "experience: a jack-o'-lantern shell with a carved face, printed upright on its open rim; a chibi figure with a carried pumpkin and a free fist"
related: [overhangs-and-print-orientation, rounded-bodies-on-the-print-bed, knife-edges-and-tapers, wall-thickness-and-hollowing, carved-figures-on-split-prints, fdm-bridging-and-sacrificial-layers]
updated: 2026-10-10
---

# Overhang shape recipes

Shapes that fail `check_overhang` however carefully their slopes are drawn,
and the reshaping that made each one print without support. The terms (bridge,
ledge, reach) and the general fixes are in [[overhangs-and-print-orientation]];
bed edges are in [[rounded-bodies-on-the-print-bed]]. Keep every recipe's
drawn angle inside the limit with margin
([[overhangs-and-print-orientation#do-not-design-at-the-limit]]).

## A fan standing on its edge

A leaf, fin or feather printed standing in its own plane has an underside that
faces down at 90° less the direction it points: a leaf pointing 30° off the
bed prints its whole lower edge over air. Squeeze a fan's leaves into the band
45° + margin to 135° − margin before anything else.

That is not enough on its own. A leaf widens fastest at its base, so near the
root its lower edge falls away from its axis: a leaf pointing 55° whose widest
point is a third of its length out still has an edge at 30-35° there. Either
bury the base in the host, or run a straight web under the outer leaf from its
widest point down into the host at 52° or steeper (the hull of the leaf up to
its widest and a ball as thick as the leaf, placed so the tangent between them
has that slope). A ball sitting on the host is the same problem at its lower
hemisphere; make it a cone below its equator (the hull of the ball and a point
r / cos β under its centre gives a cone β steep).

Check it on the faces, not on an outline. Subtract the host from the feature
with both marked as originals (manifold3d `as_original`, then the mesh's
`run_original_id`): the faces the host's cut contributes are the feature's
footing, the rest is its surface. Group the downward faces into connected
patches and let a patch under about 1 mm across pass as a ledge — the round
end of a groove is one.

## Low points, leaning reliefs and stacked rounds

Three shapes fail the overhang gate however their slopes are drawn:

- **A low point in mid-air.** A horse's chin over its throat notch is the
  lowest point of the head with air below it: whatever the jaw's angle, the
  first layer of the chin prints on nothing. Printed upright, the underside has
  to run downhill all the way to the body — the jaw at 40° down and back to a
  notch below the chin, the neck leaning forward under it. The notch survives as
  a V; the undercut does not.
- **A raised relief on a surface that leans back as it goes down.** A 0.5 mm
  emblem on a chest narrowing toward the waist read as 1-2 mm of reach:
  the relief's lower edge stands out from a surface that is itself receding
  below it. A flush colour inlay shows the same emblem and hangs nothing.
- **A panel raised on a wall lifts its own lower edge.** Cutting a raised
  panel's down-facing edges back at 50 deg moves the edge, where it meets the
  wall, `proud x 1.19` higher at the panel's face, and a smaller relief drawn
  on the panel near that edge is left standing over air. Set the panel's foot lower or the detail higher.
  And keep a raised panel inside the face that carries it: a collar wider than
  the block under it kept its uncut 35 deg edge face exposed behind the
  block's plane.
- **A part turned after it was drawn tilts its print face.** A foot turned
  out about the vertical and printed on its medial face faces the bed with
  that face, tilted only by the turn. Extrude the turned face along
  the print's down axis to the bed plane and clip there: the foot keeps one
  flat medial face and still points out.
- **A rounded top under a narrower piece.** A forearm whose top is filleted
  into a dome, with a thinner upper arm standing on it, leaves the upper arm's
  rim over the dome's shoulder: a 1.2 mm ring with air under it. Cap the
  rounding at the difference of the two radii.

A hole crossing a part that prints along its own axis is a bridge only if
there is material beside its ceiling at every layer. A chimney hole through a
roof printed standing on its gable end had none, so its ceiling was an 8 mm
cantilever. Split the part at the hole's far face, so the hole becomes a notch
open at the top of the print.

Make seams and decorative grooves that run across the build direction
V-shaped, with half-width at least the depth (0.8 x 0.35 mm). A flat-roofed
groove beside a recess ceiling is clustered into one overhang region, and on
stepped corners it reads as a 1.1 mm reach on the 0.4 mm grid.

A groove **on the bed face** is different: its flanks hang straight off the
bed. A 90 deg V there, or a groove line along a hole's edge (which cuts a 45
deg chamfer), failed `check_overhang`, and on one part it passed once and
failed the next run as the tessellation moved. Either leave a hidden bed face
ungrooved, or narrow the V so its flanks stand at most about 30 deg off
vertical (0.2 mm half-width at 0.35 mm depth). A flat-roofed groove on a bed
face fails with "reach inf", even 0.5 mm wide, where a slicer would bridge it.

When the bed face is the one people see (a skirt plate or a visor printed face
down) and the part already prints in more than one filament, draw the panel
line as a flush inlay of a darker filament instead: at least 0.5 mm wide and
three layers deep, it reads as a line and leaves nothing to bridge
([[fdm-multi-material-design#the-same-art-on-both-faces]]).

## A flat-topped dome: fill the crown, funnel underneath

Printed upright, a dome's inside is its ceiling, and near a flat crown it is
far past 45 deg. A ceiling cone rising inward from the wall cannot fix it: from
any wall point low enough to leave the window or cavity below it clear, a
52 deg cone reaches the outside of a flat crown before it reaches the axis.
Fill the crown instead, and give the fill an underside that rises **outward**:
a funnel from the foot of the central boss (the socket, bore or well that
passes through the crown) up to where the dome's own inside is still steeper
than about 45 deg. Each layer then grows outward by less than its height, and
the boss's mouth needs only a ledge under 1 mm.

## A break on an edge that already leans out hangs flatter

A part printed on an edge whose surface leans outward -- an egg's rim, a bowl's
lip -- already overhangs by that lean. Any chamfer or round across that edge is
flatter than the surface it replaces, so it turns a passing 39 deg surface into
a failing 20-30 deg one. Leave such an edge sharp and put the visible break on
the mating part's edge, which faces up.

## A socket tilted inside an upright print

A tilted socket inside a part printed on its own axis (a leaning hat whose
seat follows a pyramid) changes each ceiling face's overhang. For a face with
unit normal `n` and the socket tilted by `a` about a horizontal axis, check
`n` rotated by `a` against the build direction: the face hangs at
`90 - acos(n_z cos a + |n_h| sin a cos phi)` from vertical, with `phi` the
angle between the face's horizontal normal and the tilt direction. Tilting
toward a pyramid's edge (`phi = 45 deg`) instead of a face roughly halves the
added overhang: a 63 deg pyramid socket fails at 20 deg toward a face and
passes at 25 deg toward an edge, tops out near 28 deg.

## A spherical dimple in an upright print

A bead or ball half-sunk in a side wall needs a teardrop roof over its dimple.
A cone tangent to the sphere at latitude `phi` above the equator leans `phi`
off vertical, not `90 - phi`, so the sphere band between 45 deg and `phi`
still hangs: put the tangent at `phi = 40 deg`, not 50. The bead itself prints
without support cut flat at `d <= R sin 45` below its centre, with its
locating peg lying on the bed.

## Carved openings in an upright shell

A lantern face, a vent or a window cut through a shell that prints upright:

- **Cut along rays from the body's axis.** A cutter extruded parallel to the
  face's centre direction meets the skin 40-50 deg off its normal toward the
  face's edges and leaves wedges thinner than two lines. A cut along the local
  normal, or along rays from the body's axis, keeps that angle within the
  shell's own curvature. Keep opening edges and sloped sills off the flanks of
  creases.
- **Peak every top.** Upright triangles, arches and pointed tops print. A
  flat window top is a bridge, so keep it short.
- **Divide a wide opening.** A wide grin cannot pass both print gates as one
  hole. A lintel flared to rise inward at 50 deg or more leaves a wedge at the
  skin that the thickness gate reads as a wall. A level step at the skin is an
  overhang. Teeth spanning the mouth turn each window top into a bridge of
  about 4 mm or less, and corners that climb at 60 deg or more need no bridge.
- **A hollow squat shell has no printable roof.** The inside of a pumpkin or a
  dome turns flat at its crown. Split it where the wall leans out to the print
  limit, and let a lid printed on its flat underside be the ceiling. The seam
  can read as a carved lid line.

## Grooves, facets and plates in a part printed upright or on its side

- **A V groove across a side-printed part is a ceiling unless it is wide.**
  Its flanks lie nearly flat in the print. Make the V's half-width at least
  1.2 × its depth, so each flank stands 50° off horizontal.
- **A groove cut into a facet reads deeper than it is.** On a face angled 15°
  in plan, a 0.6 mm groove's ceiling read as standing out 1.1 mm; keep grooves
  on angled facets to 0.4 mm.
- **Where a groove would cross a ridge, set the band back instead.** A band
  set back by the groove's depth leaves a step up, which needs no support.
- **A raised plate's lower edge is lifted by its underside.** Printed upright,
  a plate's underside rises 1.2 per mm out (50°), so the visible lower edge
  sits 1.2 × proud above the edge drawn at the face. Where the plate's
  proudness varies, as on a ridged breastplate, draw the edge so the lifted
  edge has the wanted shape: for a front V of angle θ over facets falling back
  at θ, draw it at (1 + 1.2) × tan θ.
- **A panel line round a surface that slopes in leaves a sliver** where the
  slope crosses the groove's depth. Run panel lines only across walls.
  A square groove along a dome's sloping shoulder is the same defect: its
  downhill wall thins to nothing where the slope meets the groove's floor.
  The thickness gate once passed such a line, then read it as a 0.2 mm wall
  after a detail elsewhere moved the part's bounding box by 0.5 mm, and with
  it the gate's grid. A pass does not clear the line. Move it onto the flat
  top beside the slope, or onto a wall.

## A ball carried on a cone

A small ball standing off a printed body (a fist, a carried lantern, a pom)
needs material under it. A cone from the body to the ball's centre leaves the
ball's underside hanging. Make the cone tangent to the ball, seen from the
cone's apex. For a sphere of radius `r` whose centre is `d` from the apex, the
half-angle is `asin(r / d)`. Keep the cone 10 deg inside the overhang limit,
because a patch skin ripples a few degrees. A fist hanging free at the side
prints when it is drawn into a teardrop that runs down to a point on the
thigh. End the glove colour at the fist, so the teardrop reads as part of the
leg.

## A glued saddle on a rounded rim: keep the outer crown cylindrical

For an adhesive saddle on a rounded rim, the inner mating face may need a
toroidal offset while the outside remains a cylindrical crown. Giving both
faces concentric toroidal curvature can make the front edge a narrow print
foot and leave the following slices hanging over air, even when the post
lies flat on the bed. Extending the outer crown to the front print datum
supports those slices without changing the glue gap. Describe the wall
parameter as the minimum crown thickness, since the forward region becomes
thicker, then repeat interference, overhang and wall checks. The outer
appearance and material volume change; the adhesive interface does not.
