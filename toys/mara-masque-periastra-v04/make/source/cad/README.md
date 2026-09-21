# Periastra Zenith CAD — revision D: the telescope stands on the floor

Miniature English draughts in a removable-roof observatory, where the two sides
are the Sun and the Moon and the roof is the dome that watches them. Five
independently printable designs form 58 physical parts: one base, one domed
roof, thirty-two board inlays, twelve Sun counters and twelve Moon counters. No
hardware or power.

**What revision D changes, and all it changes.**

One thing: the telescope and the way the dome carries it.

1. **The slit stops at the springing line.** It still runs the full height of the
   dome — from its far edge, over the apex, down the near flank to the bottom of
   the dome — but its lower limit moves from z3.0, the plate top, to z14.7, the
   drum top. It cuts the dome only, so the drum below is whole and its
   rotation-ring groove runs unbroken all the way round. The floor the cut leaves
   is the exposed drum top, and that is the observatory floor.
2. **The telescope stands on that floor.** 85.3 mm of tube at 50 degrees, its
   axis meeting the floor at (0, +13.0, 14.7), cut off flat **by** the floor
   plane on a level 15.0 x 19.58 mm elliptical foot fused to the drum, and
   blended into it with a 6.0 mm cove carried right round that foot. It leaves
   the dome 32.4 degrees from the apex and its muzzle stands 3.899 mm proud of
   the shell, 2.586 mm of that measured on its own axis.
3. **The old mount is deleted.** No fork, no arms, no keel, no pier, no foot
   block. Above the floor the only thing standing in the slit is the telescope.

Nothing else moves. `base`, `inlay`, `sun_counter` and `moon_counter` come out
byte-for-byte identical to the archive and `measure/check_fit.py` asserts all
four hashes on every run.

`periastra.step.py` is the combined closed assembly; `assembly.py` positions its
live-source children. `part_base.step.py`, `part_roof.step.py`,
`part_inlay.step.py`, `part_sun_counter.step.py` and `part_moon_counter.step.py`
return bed-oriented parts. `periastra_lib.py` holds dimensions and geometry. The
26 structural part keys of the archive — `base`, `roof`, `single_01`..`single_12`,
`forked_01`..`forked_12` — are all still present, and this revision adds
`inlay_01`..`inlay_32`, for 58. `single_*` is the Sun counter and `forked_*` is
the Moon counter.

Base 190 by 190 by 24 mm, board 176 mm with 22 mm cells. Four designs are frozen
and `measure/check_fit.py` asserts all four on every run:

| design | sha256 |
|---|---|
| `part_base.step` | `1db4b15610146fc0c993268802e0279d7859f56b42df22f7ba5d3915ad55e1b8` |
| `part_inlay.step` | `81085d55483e4841813ccbd069c89d4c8d4d285de977e334da709fcdf38e9b90` |
| `part_sun_counter.step` | `262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b` |
| `part_moon_counter.step` | `588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e` |

`part_roof.step` is the one design this revision moves, and `check_fit.py` also
fails the build if it comes out as the archive's roof. Print on a 220 by 220 mm or
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
ring. **That ring is continuous.** Nothing is cut through the drum wall at any
point on its circumference, and `measure/check_fit.py` proves it on the built
STEP: the roof sliced at z4.0, 7.0, 9.0, 10.7, 13.0 and 14.0 is one piece at
every height, with 0.000000 mm3 of gap in the ring band and 0.000000 mm3 of notch
in the outer wall wherever the groove does not cut it. It also proves that
0.000000 mm3 of roof lies outboard of the 75.0 mm drum radius anywhere below the
springing line.

An **exact hemisphere** of sphere radius 75.0, centred on the axis at the drum
top, rises from there: base radius 75.0, rise 75.0, nominal apex at z110.7
closed. At its base the hemisphere's surface is vertical, so it flows continuously
into the drum wall and prints apex-up with a 0 degree base overhang.

One 30.0 mm shutter slit with parallel square-cut walls is cut **through the dome
only**, on a single meridian in the YZ plane. It runs from 30.0 mm of surface arc
— 30/75 radian, 22.9 degrees — past the apex on the far side, over the apex, and
down the near flank to the springing line at z14.7, where it stops. The far half
of the dome stays unbroken and the drum is untouched. The slit is kept at its
built absolute size and is not scaled with the dome: the 30 mm width is what
gives the telescope clear air on both sides.

