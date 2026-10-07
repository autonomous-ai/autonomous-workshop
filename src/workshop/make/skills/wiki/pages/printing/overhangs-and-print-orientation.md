---
title: Overhangs and print orientation
tags: [overhang, orientation, bridge, ledge, support, teardrop, chamfer, build-direction, fdm]
aliases: [print pose, which way up, unsupported, droop, sag, 45 degree rule, support material]
sources:
  - "experience: support-free figurines: a horse chin, raised chest emblems and stacked arm segments all failed check_overhang"
  - skills/cad/scripts/check_overhang
  - "experience: parts that were sound, watertight and thick enough but could not print unsupported"
  - "toolchain: tessellated 45 degree cones land facets at 44.7 degrees (reproducible)"
  - "experience: a flat-topped egg crown, bayonet grooves in a rim band and a chamfered rim all failed the overhang gate until reshaped as described"
  - "experience: a wedge base with a stop rail and sunk pads on 60 and 30 deg faces failed overhang until the walls leaned and the underside pad moved outside the body"
  - "experience: lever pockets beside a pushrod in a carved figure's split halves joined the socket's and channel's ceilings into one over-long bridge"
related: [wall-thickness-and-hollowing, joints, printed-part-count]
updated: 2026-09-30
---

# Overhangs and print orientation

Soundness, bed fit, mesh closure and wall thickness are all blind to the build
direction: a part whose every feature hangs in mid-air passes them. This page
is the design side — what an overhang is, which shapes cause one, and the fixes
in the order worth trying. The gate is `check_overhang` (usage in
`skills/cad/references/print-optimisation.md`).

## Bridge, ledge, overhang

A down-facing region is one of three things, and area cannot tell them apart —
a horizontal bore and a shelf of the same area and slope have completely
different answers:

- **bridge** — short enough to span, with material on both sides of it at its
  own level. A bore ceiling, a slot roof. Prints.
- **ledge** — standing less than about 1 mm out from the material beside it. A
  rim, a step, the flat under a small boss. Prints.
- **overhang** — neither. The slicer droops it or asks for support.

Two numbers decide it. **Span** is the **shorter** plan dimension, because that
is the one the slicer has to cross — a 10 × 40 mm roof is bridged across the 10.
**Reach** is how far the region stands out from anything at its own level: half
the span for a bore ceiling, the whole protrusion for a shelf.

## The cap on a stem

A part held up in its middle — a disc on a peg, an accessory printed key-down —
has material under its centre and nothing under its rim. It looks supported and
is not: the rim is a full-reach overhang. If a printable part's underside is its
mating face and its key points at the bed, that is this shape; flip it.

## The fixes, in the order worth trying

- **Reorient the part.** A part entry owns its print pose; a link that is a
  plate in the assembly becomes a plate on the bed, and its bores turn vertical.
  Most overhangs are a pose problem, not a shape problem.
