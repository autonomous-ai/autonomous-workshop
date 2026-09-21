# Periastra Meridian CAD — revision C: centred yoke, inlaid board

Miniature English draughts in a removable-roof observatory, where the two sides
are the Sun and the Moon and the roof is the dome that watches them. Five
independently printable designs form 58 physical parts: one base, one domed
roof, thirty-two board inlays, twelve Sun counters and twelve Moon counters. No
hardware or power.

**What revision C changes, and all it changes.**

1. **The yoke arms are centred.** Both arms of the telescope yoke were 4.000 mm
   off centre, because `extrude()` grew the arm face along its own normal and
   the normal follows the polygon's winding order. One arm ended up as a lone
   fin beside the tube and the other carried the telescope by itself. The arms
   are now built once and mirrored, and `measure/check_fit.py` cuts the built
   roof against its own mirror image and fails the build if more than 1 mm3 is
   left over.
2. **The board gets the house tiled-board fit layer.** The 32 dark cells were a
   0.8 mm recess with a 0.3 mm lip — one faint outline, in one colour, on an
   opaque print. They are now blind 22.0 mm pockets 2.0 mm deep, each holding a
   separate 21.5 x 2.0 mm inlay printed in a contrasting filament and finishing
   flush with the board floor.

Nothing else moves. The two counters come out byte-for-byte identical to the
archive and `measure/check_fit.py` asserts both hashes on every run.

`periastra.step.py` is the combined closed assembly; `assembly.py` positions its
live-source children. `part_base.step.py`, `part_roof.step.py`,
`part_inlay.step.py`, `part_sun_counter.step.py` and `part_moon_counter.step.py`
return bed-oriented parts. `periastra_lib.py` holds dimensions and geometry. The
26 structural part keys of the archive — `base`, `roof`, `single_01`..`single_12`,
`forked_01`..`forked_12` — are all still present, and this revision adds
`inlay_01`..`inlay_32`, for 58. `single_*` is the Sun counter and `forked_*` is
the Moon counter.

Base 190 by 190 by 24 mm, board 176 mm with 22 mm cells. The two counters are
frozen: `part_sun_counter.step` hashes
`262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b` and
`part_moon_counter.step` hashes
`588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e`, and
`measure/check_fit.py` asserts both on every run. Print on a 220 by 220 mm or
larger bed, 0.4 mm nozzle. All part bottoms sit at Z=0. Roof backing rests on
integral base ledges at Z=21; nominal lateral clearance 0.8 mm per side. Slide
the loose roof vertically upward 100 mm for the illustrated reveal, then set it
aside to play. The base stops downward roof motion; no upward latch exists.
Store all 24 counters in starting rows beneath it; the roof underside is 10.0 mm
above the board floor and 3.0 mm above a counter's top. The inlays finish flush,
so they take none of that storage void.

## The board

An 8x8 field of 22.0 mm cells, 176 mm across, on a floor at z11. The 32 cells
where file + rank is even carry a blind pocket 22.0 mm across and 2.0 mm deep,
with all four plan corners chamfered 1.0 mm, on 9.0 mm of continuous backing.
Each pocket takes one separate **inlay**: a 21.5 x 21.5 x 2.0 mm tile with the
same 1.0 mm plan corner chamfers, 0.25 mm of clearance per side, gravity-seated
with no retention feature, finishing flush with the board floor. Print the
inlays in a colour that contrasts with the base; they are sealed a night-sky
indigo against the base's pale grey-blue, and that colour difference is what
makes the board read as a chequerboard on an opaque single-colour print.

These numbers come from `references/tiled-board-baseline.md` in the Mara Masque
inventor skill, scaled to this 22 mm square. `GEOMETRY-NOTES.md` section C2
cites every clause relied on and every default deliberately overridden.

The plan corner chamfers are structural, not decorative: without them two
diagonally adjacent pockets meet at a shared vertical edge and the board mesh
comes out non-manifold. With them, each diagonal junction keeps a 1.414 mm
material bridge and the mesh closes. That is measured, not assumed, and so is
the closed manifold mesh itself.

## The roof

