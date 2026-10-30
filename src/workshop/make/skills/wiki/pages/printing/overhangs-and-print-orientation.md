---
title: Overhangs and print orientation
tags: [overhang, orientation, bridge, ledge, support, teardrop, chamfer, build-direction, fdm]
aliases: [print pose, which way up, unsupported, droop, sag, 45 degree rule, support material]
sources:
  - "experience: a battery door's flange rebate in a bed face, a drop-in slot over a round hole, a 0.9 mm ledge that read as 1.2"
  - skills/cad/scripts/check_overhang
  - "experience: parts that were sound, watertight and thick enough but could not print unsupported"
  - "toolchain: tessellated 45 degree cones land facets at 44.7 degrees (reproducible)"
  - "experience: bayonet grooves in a rim band failed the overhang gate until their roofs were sloped"
  - "experience: a wedge base with a stop rail and sunk pads on 60 and 30 deg faces failed overhang until the walls leaned and the underside pad moved outside the body"
  - "experience: lever pockets beside a pushrod in a carved figure's split halves joined the socket's and channel's ceilings into one over-long bridge"
  - "experience: curved slot roofs, shallow tunnel roofs and ear bases on a dome failed check_overhang until gabled, sloped and sunk"
  - "experience: a lofted 45 deg flank failed check_overhang between stations; 40 deg passed"
related: [overhang-shape-recipes, rounded-bodies-on-the-print-bed, fdm-bridging-and-sacrificial-layers, wall-thickness-and-hollowing, joints, printed-part-count, layer-anisotropy]
updated: 2026-10-12
---

# Overhangs and print orientation

Soundness, bed fit, mesh closure and wall thickness are all blind to the build
direction: a part whose every feature hangs in mid-air passes them. This page
is the design side — what an overhang is, which shapes cause one, and the fixes
in the order worth trying. The gate is `check_overhang` (usage in
`skills/cad/references/print-optimisation.md`). Recipes for particular shapes
(fans, chins, domes, dimples, carved openings, balls on cones) are in
[[overhang-shape-recipes]]; bed edges in [[rounded-bodies-on-the-print-bed]].

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
- **Taper it.** A cone under a collar, a buttress under a shelf, at 52° or
  steeper, not 45° ([[overhangs-and-print-orientation#do-not-design-at-the-limit]]).
- **Break the bed edge steeply.** A bed-side fillet and a symmetric 45°
  chamfer both fail; the steep chamfer and the teardrop round are in
  [[rounded-bodies-on-the-print-bed#breaking-the-bed-edge]].
- **Roof a slot that crosses the bed face.** A plate or pin seated in a groove
  across a split print's bed face leaves each half a recess whose ceiling is
  parallel to the bed, and where the plate leaves the part that ceiling hangs
  from one side only. Roof it: a draft of the groove's outline rising at 50°
  from its edges ([[carved-figures-on-split-prints#a-plate-across-the-split]]).

## A slot's roof reaches to its far wall

Reach is measured to the nearest point with material under it at its own
level. For a groove cut outward from a bore -- a bayonet groove, a keyway -- that
is the groove's far wall, so a level strip at the mouth counts the groove's
whole depth, not its own width, and the gate's voxel grid can put identical
grooves either side of 1 mm. Keep such a roof under 1 mm deep, or slope all of
it: falling toward the far wall at 52 deg (rising toward the mouth), which
leaves nothing level and meets the bore at an obtuse corner.

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

A door-flange rebate round an opening in the bed face is worse: its ceiling
hangs off the outer wall alone. Lay the flange on the bed face instead.

## A ledge is measured on a grid, and a slot from a hole's top leaves shelves

A voxel gate rounds a ledge's reach to its grid: a 0.9 mm flat ledge read as
1.2 mm at a 0.4 mm grid and failed a 1.0 mm ledge limit. Give a stop or a lip
a sloped underside at the print slope instead of designing a flat ledge near
the limit.

A drop-in slot cut upward from a round hole's top meets the hole on a narrow
chord and leaves a shelf a tenth of a millimetre thick each side. Start the
slot's straight sides at the hole's centre, where they are tangent to it — or,
when the part can go in along the hole's axis, drop the slot and keep the hole
round: its top is a short bridge.

## How the gate spans a region, and features on a dome

`check_overhang` spans a downward region by the shorter side of its bounding
box. A curved strip of slot roof reads as its bbox width. A level tunnel roof
that is shallower radially than it is wide is spanned slot-to-lip with nothing
at either end, and fails. Gable slot roofs, slope sills 50 deg from the slot
wall, keep roofs at least 3.4 mm apart where they reach the slot, and make
corner lips climb at 50 deg or more. A pyramid (an ear) on a sphere-like head
must keep its whole base inside the head, or the base's downward faces fail.
Keep its outward lean plus its side half-angle at 45 deg or less.

## Do not design at the limit

A cone that flares one millimetre out per millimetre up is a 45° overhang —
exactly the threshold — and the flat facets a tessellator lays on it land at
44.7°, on the wrong side. The same goes for a 45° buttress or a chamfer sized
to the limit. Give the angle somewhere to go: 1.3 mm of rise per mm of flare is
52° and passes at any tessellation tolerance.

A smooth loft adds its own overshoot between stations: a lower flank whose
stations were all at exactly 45 deg failed the gate. Build such flanks at about
40 deg from vertical.

The margin has to cover the gate's mesh as well as the drawing. At 0.02 mm
chords, a ruled band only 0.06-0.08 mm wide in plan, meshed with triangles 10-15 mm
long along a gently curved outline, came out up to 25° flatter than drawn: a
40° band read as 55-60° from vertical. Keep any band near the limit wide in plan
(0.2 mm and more), and keep the drawing 15° under the limit.

## What geometry cannot tell you

Your slicer's support settings, whether the material bridges well, or whether a
46° face will actually droop on your machine. The overhang rule answers the
geometric question only; a test print answers the rest.

Bridge spans, sacrificial layers and support settings: [[fdm-bridging-and-sacrificial-layers]]. Orientation for strength: [[layer-anisotropy]].
