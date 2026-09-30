---
title: Overhangs and print orientation
tags: [overhang, orientation, bridge, ledge, support, teardrop, chamfer, build-direction, fdm]
aliases: [print pose, which way up, unsupported, droop, sag, 45 degree rule, support material]
sources:
  - skills/cad/scripts/check_overhang
  - "experience: parts that were sound, watertight and thick enough but could not print unsupported"
  - "toolchain: tessellated 45 degree cones land facets at 44.7 degrees (reproducible)"
related: [wall-thickness-and-hollowing, joints, printed-part-count]
updated: 2026-09-28
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
  overhang; a chamfer is not.

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