A 182.4 mm square backing plate 3 mm thick carries a **150 mm drum** of radius
75.0 and height 11.7 — z24 to z35.7 closed. One rotation-ring seam 2.0 mm wide
along the axis and 1.0 mm deep runs all the way round the drum, centred 4.0 mm
below its top, its upper wall relieved at 50 degrees so it is not an unsupported
ring. An **exact hemisphere** of sphere radius 75.0, centred on the axis at the
drum top, rises from there: base radius 75.0, rise 75.0, apex at z110.7 closed.
At its base the hemisphere's surface is vertical, so it flows continuously into
the drum wall and prints apex-up with a 0 degree base overhang.

One 30.0 mm shutter slit with parallel square-cut walls is cut through dome and
drum on a single meridian in the YZ plane, open from the bottom of the drum, over
the apex, and 30.0 mm of surface arc — 30/75 radian, 22.9 degrees — down the far
side, so the far half of the dome stays unbroken. The slit is kept at its built
absolute size and is not scaled with the dome: the 30 mm width is what gives the
telescope clear air on both sides.

A slender telescope stands in the slit on x = 0, the slit's own mid-plane: a
15.0 mm outer tube, 45.0 mm long, on an axis 35 degrees above horizontal, with an
open 7.0 mm muzzle bore 13.0 mm deep leaving a 4.0 mm tube wall. Its muzzle
stands 13.0 mm clear of the dome surface. It is carried on a yoke of two 4.0 mm
arms, **arm A spanning x = -9.000 to -5.000 and arm B spanning x = +5.000 to
+9.000**, measured on the built STEP: 6.000 mm of clear air between each arm and
its slit wall, equal on both sides, and a 10.000 mm gap between the arms centred
on x = 0. Each arm overlaps the tube's own x range by 2.500 mm and is fused to
it, so both arms carry the telescope. They rise from a solid pier that is fused
to the drum, and run forward into a keel that carries the tube to its muzzle, so
no part of the telescope is cantilevered and `check_overhang` reads its underside
as a bridge rather than an overhang. The arms are 4.0 mm and were not thickened.

**The arms are produced by a construction that cannot depend on extrusion
winding order.** One arm is built, moved so that its *measured* minimum x lands
on `ARM_INNER_X`, and mirrored about the YZ plane. The previous revision
positioned both arms with hand-written offsets that assumed which way the
extrusion grew; it grew the other way and put both arms 4.000 mm off centre.
`measure/check_fit.py` now proves the roof is mirror-symmetric about x = 0 on the
built STEP — 0.0000 mm3 of asymmetric volume, against 8987.8 mm3 (0.91 %) in the
archive.

The dome now leaves a flat margin of 16.2 mm all the way round it on the plate.
**That margin is bare.** There is no railing, walkway, ladder, panelling, rib,
rivet, window, finial or decoration of any kind on it, and the plate has no
notches, cut-outs or holes. The roof printed on its own stands 89.7 mm tall —
3 plate + 11.7 drum + 75 dome — and the closed object is 190 x 190 x 110.7 mm.

## The counters

Round discs 20.0 mm across and 7.0 mm thick with a perfectly circular outline —
no tail, tab, notch or projection — and a 1.0 mm chamfer on both face edges,
leaving an 18.0 mm flat face. **Both faces are identical mirror images**, so the
counter is the same piece whichever way up it lies and there is no wrong way to
place it. `measure/check_fit.py` proves that on the solid, not on a render:
turning a counter over about X reproduces the same solid with a boolean residue
of 0.

Each face carries a flat 2.0 mm rim band from Ø14.0 to Ø18.0 at full face level,
a flat Ø14.0 field floor 1.5 mm below it, and a symbol raised 1.5 mm back out of
that floor to full face level inside a Ø12.5 circle, with 0.75 mm of flat clear
field between the symbol and the field wall. Every surface on the counter is flat
and horizontal or square and vertical: there is no sloped dish, conical surface,
annular rebate, plateau or halo anywhere. A 0.3 mm 45 degree bevel runs round the
top of every raised island, because a vertical-flanked island is indistinguishable
from a groove under normal-only shading. The web of solid material between the
two field floors is **7.0 - 1.5 - 1.5 = 4.0 mm**.

The Sun is an unbroken Ø6.5 ball with a 1.0 mm ring of clear field round it and
eight detached wedges from radius 4.25 to radius 6.25, each 1.8 mm wide at its
inner end and 2.2 mm at its blunt outer tip, widening outward. The whole mark is
held inside the Ø12.5 circle so the 0.75 mm clear field survives at the wedge tip
corners as well as along their flat ends.