- **Teardrop a horizontal bore.** A round hole through a vertical wall has a
  ceiling the slicer must bridge, and above a few millimetres it sags into the
  bore. Replacing the top with two 45° faces meeting at an apex gives every
  layer material below it. The bore stays round where a shaft touches it
  ([[joints#revolute-joints]]).
- **Put material under the feature.** A pin whose base overhangs the disc it
  stands on has nothing to print onto; widen the disc, or add a boss under the
  pin. Invisible to every other gate and common in cranks and webs.
- **Taper it.** A cone under a collar, a 45° buttress under a shelf.
- **Chamfer, don't fillet, at the bed.** A bed-side fillet is itself an
  overhang; a chamfer is not — unless it is exactly 45°: tessellated, some of
  its facets measure just under the limit and the gate fails them. Make a bed
  chamfer steeper than it is wide (0.6 across by 0.9 up is 56°).
- **Roof a slot that crosses the bed face.** A plate or pin seated in a groove
  across a split print's bed face leaves each half a recess whose ceiling is
  parallel to the bed, and where the plate leaves the part that ceiling hangs
  from one side only. Roof it: a draft of the groove's outline rising at 50°
  from its edges ([[carved-figures-on-split-prints#a-plate-across-the-split]]).

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
- **A rounded top under a narrower piece.** A forearm whose top is filleted
  into a dome, with a thinner upper arm standing on it, leaves the upper arm's
  rim over the dome's shoulder: a 1.2 mm ring with air under it. Cap the
  rounding at the difference of the two radii.

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

## A slot's roof reaches to its far wall

Reach is measured to the nearest point with material under it at its own
level. For a groove cut outward from a bore -- a bayonet groove, a keyway -- that
is the groove's far wall, so a level strip at the mouth counts the groove's
whole depth, not its own width, and the gate's voxel grid can put identical
grooves either side of 1 mm. Keep such a roof under 1 mm deep, or slope all of
it: falling toward the far wall at 52 deg (rising toward the mouth), which
leaves nothing level and meets the bore at an obtuse corner.

## A break on an edge that already leans out hangs flatter

A part printed on an edge whose surface leans outward -- an egg's rim, a bowl's
lip -- already overhangs by that lean. Any chamfer or round across that edge is
flatter than the surface it replaces, so it turns a passing 39 deg surface into
a failing 20-30 deg one. Leave such an edge sharp and put the visible break on
the mating part's edge, which faces up.

## Pockets inside a split print: one ceiling, one bridge

A part printed on its split face carries every internal pocket as a recess
with a flat ceiling -- a socket, a rod channel, the room a lever swings in --
and the slicer bridges each ceiling across its shorter plan dimension, between
walls. Where several pockets meet, their ceilings join into one bridge area,
and one bridge direction then has to serve all of it: a tall narrow pocket
(bridged across its width) opening into a long low strip (bridged across its
height) leaves one of them spanning its long way or ending in air.
`check_overhang` sees the same thing: it groups ceiling samples in cells of
four voxels (1.6 mm at a 0.4 nozzle) and spans each group by its bounding
box's shorter side, so two ceilings within about two cells of each other in
height and in plan are one region, and a T of two short spans reads as one
long one.

Part them, and give each part walls at both ends of its span:

- **A step of at least two cells** (3.2 mm; use 3.3) in ceiling height, or
  **a gap of at least two cells** in plan (3.4), separates two ceilings. A
  smaller step or gap joins them.
- **Step down, not up.** The shallower pocket is the one whose neighbour must
  be deeper: a ceiling next to a *taller* void has nothing at its own level
  at that edge and hangs there, while a ceiling next to a *lower* one has the
  material above the lower one as its wall. A pocket that is raised beside a
  socket to part their bridges leaves the socket's ceiling hanging along that
  side; the gate may still call it a bridge if its flank probe happens to hit
  material, so reason it out rather than trusting one half that passed.
- **Keep what must pass the centre thin and low.** A lever reaching a
  pushrod in the middle of the part turns in a long pocket, and the socket and
  rod channel there are tall: make the lever a flat plate on its inner face
  where it enters the centre, under a ceiling a step lower than both, and
  thicken it only where its pocket stands two cells clear of them
  ([[automata-patterns#pattern-legs-that-swing-with-the-wings]]).

## Features on a tilted face, and layers on the bed face

A stop rail or a sunk pad on a face inclined `t` from the horizontal has a
down-slope wall whose normal points `t` below the horizontal. Past `t = 45 deg`
that wall is an overhang: on a 60 deg face a square-walled 3 mm rail and a
0.8 mm pocket both failed. Lean the wall out of the face by at least `t - 45 deg`
(30 deg gives margin): the rail's down-slope wall ramps, the pocket's walls
draft in toward the floor. Only the walls that face down-slope need it; the
wall that retains the load keeps its square face.

End a ramped rail with walls square to its run, not with the slanted outline of
the region it sits in: a ramp cut by a slanted outline leaves a 0.3 mm wedge at
each end that the thickness gate reads as a wall.

A layer sunk into the bed face (an anti-slip pad let into the underside) makes
the recess's ceiling a bridge over air across its whole width, so a 62 mm
triangle failed the 12 mm bridge limit. Put the layer under the flat base
instead and let the body keep its Z=0 datum.

## Do not design at the limit

A cone that flares one millimetre out per millimetre up is a 45° overhang —
exactly the threshold — and the flat facets a tessellator lays on it land at
44.7°, on the wrong side. The same goes for a 45° buttress or a chamfer sized
to the limit. Give the angle somewhere to go: 1.3 mm of rise per mm of flare is
52° and passes at any tessellation tolerance.

## What geometry cannot tell you

Your slicer's support settings, whether the material bridges well, or whether a
46° face will actually droop on your machine. The overhang rule answers the
geometric question only; a test print answers the rest.

Bridge spans, sacrificial layers and support settings: [[fdm-bridging-and-sacrificial-layers]]. Orientation for strength: [[fdm-print-orientation-for-strength]].
