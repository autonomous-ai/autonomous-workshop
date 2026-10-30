---
title: Infinity cubes — fold states and decorating every face
tags: [infinity-cube, fidget, fold, print-in-place, hinge, inlay, multi-colour, state-graph]
aliases: [infinity fidget cube, infinite cube, folding cube, fidget cube fold, yoshimoto-style cube, eight cube loop, cube skins, fold state art, pattern joins when folded]
sources:
  - https://github.com/jhpieper/sturdy-infinity-cube (openscad/sturdy-infinity-cube.scad, MIT: size 20, spacing 1, cut 2, link pivots 4 mm from the face and the joint)
  - "experience: a kinematic model of that cube's eight hinges, every hinge open or folded, enumerated for loop closure and overlap"
  - "experience: three themed skins built on it; a build review found the seam band, the line width and the flat-joined seams"
related: [mechanical-puzzles, print-in-place-mechanisms, hinges-and-pin-joints, fdm-multi-material-design, play-value-and-tactile-feel, mechanism-verification]
updated: 2026-10-27
---

# Infinity cubes — fold states and decorating every face

An infinity cube is eight sub-cubes on eight hinges closed into one loop, so it
has no free end and folds over and over. It is printed flat as a 2 x 4 slab with
every hinge open. Getting the mechanism right is the base's job. This page is
about what to know before **decorating** one: which faces show in which state,
where art can go, and which seams join only when the cube is folded.

## Model the states before drawing anything