The slit's floor is the exposed drum top: a level surface 30.0 mm wide, bounded in
y by the drum's own 75.0 mm circle, running from y -73.48 at the slit walls
(y -75.0 on the centreline) to the far wall at y +29.21. **That is the observatory
floor, and it is the one piece of solid material the telescope can reach without a
bracket** — the dome is a solid hemisphere and the slit is a box that removes
every piece of material inside it, so nothing else within reach of the tube still
exists.

**The telescope is therefore its own pier.** A 15.0 mm outer tube, 85.3 mm long
measured along its axis from the floor plane, on an axis 50 degrees above
horizontal lying on x = 0 — the slit's own mid-plane — meeting the floor at
y = +13.0. The floor plane itself cuts the tube off flat, so it stands on a level
elliptical foot 15.0 x 19.58 mm fused to the drum, and the root is blended into
the floor with a **6.0 mm cove fillet carried right round the foot**. Measured on
the built STEP the root is 26.425 mm across the slit and 35.246 mm along it,
leaving 1.788 mm of clear air to each slit wall and 3.618 mm to the far wall. The
muzzle is open: a 7.0 mm bore 13.0 mm deep leaving a 4.0 mm tube wall.

It leaves the dome 32.4 degrees from the apex and its muzzle stands 3.899 mm
proud of the sphere — 0.26 of the tube's own diameter, and 2.586 mm measured on
the axis — with its top at z84.86 local, under both the nominal apex at z89.7 and
the built high point at z88.1847. 82.69 mm of the 85.3 lies inside the dome,
visible down the open slit. The footing at y +13.0 and the length of 85.3 mm are
the low ends of the two windows the correction brief leaves free; `GEOMETRY-NOTES.md`
D9d says why they were taken there.

**50 degrees is a hard floor, not a preference.** For a cylinder whose axis sits E
degrees above horizontal, the steepest downward-facing surface has its normal E
degrees from vertical. At 35 degrees, which is what the archive built, the tube is
a 35-degree overhang and fails the 45-degree gate — which is the real reason the
old keel existed. At 50 it clears by 5 degrees and needs nothing under its length.
`check_overhang` passes `part_roof` at a 0.4 mm nozzle with the keel deleted.

**Above the floor, the only thing standing in the slit is the telescope.** No
fork, no arms, no keel, no pier, no foot block. `measure/check_fit.py` slices the
roof inside the slit at z15.2, 18.0, 25.0, 40.0, 60.0 and 78.0 and asserts exactly
one lump of material at each height, centred on x = 0 within 0.000001 mm. It also
asserts the roof is a single connected solid — the gate that would catch a mount
deleted without giving the tube something to stand on — and keeps revision C's
mirror-symmetry test, which measures 0.0000 mm3 of asymmetric volume.

**The root is a cantilever and no physical test backs it.** 85.3 mm of tube is
overhung from that 15.0 x 19.58 mm foot, 65.3 mm above the floor with 54.8 mm of
horizontal run and its centre of mass 17.6 mm outside the foot. In FDM the layer
lines at the root run across the bending plane. The cove is the mitigation and it
is a geometric one only. `GEOMETRY-NOTES.md` D4 carries this in full.

The dome leaves a flat margin of 16.2 mm all the way round it on the plate.
**That margin is bare.** There is no railing, walkway, ladder, panelling, rib,
rivet, window, finial or decoration of any kind on it, and the plate has no
notches, cut-outs or holes. The roof printed on its own stands 88.1847 mm tall —
the nominal 89.7 of 3 plate + 11.7 drum + 75 dome, less the 1.5 mm the shutter
removes at the apex — and the closed object's declared envelope is
190 x 190 x 110.7 mm with its highest material at z109.185. That envelope is
measured identically on the archive's roof and this revision does not move it.

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

Base bottom down. Roof flat backing plate down with the dome apex up; the telescope needs no
support under its length at 50 degrees. Counters
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
than a claim: 57 of the 58 delivered parts are byte-identical and only `roof`
changed.

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