The Moon is one slim crescent: a Ø12.5 outer arc concentric with the field,
bitten by a Ø11.20 circle whose centre is offset 2.850 mm along +x, so the two
circles cross at x = +2.78 and the horns curl past the middle towards each other,
leaving a deep bay rather than a shallow scoop. Belly 3.50 mm measured radially;
waist 3.30 mm at 150 degrees, 2.65 at 120, 1.90 at 100. Both horn tips are
rounded, never cut square. The rounding radius is 0.45 mm rather than the 0.9 mm
the correction brief named, and `GEOMETRY-NOTES.md` carries the measurement that
forced that change.

**The rim band is what makes stacking work, and that is now its job.** Two
counters placed face to face meet rim band on rim band — a full 2.0 mm annulus of
flat contact — and symbol top on symbol top, all four surfaces coplanar at full
face level. A stacked pair is 14.0 mm tall and sits square at any relative
rotation, including two Moon counters turned so their off-centre crescents lie on
opposite sides: the rim band alone carries it.

Kings are crowned by stacking, as in an ordinary draughts set. This is a change
of physical expression, not of rules. English draughts is played exactly as
before: men move and capture diagonally forward one square, capture is
compulsory, a man reaching the far row is crowned and its turn ends there, and a
king moves and captures one square diagonally in all four directions. The king
still exists, still has exactly its usual powers, and is still created at exactly
the same moment. Only the token that shows it changes, from a turned-over disc to
a stacked pair.

## Print orientation

Base bottom down. Roof flat backing plate down with the dome apex up. Counters
flat on either face — they are identical, so the choice is free; the bed contact
is the 2.0 mm rim band plus the coplanar flat top of the raised symbol, which is
a wide and well distributed first layer.

## What has and has not been verified

Digital verification only. **No physical print, tactile fit, strength, durability
or human playtesting has occurred**, and Playtest was not run for this Spark
route. Motion is unverified for this revision: the operator selected
`check_motion` false, so no motion sweep, animation or independent motion review
was run, and nothing about assemblability or working motion is claimed.
`check_overhang` fails both counters on its span proxy and the product therefore
makes **no print-ready claim**; `GEOMETRY-NOTES.md` carries that in full.

Production STEP export is reproducible run to run: `export_delivery.py` and
`write_states.py` zero the `FILE_NAME` timestamp that `export_step` stamps into
the header, and exporting the whole delivery twice in succession reproduced every
one of the 58 parts byte for byte. The five print designs likewise regenerate to
the same sha256 across runs, which is what makes the frozen-counter hash gate
possible at all. **The combined `periastra.step` is NOT byte-reproducible**: the
toolchain emits its colour-style entities in a varying order, so three successive
builds of the same geometry gave three hashes. Nothing printable and no dimension
is affected; `GEOMETRY-NOTES.md` C15 has the measurement.
`measure/revision-diff.md` lists every delivered part against the archive's
sealed group, so which parts moved and which did not is a checkable fact rather
than a claim.

## Two things this revision does NOT fix, both deliberate

The commissioner scoped both of these out. They are recorded here and in
`GEOMETRY-NOTES.md` section C6 so nobody buys the set expecting otherwise.

- **The closed box is not sealed.** The side walls drop to z17 and the roof plate
  underside seats at z21, so a 4.0 mm reveal runs right round the perimeter. It
  is deliberate sightline, and it is also an opening.
- **The 32 inlays are loose.** They are gravity-seated with no retention feature,
  and at 2.0 mm thick they are thinner than that 4.0 mm reveal, so tipping the
  closed box can spill them. A counter cannot pass — its smallest dimension is
  7.0 mm — so what you lose on tipping is inlays, not counters.

Closing the box would resolve both at once and is not attempted here.

Cell pitch and full side width remain 22 mm. A Ø20.0 counter leaves 1.0 mm of
board each side inside a 22 mm cell and seats flat on the inlay: the inlay's
chamfer line stands 14.50 mm from its centre against the counter's 10.00 mm
radius, so a Ø20.0 circle fits entirely on the flat top. There is no raised grid.

## Print orientation for the inlays

Flat, either face down — the tile is symmetric top to bottom apart from which
face finishes flush, and both are flat. 32 of them. They are the only part of the
set printed in a second colour, and that colour is the whole point of the part.