Treat each hinge as either open (as printed) or folded 180°. With a double-pivot
link whose pivots sit 4 mm in from the face and the joint, a fold keeps the 1 mm
gap. The fold transform is a 180° rotation about a line parallel to the joint,
at the middle of the gap and **half a gap beyond the face plane on the link's
side**. Compose these transforms around the loop. A state is valid when the loop
closes (the last hinge's transform agrees with the chain) and no two sub-cubes
overlap. On the Sturdy cube, enumerating all 2^8 open/folded patterns gives two
2 x 4 slabs, two 4 x 2 x 1 sticks, two 41 mm cubes and a few half-folded states.

The play cycle is six moves, each one coaxial hinge group:

```text
flat -> stick A (top hinges) -> cube A (side hinges) -> slab B (bottom hinges)
     -> stick B (side hinges) -> cube B (top hinges) -> flat (bottom hinges)
```

Sweep every move for collisions: links turned half the fold about each pivot,
pairwise booleans at about nine samples. Also check that each hinge bent the
wrong way collides, and that a link pulled out of its pocket hits a pin. A
reachable pose with no clash is what the art is drawn on.

## The two cube states partition the faces

Each cube state shows 24 of the 48 faces, and **the two cube states show
disjoint sets**. On the Sturdy cube, cube A shows the eight bed faces and 16
sides, and cube B shows the eight print-top faces and the other 16 sides. Two
"skins" therefore decorate every face exactly once. Assert the partition in
source, because a hinge topology that differs breaks it.

- **The hero face is the link-free face.** In each state some big faces carry
  hinge links in their seams. Enumerate them: on the Sturdy cube, only cube B's
  top (the print tops of the four middle sub-cubes) and one side of cube A are
  link-free. The focal art goes there.
- **The hero is also whole in the flat print** when its four tiles keep their
  relative pose through the folds (they do for cube B's top). Art that should
  join *only* when folded cannot live there.

## Where art can go: the seam band

The concept images draw a hairline between tiles. The cube has a band of
**gap + 2 x edge cut + 2 x margin**: 1 + 2 x 2 + 2 x 0.3 = 5.6 mm on the Sturdy
cube. That band runs as a cross through the centre of every big face, and the
art keeps only about 56 % of the face. Anything centred on a big face (a sun
disc, a ring, a chip) loses the cross. Lay out the hero so that a seam falls
where the motif has no feature: on a face, the vertical seam where the nose is
and the horizontal seam between the eyes and the mouth. A centred disc reads as one shape only when about half of it clears the cross
(a sun of radius 13 mm keeps 51 %; at 10 mm it kept 40 % and read as four
fragments in each tile's inner corner). A ring about the centre
must sit at a radius where enough of it clears the band: at r = 7.4 about half
of it survives, and at r = 4.9 less than a quarter.

Also keep every hinge pocket footprint, grown by the hinge keep-out band, bare.
The pocket opens through the joint faces as well as the link's own face, so take
the footprint from the pocket solid sliced at each face, not from the link alone.

## Draw in the fold, map back to the print

Draw the art in 2D on each big face of the state where it must join, in that
face's (u, v) frame. Each tile is one sub-cube face. Take the tile's pose in the
state, invert it, and place the face's plane in the sub-cube's print frame.
Clip the art to the tile's flat, minus the keep-outs, and extrude it inward as a
square-cut colour solid. Then subtract it from its host, so the fused print is
the undecorated cube exactly. Verify by posing each colour solid back into its
state: its outer face must land on the big face with the art region's area and
centroid.

**"Joins only when folded" needs the seams the flat print does not already
join.** A seam between two sub-cubes whose relative pose in the state equals
their pose as printed joins in the flat slab too. Their hinge is open in both,
or they are both in a rigid block. On the Sturdy cube that is the bottom-hinge
pairs in cube A, and the side, top and middle-block pairs in cube B. Let art
cross only the other seams, and count the crossings per face in an audit. Links
can block the only qualifying seam. Cube B's left and right faces leave two
grid lines for crossings.

**Count the crossings on the finished inlay, not on the drawing.** Every later
step can delete half a crossing without touching the drawing: trimming a trace
end for its pad, skipping a pad that does not fit, dropping a speck, cutting one
colour back from another. One router drew 49 crossings, and 19 survived on
both tiles. Probe a point just inside each tile's flat on both sides of every
crossing in the resolved regions, and assert the count. Start a crossing a full
grid step back from the seam, never end a trace on the far edge of a seam, and
keep crossings in a colour that nothing is cut back from.

The same goes for a radial motif drawn from a hub: a spoke shorter than the
speck limit is deleted, so draw each spoke as one line from inside the hub into
its trace, and assert the spokes on the finished regions.

A rigid-body motion gate can still prove part of the cycle. The two moves that
start from the print pose (the top hinges to the stick, the bottom hinges to
the cube B fold) are rotations about one fixed axis direction for every moving
body: write each body's pose as an angle table about that direction plus a
translation table, from the kinematic model. Add each hinge folded alone, the
same hinge bent the wrong way (expect blocked) and each link pulled out of its
pocket (expect blocked). The other four moves start from a folded state. They
need the local sweep.

## A circuit skin needs routing rules, not a random walk

Traces grown by a random walk on a grid read as disorder. Ends land wherever
the walk stops, pads are dropped where they do not fit, and walks start beside
each other, so nodes come apart from their traces, traces end in the air and
pads bunch. What makes PCB art read as a circuit (routing guides, published
circuit prints, stock circuit patterns):

- traces only at 0°, 45° and 90°, in parallel buses at one pitch, each bus
  drawn as the mitred offset of one centreline so the pitch survives every jog;
- every trace has two ends, each on a chip, a connector or a ring pad; a bus
  that cannot reach a second chip fans out 45° into two pads;
- chips anchor the layout (one per tile at its most open spot); hinge-link
  outlines double as connectors that traces leave like pins;
- pads only at trace ends, a minimum centre pitch apart, everything a clear
  gap from what it does not join.

Audit all of it on the vector layout (angles, ends, lone pads, pad pitch and
clusters). Audit continuity and whole pads on the finished regions too. Measure
crossing room geometrically (a straight lane clear of the link outlines), so a
face that cannot carry a crossing is reported rather than excused.

## Colour on the sides costs a change on every layer

Thirty-two of the 48 faces are vertical in the print, so any colour on them is a
colour change on every layer they span: about 84 of 100 layers at 0.2 mm on a
20 mm sub-cube. Each colour used there adds about that many changes. Keep extra
colours (vias, a second trace net, a pad colour) on the 16 faces printed flat,
where they cost six layers. A 0.6 mm line on a side is one extrusion line per
layer; use two lines (0.8 mm at a 0.4 mm nozzle).

## Checks

- Enumerate the valid states and the cycle; sweep every move; check wrong-way
  bends and link capture as blocked.
- Assert that the two cube skins partition the 48 faces, and name the link-free
  faces.
- State the seam band and the art-area fraction before approving a concept that
  draws hairline seams.
- Pose every colour solid in its state and compare it with the art; render
  that state.
- Count the seam crossings that join only in the fold, per face.
