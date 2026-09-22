# Geometry notes, deviations and limitations — Periastra Zenith

Everything here is measured, not assumed. Each item names the tool or the script
that produced the number.

This file has two parts. **Part D** records revision D, the correction in front of
you: the telescope and the way the dome carries it. **Everything below the
"carried forward" rule** is the previous revision's note set, kept as history.
Inside it, "Part I" means revision C and "Part II" means the archive revision C
corrected; those labels are historical and are not renumbered. Exactly one
sentence in it has been edited — the stale colour-contrast line in section 6,
marked superseded as the correction brief required. Nothing else that was written
before has been changed.

---

# Part D — revision D: the telescope stands on the observatory floor

One thing changes: the telescope and the way the dome carries it. Everything else
in this object stays where it is, and four of the five print designs come out of
this revision byte for byte identical to the archive.

## D0. The name changed, and why

The corrected archive is `toys/mara-masque-periastra-zenith`. The name had to
change: a `--no-publish` correction cannot overwrite a `toys/` slug that already
holds different bytes, because `materialize_public_example` refuses with "public
example already exists with different or partial bytes" when a locally sealed run
has no Factory receipt. The last revision kept its name, finished Make and
Release, and then failed to write its archive at the very last step. This is a
distinct revision title, not a re-publication of Periastra Meridian.

## D1. What was wrong, measured on the shipped roof

Three findings from the independent critic on the archive, all on the roof and all
about the same region: the telescope and its trough broke out of the dome's lower
flank and read as a teapot spout; the yoke's foot block projected outboard of the
drum face and terminated in raw untreated flats; and the telescope read as a
cannon or a mortar rather than an instrument. The measured causes and the measured
result:

| what | archive | revision D |
|---|---|---|
| where the tube leaves the dome, from the apex | 55.0 deg | **32.37 deg** |
| bare dome skin crossed before the muzzle clears | 13.0 mm | 0.0 mm |
| muzzle projection past the 75 mm sphere, on the axis | 11.9 mm | **2.586 mm** |
| the same, measured to the farthest material | — | **3.899 mm** |
| farthest material, as a fraction of the tube's 15.0 mm diameter | 0.79 | **0.26** |
| slit lower limit | z 3.0, the plate top | **z 14.7, the drum top** |
| the drum's rotation ring | cut through by a 30 mm channel | **continuous** |

**Raising the elevation alone does not fix this.** With the pivot at
`(0, -35.2, 39.4)` — 35 mm off the axis and low — 35 degrees of elevation exits at
55.0 degrees from the apex, 50 degrees exits at 48.5 and 65 degrees exits at 41.6.
Thirty degrees of extra elevation buys thirteen degrees of exit angle. The pivot is
the lever, not the angle.

## D2. The slit runs the full height of the dome and stops at the springing line

The opening loses nothing. It still runs from its far edge at y +29.21, over the
apex, and down the near flank to the bottom of the dome. Only its lower limit
moves:

```
SLIT_FLOOR_Z = PLATE + DRUM_HEIGHT = 14.7      (was PLATE = 3.0)
```

The slit is subtracted from the dome alone, so the drum below it keeps its full
wall and its rotation-ring groove runs unbroken all the way round. The floor the
cut leaves behind is the exposed drum top: a level surface 30.0 mm wide, bounded
in y by the drum's own 75.0 mm circle, so it runs from y -73.48 at the slit walls
(y -75.0 on the centreline) to the far wall at y +29.21. That is the observatory
floor, and the telescope stands on it.

## D3. The telescope stands on that floor and lies across the dome

```
TUBE_ELEVATION   50.0 deg                      (was 35.0)
TUBE_FOOT        (0.0, +13.0, 14.7)            the axis meets the floor here
TUBE_LENGTH      85.3 along the axis FROM THE FLOOR PLANE   (was 45.0 on a yoke)
TUBE_RADIUS / TUBE_BORE_RADIUS / TUBE_BORE_DEPTH   7.5 / 3.5 / 13.0, unchanged
```

The tube is built through the floor plane and cut off flat **by** it, so it stands
on a level ellipse. Measured with `measure/check_fit.py`:

| quantity | measured |
|---|---|
| elliptical foot, across the slit x along it | **15.0 x 19.5811 mm** |
| the axis runs from | (0, +13.00, 14.70) to (0, -41.83, 80.04) |
| exit angle from the apex | **32.37 deg** |
| of the 85.3 mm of tube, the length inside the dome | **82.69 mm** |
| muzzle projection past the 75.0 mm sphere, on the axis | **2.5855 mm** |
| muzzle projection, farthest material on the rim | **3.8993 mm** (0.26 of a tube diameter) |
| muzzle top | z **84.8645** local, z105.86 closed |
| nominal dome apex z 89.7 — the muzzle is under it by | 4.8355 mm |
| built high point of the roof z 88.1847 — the muzzle is under it by | 3.3202 mm |

**Two projection numbers exist and both are reported, and both are held inside the
brief's 2.5-7.0 mm window.** The brief quotes the projection as an *axis* figure
("3.2 mm = 0.21 of the tube's own diameter") and separately asks the built check to
"measure how far the muzzle stands proud". Those are different numbers, because the
farthest point of the muzzle is on its rim and the rim is off axis.
`check_fit.py` asserts both: 2.5855 mm on the axis, 3.8993 mm to the material.

**Why 50 degrees, and why it is a floor.** For a cylinder whose axis sits E degrees
above horizontal, the steepest downward-facing surface has its normal E degrees
from vertical. At the shipped 35 degrees the tube was a 35-degree overhang and
failed the 45-degree gate, which is the real reason the keel existed. At 50 degrees
it clears by 5 degrees and needs nothing under its length: `check_overhang` passes
`part_roof` at a 0.4 mm nozzle with the keel deleted. `check_fit.py` asserts
`TUBE_ELEVATION >= TUBE_ELEVATION_MIN == 45.0`.

**Why the footing is at y +13.0 and the tube is 85.3 mm.** Both are the low end of
the two windows the brief leaves free, and both were moved there after the first
independent review; D9d has that history. y +13.0 puts the tube's axis 9.96 mm from
the sphere's own centre instead of 11.49 mm, so the tube leaves the shell more
radially and less of its flank stands in the open. 85.3 mm is the shortest length
that keeps **both** projection figures inside 2.5-7.0 mm: below it the axis figure
drops under 2.5.

## D4. The root, and the one genuine risk this change introduces

The whole tube is a cantilever taken entirely at its root:

| quantity | value |
|---|---|
| length overhung from the foot | 85.3 mm |
| height above the floor | 65.34 mm |
| horizontal run | 54.83 mm |
| foot | 15.0 x 19.5811 mm ellipse |
| centre of mass, horizontally outside the foot | 17.6 mm |

In FDM the layer lines at that root run across the bending plane, which is the weak
direction, and a bare butt joint between a cylinder and a flat floor would snap
there.

**The fillet built is a cove of radius 6.0 mm, carried right round the foot.** The
resulting root, measured on the built `part_roof.step`:

| quantity | measured |
|---|---|
| **cove fillet radius** | **6.0 mm** |
| **root width across the slit (x)** | **26.4246 mm** |
| **root run along the slit (y)** | **35.246 mm**, from y -9.6576 to y +25.5884 |
| clear air to each slit wall at the floor | 1.7877 mm |
| clear air to the slit's far wall | 3.6180 mm |

The cove's run onto the floor is `r / tan(theta/2)` for a dihedral `theta`, which is
why it is long on the downhill side of the foot and short on the uphill side; the
numbers above are the built extents, not that formula. A larger radius was not
taken because the cove must stay inside the 30 mm slit and clear of both walls, and
6.5 mm would leave under 1.1 mm of air on x.

**No physical test backs this fillet.** It is a geometric mitigation of a cantilever
root. Nothing here establishes that the telescope survives printing, handling or a
knock, and this product makes no print-ready claim at all.

## D5. The old mount is deleted entirely

No fork, no two arms, no keel, no pier and no rectangular foot block. The constants
and the helper that built them are gone from `periastra_lib.py`, and
`check_fit.py` asserts their absence by name: `PIER_Y`, `PIER_TOP`, `ARM_THICK`,
`ARM_INNER_X`, `ARM_GRIP`, `ARM_RISE`, `ARM_KEEL`, `arm_profile`, `TUBE_BACK`,
`MUZZLE_CLEARANCE_MIN`.

## D6. Proved on the built STEP — every number section E of the brief asked for

All of these read `part_roof.step`, not the source that made it.
`measure/check_fit.py` writes them to `measure/fit-audit.json` and fails the build
if any of them moves.

**The roof is one connected solid.** `len(roof.solids()) == 1`, volume
1009918.6 mm3. Zero floating lumps. This is the gate that would have caught a bare
yoke deletion: remove the mount, leave the tube where it was, and the roof becomes
two bodies with one of them in mid-air.

**The only thing in the slit is the telescope.** The roof is sliced horizontally
inside a window that never touches a slit wall, at six heights above the floor:

| z | lumps | x span of the lump | centre x | what it is |
|---|---|---|---|---|
| 15.2 | **1** | -11.4028 .. +11.4028 | 0.000001 | tube + cove |
| 18.0 | **1** | -8.1943 .. +8.1943 | 0.000001 | tube + cove |
| 25.0 | **1** | -7.5000 .. +7.5000 | 0.000000 | bare tube |
| 40.0 | **1** | -7.5000 .. +7.5000 | 0.000000 | bare tube |
| 60.0 | **1** | -7.5000 .. +7.5000 | 0.000000 | bare tube |
| 78.0 | **1** | -7.5000 .. +7.5000 | 0.000000 | bare tube |

One lump at every height, centred on x = 0 within 0.000001 mm against the brief's
0.01 mm allowance. No arms, no keel, no pier, no block.

**The tube reaches the floor.** Everything standing in the slit from the floor to
the apex is a single body whose lowest material is at z **14.700000**, the floor
plane itself. Its footprint there is 26.4246 x 35.246 mm, which contains the
15.0 x 19.5811 mm foot, and it is fused to the floor because the roof is one solid.

**The floor is one face, and the foot is a hole in it.** The roof carries exactly
**one** planar face in the floor plane at z 14.7. Its area is **2384.5425 mm2**,
its bounding box is 30.0 mm across and runs y -75.0 to +29.2064, and the
telescope's foot occupies a **722.1027 mm2** hole in it. There is no second,
coincident surface there. This measurement exists because the first blind critic
read the blend at the root as "coincident-surface noise — two surfaces occupying
the same place"; D9b records what that reading actually was.

**The slit crosses the zenith.** A column 4.0 mm across standing on the dome's own
axis, from z 85.5 — above the telescope's highest material — up to the nominal apex
at z 89.7, contains **0.000000 mm3** of roof material. If the slit did not run over
the crown the dome would be solid out to r 10.2 mm at z 89.0. This measurement
exists because the second blind critic read the plan frame as showing a slot that
"does not reach the zenith"; D9e records what that reading was.

**The drum ring is continuous.** The roof is sliced through the drum at six heights
between the plate top and the springing line. Each slice is one piece; the ring
band from r 70.0 to r 73.9 is solid all the way round at every height; and where
the rotation groove does not cut it, so is the outer wall from r 74.05 to r 74.95.

| z | pieces | outer diameter | ring-band gap | outer-wall gap |
|---|---|---|---|---|
| 4.0 | 1 | 150.0 mm | **0.000000 mm3** | **0.000000 mm3** |
| 7.0 | 1 | 150.0 mm | **0.000000 mm3** | **0.000000 mm3** |
| 9.0 | 1 | 150.0 mm | **0.000000 mm3** | **0.000000 mm3** |
| 10.7 | 1 | 148.0 mm (the groove) | **0.000000 mm3** | not probed, in the groove |
| 13.0 | 1 | 150.0 mm | **0.000000 mm3** | not probed, in the relief |
| 14.0 | 1 | 150.0 mm | **0.000000 mm3** | **0.000000 mm3** |

**Nothing projects outboard.** Between the plate top at z 3.0 and the springing line
at z 14.7, the volume of roof material outside the 75.0 mm drum radius is
**0.000000 mm3**. The 182.4 mm backing plate below z 3.0 is the preserved design and
is excluded by construction; that exclusion is stated in the source of the check,
not hidden in it.

**Mirror symmetry**, the gate revision C added and this revision keeps: the roof cut
against its own mirror image about x = 0 leaves **0.0000 mm3** of asymmetric volume
out of 1009918.6 mm3, **0.0000 %**. It was 0.0000 mm3 in revision C and it has
stayed there.

**The projection**, measured on the tessellated built solid as the farthest material
above the springing line from the sphere's own centre, minus 75.0: **3.8993 mm**,
inside the brief's 2.5-7.0 mm window, with the axis figure at **2.5855 mm** inside
the same window.

**The muzzle stays under the apex.** Muzzle top z 84.8645; nominal apex z 89.7;
built high point z 88.1847.

**The four frozen hashes**, asserted on every run:

| design | sha256 | verdict |
|---|---|---|
| `part_base.step` | `1db4b15610146fc0c993268802e0279d7859f56b42df22f7ba5d3915ad55e1b8` | byte-identical |
| `part_inlay.step` | `81085d55483e4841813ccbd069c89d4c8d4d285de977e334da709fcdf38e9b90` | byte-identical |
| `part_sun_counter.step` | `262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b` | byte-identical |
| `part_moon_counter.step` | `588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e` | byte-identical |
| `part_roof.step` | `da320a57109473fc5031044b55a100f2ddd97314863cfb2ccab60d0e2e82a52d` | **CHANGED**, as required |

`check_fit.py` also asserts that the roof is *not* the archive's
`23957b5a061b948099df92c67412ea1f6ca1fd9727b3a273aaa1298c5b46c9ed`, so a no-op
build fails instead of passing quietly.

## D7. The closed envelope is unchanged, and the honest number for it

The declared envelope stays 190 x 190 x 110.7 mm, which is the base plus the
nominal dome apex. The **built** roof measures 182.4 x 182.4 x **88.1847** mm,
because the shutter slit runs over the apex and removes it: the highest material on
the roof is the dome shoulder at the slit wall,
`14.7 + sqrt(75^2 - 15^2) = 88.1847`, which puts the closed object's highest
material at z109.185. That is the archive's own envelope, measured identically on
`revision-work/make/models/cad/part_roof.step`, and this revision does not move it.
`check_fit.py` asserts all three numbers.

## D8. What did not move

`base`, `inlay`, `sun_counter` and `moon_counter` are byte-identical, and
`measure/revision-diff.md` compares every one of the 58 delivered parts against the
archive's sealed build group: 57 unchanged, 1 changed (`roof`), 0 added, 0 removed.
Every constant the brief listed keeps its value and `check_fit.py` asserts each of
them. The dome is still an exact hemisphere on a visible drum, the plate is still
bare, and the board, its 32 inlays and both counters are untouched.

## D9. The evidence set

Every frame the archive carried is regenerated here from the new geometry and none
is removed. `cad/render_family.py` is the frame table, so the set is reproducible
rather than assembled by hand.

Two frames are **renamed and nothing else**: `roof/yoke_az-60_el18.png` and
`roof/yoke-close_az-60_el18.png` are now `roof/quarter_az-60_el18.png` and
`roof/quarter-close_az-60_el18.png`, at the same camera and the same crop. The yoke
they were named after no longer exists, and no feature that replaces it is visible
from that camera, so they are named for the camera instead. See D9b.

Section F of the brief required four frames in the FIRST review round, and they were
in it. They are listed here as they now stand, after the two evidence repairs D9b
and D9d record:

- `snap/roof/side-elevation_az0_el0.png` and `snap/roof/side-elevation-close_az0_el0.png`
  — a straight side elevation with the camera **level with the dome**. The
  silhouette requirement is matched on this frame and on no other; oblique frames
  were not accepted for it.
- `snap/roof/into-slit_az-75_el24.png`, `snap/roof/into-slit_az-105_el24.png` and
  `snap/roof/into-slit_az-90_el28.png` — three-quarter views into the open slit from
  both quarters and down its own axis — with `snap/roof/foot-in-slit_az-90_el14.png`
  and `snap/roof/foot-macro_az-90_el28.png` as close crops of the foot itself.
- `snap/roof/drum-ring_az0_el6.png`, `_az90_`, `_az180_` and `_az-90_` — the drum
  from four azimuths 90 degrees apart, rendered at 1800 px so the 11.7 mm ring is
  legible.
- the same three-quarter frames again for the unfinished-surface question.

Two further frames were added in the last repair and D9e says why:
`snap/roof/slit-elevation_az-90_el0.png`, a straight elevation at the same camera
height as the silhouette frame but looking along the slit's own axis instead of
across it, and `snap/roof/foot-macro_az-90_el55.png`, the root from high above where
the tangency artefact of D9c is least in the way.

Two more frames were added on the critic's recommendation in round 6:
`snap/closed/corner-seat_az-45_el6.png` and its close crop. Shot square to a side,
the closed object reads as a lid that will not shut; shot at the corner, where the
four integral ledges carry the plate inside the opening, the 4.0 mm gap reads as
what it is — a sightline, with the plate seated.

**The frame that shows this object best is
`snap/roof/slit-elevation_az-90_el0.png`, not `snap/roof/side-elevation_az0_el0.png`.**
That is the independent critic's recommendation, made in
`review/revision-d/round-5-final-resolution.md`, and it is recorded here because it
costs no geometry: at az0 the shutter is edge-on and the object reads as a smooth
cloche with a nub; one bearing round, at the same camera height, it reads as an
opened dome with an instrument standing in it.

Carried forward unchanged: `snap/roof/slit-plan_el90.png` and
`slit-plan-close_el90.png` (the plan view down the slit) and
`snap/board/populated-plan_el90.png` and `empty-plan_el90.png` (the whole board at
playing scale, at 1800 px), which the previous brief required.

## D9b. The first evidence repair, and no geometry moved with it

The first blind critic (`review/revision-d/round-1-blind-read.md`) reported that the
telescope "tapers to a needle" and that its lower end "disappears into a grey
speckled, dithered smear — coincident-surface noise", and called it the worst defect
in the set. Two of its three roof findings were about the pictures, not the part,
and one of them was a framing error of mine. All three were investigated before
anything was changed:

1. **The taper is a line-of-sight effect.** The slit is 30.0 mm wide and roughly
   90 mm deep, and the tube lies on its mid-plane. A camera 15 or 30 degrees off the
   slit's axis has the near slit wall standing in front of the lower part of the
   tube, so the visible sliver narrows with depth and the root is hidden. The only
   line of sight that reaches the root is straight down the slit's own axis. The
   frames the critic was given for that question were 15 degrees off it.
2. **The speckle is the renderer, and it is now measured.** `render_review` is a
   flat-shaded z-buffer renderer. A tangent fillet dying into a plane has, at its
   outer margin, a surface whose normal and whose depth both approach the plane's,
   so the two dither against each other at grazing camera angles. Re-triangulating
   at 0.01 mm instead of 0.05 mm does not remove it; raising the camera does. The
   geometric question the critic actually raised — are there two surfaces there? —
   is answered in D6 by measurement: one planar face in the floor plane,
   2384.5425 mm2, with the 722.1027 mm2 foot as a hole in it.
3. **`roof/foot*_az-60_el18.png` had no foot in them.** The critic said so and was
   right. At 30 degrees off the slit's axis the near wall hides the slit floor
   completely, so no crop of that camera can show the root. Naming those frames
   after the foot was my error.

What changed, and nothing else: every frame re-triangulated at **0.01 mm** instead
of 0.05 mm for display, which also removed the dome banding the same critic
reported; `snap/iso.png` and `snap/signature.png` at 0.02 mm instead of 0.08 mm; the
two mis-named frames renamed to `roof/quarter_*` with the archive's own crop
restored; and three frames added that look straight down the slit's axis and reach
the root.

**No solid moved with that repair.** `part_roof.step` hashed
`445bf4503ee374987f9cb553b275a8d0d6c78af5d5fe5c9a00071a0138dcd878` before and
after it, all four frozen designs were unchanged, and `measure/fit-audit.json`
reported the same numbers.

The same critic read the repaired frames, still without being told anything about
the object, in `review/revision-d/round-2-second-blind-read.md`. It withdrew both
findings in full: "my round-1 answer of 'nothing' was wrong... on axis it is
obvious", and "It is the floor of the slot with the tube socketed through it... I
read a partially-occluded sliver of it as a run-out."

## D9c. Renderer limitation, stated so it is not mistaken for geometry

Carried forward from Part II section 7 and extended by what this revision found:
`render_review` applies deterministic flat shading with no ambient occlusion and no
anti-aliasing of depth ties. Where a tangent blend runs out onto a plane — the cove
at the telescope's root is the only such place in this product — the last millimetre
of the blend dithers against the plane at grazing camera angles. It is a display
artefact of a tangent fillet, it is present in every render of this product at low
elevations, and it is not in the delivered STEP. The frames that show the root with
the least of it are the two taken down the slit's axis at 14 and 28 degrees of
elevation.

## D9d. The second repair: the silhouette, and a contaminated question

In round 2 the same critic was asked the brief's silhouette question, and I asked it
badly. The brief's question is open — "what does the thing sticking out of this dome
look like?" — with the requirement that the answer must not be a spout, a cannon, a
mortar or a gun. I put those four words in front of the critic as a yes/no. Its
round-1 answer, given with no options offered, had been "snapped-off pipe, chimney,
straw-end" — none of the four. Its round-2 answer, after I named them, was "YES...
a mortar or short cannon barrel poking out of an armoured cupola". **The
contamination is mine and it is recorded here rather than argued away.**

The finding was treated as real regardless, and the geometry was changed:

```
TUBE_FOOT   (0.0, +15.0, 14.7)  ->  (0.0, +13.0, 14.7)
TUBE_LENGTH 87.0                ->  85.3
```

Both are the low end of the two windows the brief leaves free, and the brief grants
them in terms: "FREE VARIABLES, yours to move if the first review fails". The first
review failed on exactly this. The effect, measured:

| quantity | before the repair | after |
|---|---|---|
| axis projection past the sphere | 3.2069 mm | **2.5855 mm** |
| farthest material past the sphere | 4.6548 mm | **3.8993 mm** |
| the same, over the tube's own diameter | 0.31 | **0.26** |
| distance from the sphere's centre to the tube's axis | 11.491 mm | **9.959 mm** |
| exit angle from the apex | 31.19 deg | 32.37 deg |
| clear air from the cove to the slit's far wall | 1.618 mm | **3.618 mm** |

The smaller the distance from the sphere's centre to the axis, the more radially the
tube leaves the shell and the less of its flank stands in the open; the shorter
length stands less of the tube outside. 85.3 mm is the shortest length that keeps
both projection figures inside the brief's 2.5-7.0 mm window.

**What this repair could not do.** Three things the first critic asked for are
forbidden by constraints this revision does not own, and each was checked rather
than waved away:

- **A collar, flange or shroud at the exit.** The tube does not pierce the dome
  skin at all — it passes out through the 30.0 mm open slit with 7.5 mm of air on
  each side — so there is no dome material at the exit to put a collar on. A collar
  on the tube itself would be an outward feature on a cylinder inclined 50 degrees,
  and its downward-facing annulus would be an unsupported overhang: to keep that
  surface within 45 degrees of vertical the radius may grow by at most 0.0873 mm per
  mm of axis, so a 2 mm collar would need 23 mm of axial run and would not read as a
  collar at all.
- **A chamfer or bevel on the muzzle rim.** A 45-degree chamfer on a tube at 50
  degrees of elevation leaves a downward-facing conical surface about 5 degrees from
  horizontal, roughly 15 mm2 of it. `check_overhang` would fail `part_roof` on it,
  and this product already carries one print-gate failure it cannot fix.
- **Ribs, panel lines, a shutter or a base moulding on the dome.** The dome, the
  drum and the bare plate are all on the brief's preserved list.

Because the level side elevation looks along x and the muzzle's end face is normal
to a direction in the y-z plane, that face is seen exactly edge-on from that camera
and no amount of detail inside the bore can show there. What that frame can show is
how much tube stands outside the shell, and that is what this repair reduced.

A **fresh, previously unseen independent critic** then read the final frames with
no options offered and no knowledge of this history, in
`review/revision-d/round-3-fresh-blind-read.md`, and the requirement comparison in
`round-4-reveal-and-comparison.md` is bound to that reading. Using a second
unprimed reader rather than the primed one is the stricter choice, and it is the
reason four review rounds were spent.

## D9e. The last round, and what the second critic withdrew

The fresh critic's primed comparison (`round-4-reveal-and-comparison.md`) scored
11 of 13 requirements matched and returned two blocking defects. Both were put back
to it properly and both were withdrawn in `round-5-final-resolution.md`, on its own
reasoning:

- **B2, "the slit does not reach the zenith".** The critic offered to trade this one
  for a measurement and the measurement was taken: 0.000000 mm3 of roof on the dome's
  own axis between z 85.5 and the apex, and 0.0000 mm3 of asymmetric volume about
  x = 0. It withdrew without reservation and named its own two errors: it read the
  slit's *length* asymmetry — 29.2 mm past the centre on the far side, then all the
  way down the near flank — as a *width* offset across the slit, and it judged a
  crown-crossing cut on a sphere from a single orthographic plan, which flattens
  exactly the information needed to tell that cut from a flank cut.
- **B1, "the instrument does not read as an instrument".** This one was my framing
  error again. I gave the critic the brief's positive reading clause as a bare
  sentence with no frames attached, and it judged it in the only elevation it had,
  which is the one where the shutter is edge-on. The brief splits the two tests: the
  *negative* silhouette test lives in the straight side elevation ("must not read as
  a spout, a cannon, a mortar or a gun"), and the *positive* reading clause is
  written around seeing down the open slit ("most of its length visible down the open
  slit"). Told that, and given the new axial elevation, the critic scored P9 MATCHED
  and withdrew B1 — explicitly not to be agreeable: "a blocker has to be something
  this correction introduced or failed to remove", its own blind three words were
  "snapped-off peg" with none of the four forbidden readings anywhere in its answer,
  and it established that the az0 reading cannot be improved inside the freeze at
  all.

**Why the az0 elevation cannot be improved, checked rather than asserted.** The
critic's own summary, which matches the three checks recorded in D9d: the aperture is
invisible from az0 because the hemisphere is solid and the slit is meridional, so
from that bearing it yields only the two edge nicks; a muzzle ring, flange, chamfer
or dew shield is barred by the frozen 15.0 mm outer diameter, the frozen 7.0 mm bore
and the flat crosscut, and each would put a fresh overhang on a part required to
print support-free at 45 degrees; and protruding further is barred by "only its mouth
clearing the shell" and is precisely what produced the cannon this correction exists
to kill.

**Two things are carried forward as the critic's recorded objections, not as passes.**
It still reads the aperture as one that could never open, because it dies on the
unbroken rotation ring — the commissioner chose that trade knowingly, and D2 says so.
And it still reads the object at az0 as damaged: a blunt stub beside a matching
silhouette nick. Neither is scored as a defect of this correction and neither is
argued away here.

Final score on the correction's own requirements: **13 matched, 0 not matched, no
blocking defects.** Three critics' worth of rounds sit in `review/revision-d/`; the
sealed review is the second critic's, rounds 3 to 5, bound to the exact image bytes
this product ships.

## D9f. The sealed judgements, and two grounds withdrawn against measurement

`round-6-final-judgements.md` holds the nine judgements the sealed review record
carries. Eight were YES immediately. The ninth — does the delivered product read as
a finished, resolved object — came back **NO**, and it is on the record as NO before
it is anything else.

Its first form rested on three legs: purchase intent, the fact that nothing has been
printed, and two geometric relationships. The first leg was my fault: I asked "is
this a desirable object?" instead of the question the record actually asks, and the
critic answered on purchase intent, reasonably. The second the critic withdrew
itself once shown that the untested status is sealed beside this field rather than
behind it, and that counting it here would count it twice. The third stood, and it
was the real objection:

- the counters "are as large as their squares and overhang onto the light field";
- the lid "rests on the rim with an open gap all round" and "nothing shows how the
  lid is located or retained".

Both were measured rather than argued, and both are misreadings of flat-shaded
orthographic frames — the same failure mode as B2, which the critic had already
named and traded:

| what the critic read | what is built |
|---|---|
| counters overhang their squares | the dark square is a separate 21.5 mm inlay tile; a 20.0 mm counter leaves **0.75 mm of dark tile showing on every side**, and `check_fit.py` proves containment as a boolean that fails the build, not as arithmetic |
| the lid perches on the rim, nothing locates it | the 182.4 mm plate drops **inside** the 184.0 mm opening on a **0.8 mm per-side** spigot and lands on four integral 3.0 x 3.0 mm corner ledges at z21.0, probed on the built base |

The critic withdrew both, named what it had misread in each case — a raised disc
images larger than a flat tile in a perspective camera while a coplanar tile edge
carries no tonal step from overhead; and its own round-3 "defect 10", the flange
corners appearing to intersect the piers, was the 0.8 mm spigot fit it was looking
straight at — and answered the field YES.

**Three things it attached to that YES, and all three are recorded here as it asked:**

1. It has not independently verified the measurements it accepted. It took these as
   it took the zenith volumes, on their specificity and falsifiability. If any of
   them is wrong its YES is wrong with it. They are reproducible: every one is
   asserted in `measure/check_fit.py` and written to `measure/fit-audit.json` on
   every run.
2. The reveal needed a frame that sells it. Acted on: `snap/closed/corner-seat_*`
   above.
3. Process feedback, carried forward as feedback and not as an objection: one
   boolean field spanning a frozen inherited set and the correction under review is
   a weak instrument, and it nearly failed a roof scored 13/13 over two board
   readings that turned out to be wrong. The critic's words: split the field, or
   scope it to the correction.

**Its standing objection is unchanged, unscored and not a gate:** the aperture dies
on an unbroken rotation ring, and it believes viewers will read it as an aperture
that cannot open. The commissioner chose that trade knowingly; D2 says why.

## D10. Motion is unverified for this revision

The operator selected `check_motion` false in the run-root `MAKE-OPTIONS.json`, so
no motion sweep, no operating animation and no independent motion review was run.
Motion is **unverified**, never passed. Nothing about assemblability, roof seating,
roof lifting or inlay seating is claimed from the evidence in this product. The
roof-lift state in `snap/signature.png` is an exact STEP of the roof translated
100 mm in +Z; it is a picture of a position, not proof that the part moves.

## D11. This product still makes no print-ready claim

Unchanged from the archive and for the same reason: `check_overhang` fails both
counters on its connected-region span proxy, the counters are frozen by this
correction, and so the sealed status stays `digitally-verified-not-print-ready`
with `print_ready_claim: false` and the signature review binds no print-gate
reports. `part_base`, `part_inlay` and `part_roof` pass both gates at a 0.4 mm
nozzle. Part II section 1 below carries the full measurement, and
`measure/bridge-audit.json` carries the physical free-bridge numbers.

## D12. The five characteristics the host scoped out

None of these is attempted here. All are carried forward from the archive's
disclosures, unchanged:

1. The open perimeter reveal, 4.000 mm, through which an inlay can leave but a
   counter cannot. See Part II section 6, first bullet, and C6.
2. The 32 inlays are gravity-seated with no retention. See C6.
3. The Sun mark reads as a cog. The commissioner has seen it and kept it. See C13.
4. The two orientation marks sit one cell off the board centreline. They are tangent
   to a rank-8 square and do not cut into it; that was measured. See C14.
5. The dome is a solid hemisphere and stays one. It is not hollowed, shelled or
   lightened, and it is not raised as a question.

## D13. Wish tension, carried forward unchanged

The frozen Wish for the published set says "English draughts between two comet
streams". An earlier correction removed the comets in favour of the Sun and the Moon
and this revision continues that. The Wish is hash-bound and has not been edited,
rewritten or re-summarised. The revision no longer matches the Wish wording, the
change was host-directed, and the mismatch is not evidence that the correction
failed.

---

# Carried forward: the Periastra Meridian geometry notes

Everything from here to the end of the file is the previous revision's
`GEOMETRY-NOTES.md`. It is carried forward unchanged apart from the single
sentence in section 6 that the correction brief required to be marked superseded.
Inside it, "Part I" means revision C and "Part II" means the archive that revision
C corrected; those labels are historical and are not renumbered.

---

# Geometry notes, deviations and limitations

Everything here is measured, not assumed. Each item names the tool or the script
that produced the number.

This file has two parts. **Part I** records revision C, the correction in front
of you. **Part II** is the note set carried forward verbatim from the archive
being corrected; it is history and is not rewritten. Where revision C changes a
fact stated in Part II, section C10 says so explicitly.

---

# Part I — revision C: centred yoke, inlaid board

Two defects are corrected and nothing else in the object moves.

## C1. The yoke arms were both 4.000 mm off centre

### The cause, stated plainly

`periastra_lib.py` built the pair with two hand-written offsets:

```python
arm_face = Plane.YZ * Polygon(*arm_profile(), align=None)
arms = Pos(ARM_INNER_X,0,0)*extrude(arm_face,amount=ARM_THICK) \
     + Pos(-ARM_INNER_X-ARM_THICK,0,0)*extrude(arm_face,amount=ARM_THICK)
```

Both offsets are written for an extrusion that runs from x = 0 to x = +4. It
does not. build123d takes the extrusion direction from the **face normal**, and
the face normal follows the **winding order** of the polygon. `arm_profile()`
returns its points in the order that makes the normal point at -x, so
`extrude(arm_face, amount=4.0)` spans x = -4.000 .. 0.000. `Pos(+5)` therefore
landed the arm at [+1, +5] instead of [+5, +9], and `Pos(-9)` landed the other at
[-13, -9] instead of [-9, -5]. Both moved by exactly one `ARM_THICK`.

The consequences were real, not cosmetic. Arm A ended at x = -9.0 while the tube
began at x = -7.5, so it never touched the telescope: a lone 4 mm fin standing
beside it. Arm B lay entirely inside the tube's own x range and carried the
telescope by itself, off its centreline. The object had a one-armed mount.

### The construction that now makes it impossible

```python
one = extrude(arm_face, amount=ARM_THICK)
one = Pos(ARM_INNER_X - one.bounding_box().min.X, 0, 0) * one
arms = one + mirror(one, about=Plane.YZ)
```

The arm is placed by its **measured** bounding box rather than by an assumption
about which way it grew, and the second arm is a mirror of the first. Whatever
the winding order does, the pair is symmetric about x = 0 by construction and the
inner face lands on `ARM_INNER_X`. The reason is written into the source as a
comment beside the code.

### Measured, on the built STEP, before and after

`measure/check_fit.py` imports `part_roof.step` and slices it on a horizontal
plane at three heights inside the slit and below the tube. The "before" column is
the same measurement run against the archive's `part_roof.step`
(`157a1fee7b99...`) under `revision-work/`.

| slice | arm A, before | arm B, before | arm A, after | arm B, after |
|---|---|---|---|---|
| z = 18 | -13.000 .. -9.000 | +1.000 .. +5.000 | **-9.000 .. -5.000** | **+5.000 .. +9.000** |
| z = 25 | -13.000 .. -9.000 | +1.000 .. +5.000 | **-9.000 .. -5.000** | **+5.000 .. +9.000** |
| z = 32 | -13.000 .. -9.000 | +1.000 .. +5.000 | **-9.000 .. -5.000** | **+5.000 .. +9.000** |

Slit walls are at x = -15.000 and x = +15.000 on every slice.

| requirement | measured |
|---|---|
| clear air, arm A to its slit wall | 6.000 mm |
| clear air, arm B to its slit wall | 6.000 mm |
| clear gap between the arms | 10.000 mm, centred on x = 0.000 |
| each arm's overlap with the tube's x range (-7.5 .. +7.5) | 2.500 mm, fused |

Nothing else about the yoke changed: same profile, same `ARM_THICK` 4.0, same
pier, same keel, same strap, same tube, same 35 degree elevation, same muzzle.

### The symmetry gate — the test that would have caught this

`measure/check_fit.py` now cuts `part_roof.step` against its own mirror image
about x = 0 and fails the build if the leftover volume reaches 1 mm3. This is the
real gate: every telescope frame in the previous evidence set was oblique, and at
an oblique angle a fin beside the tube looks like an arm cradling it.

| roof | volume | asymmetric volume (one direction) | as a fraction | two-sided total |
|---|---:|---:|---:|---:|
| archive `157a1fee7b99...` | 985625.9 mm3 | **8987.8055 mm3** | **0.9119 %** | 17975.6111 mm3 |
| this revision | 986005.2 mm3 | **0.0000 mm3** | **0.0000 %** | 0.0000 mm3 |

The one-direction figure is the one the correction brief quoted (8987.8 mm3,
0.91 %); both readings are given so the number cannot be mistaken for the other
convention. After the repair the roof is exactly mirror-symmetric: the boolean
residue is zero, not merely small.

## C2. The board now uses the house tiled-board fit layer

`references/tiled-board-baseline.md` from the Mara Masque inventor skill was read
before any board dimension was fixed, as that skill requires. The clauses relied
on, and every default overridden, with the reason:

| quantity | baseline | this board | carried or overridden |
|---|---|---:|---|
| pocket opening | "Pocket opening — 42 mm — same as the square" | **22.0 mm** | **Carried.** The opening equals the playing square, which here is `CELL` 22.0. |
| inlay | "Inlay — 41.5 mm — undersized against the pocket"; "Total straight-edge clearance — 0.5 mm — 0.25 mm per side when centred" | **21.5 mm** | **Carried UNSCALED.** 0.5 mm total is a fit tolerance, not a proportion; shrinking it with the square would be wrong. |
| pocket depth | "Inlay thickness — 2.6 mm — surface height minus backing floor" (5.0 surface over 2.4 backing) | **2.0 mm** | **Overridden.** The baseline's depth is set by its 5.0 mm playing surface over a 2.4 mm backing. This board's floor is 11.0 mm, so depth is free; 2.0 mm is ten layers at 0.2 mm, enough to seat the inlay without making the pocket a well. |
| inlay thickness | "so the inlay finishes flush" | **2.0 mm** | **Carried.** Flush is not optional — see C4's void figure. |
| backing floor | "Backing floor under each pocket — 2.4 mm — continuous; the pocket is blind, never a hole" | **9.0 mm** | **Carried with margin.** `FLOOR` 11.0 − 2.0. |
| corner chamfer | "Corner chamfer — 2 mm — on every inlay corner and every internal pocket corner" | **1.0 mm** | **Scaled with the square** (2.0 × 22/42 = 1.048, rounded to 1.0). Applied to every inlay corner and every internal pocket corner. |
| chamfers are structural | "Without them, diagonally adjacent dark wells meet at a shared vertical edge and the checkerboard mesh comes out non-manifold. The chamfers leave a material bridge at each junction and the mesh closes." | applied | **Carried.** `measure/check_fit.py` tessellates the built base and asserts the mesh is closed and manifold; see C4. |
| faceted, not circular | "Prefer faceted recesses to circular ones in small detail; they hold their shape at nozzle scale where a small circle degrades." | applied | **Carried.** This is why `SQUARE_CORNER` 1.5, a *rounding* that served the same bridging purpose, is replaced by a plan chamfer rather than kept. |
| count and retention | "Inlays are gravity-seated with no retention feature." | 32 separate inlays, gravity-seated | **Carried as the host chose.** No retention geometry was invented; the baseline states the limit of its own evidence and the host accepted the consequence. |
| clearance direction | "If yours are meant to stay put, that is a different design and needs its own evidence." | 0.25 mm per side, untightened | **Carried.** The fit was not tightened toward interference to stop the inlays falling out. |

`RECESS` 0.8, `SQUARE_BEVEL` 0.3 and `SQUARE_CORNER` 1.5 are gone. They were the
mechanism the fit layer replaces, and `measure/check_fit.py` asserts they are
absent from `periastra_lib.py` so they cannot creep back.

**Why geometry alone could not have fixed this.** The set is printed opaque, one
colour per part, and the evidence renderer shades from the surface normal alone
with no cast shadows and no ambient occlusion, so two flat horizontal faces at
different heights come out exactly the same tone. Only sloped faces, vertical
faces and outlines carry signal. A 0.8 mm recess with a 0.3 mm lip gave a seated
player one faint outline. The baseline's answer is not geometry: the dark squares
are separate parts in a contrasting filament, which `SKILL.md` permits in terms —
"Color alone is an acceptable way to identify sides, ranks, and other state."
The inlays are sealed `Color(0.12, 0.16, 0.32)`, a night-sky indigo against the
base's pale grey-blue `Color(0.72, 0.78, 0.81)`.

## C3. One baseline clause deliberately not used

The baseline says: "**At panel seams the corners open square instead.** Chamfering
there leaves thin tapering wedges that fail a fixed-nozzle wall-thickness check."

That clause is **not used here**, deliberately. It exists because Civic Skyline is
a 384 mm board quartered into 192 mm panels to fit a 220 mm bed. This board is a
single 176 mm playing field on a 190 mm base and has no seams at all, so there is
no seam corner to open square. Every pocket corner gets its chamfer.

## C4. The numbers the fit layer buys, measured on the built STEPs

All of these are asserted by `measure/check_fit.py`, which reads
`part_base.step`, `part_inlay.step` and `part_sun_counter.step`, not the source
that made them.

**VOID.** The inlays finish flush, so they consume **zero** of the storage void.

| quantity | measured |
|---|---:|
| board floor, measured at a light cell | z 11.000 |
| pocket floor, measured at all 32 dark cells | z 9.000 |
| roof-seat ledge top | z 21.000 |
| storage void | **10.000 mm** |
| counter height, measured on `part_sun_counter.step` | 7.000 mm |
| clear above a stored counter | **3.000 mm** |

**FLUSH.** Pocket floor 9.000 + inlay thickness 2.000 = 11.000, against a board
floor of 11.000. Flushness error **0.000 mm**, against a 0.05 mm allowance.

**FIT.** Pocket opening 22.0 against an inlay measured at 21.500 across:
**0.250 mm per side**. Pocket depth measured at **2.000 mm** on **9.000 mm** of
continuous backing, against the baseline's 2.4 mm minimum. Every pocket is blind:
subtracting the built base from a 176 × 176 × 9.0 slab leaves nothing.

**PLACEMENT.** The void through the board at mid-pocket depth was compared, as a
boolean residue, against the exact union of 32 chamfered 22.0 mm prisms at the
grid centres. Residue **0.000000 mm3**: exactly 32 pockets, exactly at the cells
satisfying `(file + rank) % 2 == 0`, nothing else cut. a1 is dark and h1 is
light, the identity the baseline says to check.

**SEAT.** The counter is 20.0 mm across and sits on a flat inlay top. The chamfer
line stands **14.4957 mm** from the inlay centre — (21.5 − 1.0)/√2 — against the
counter's **10.000 mm** radius, so the chamfer is nowhere near it. Proved as a
boolean rather than as arithmetic: a Ø20.0 × 2.0 cylinder subtracted from the
built inlay leaves **0 mm3**.

**BRIDGE.** At each diagonal junction two chamfered pocket corners face each
other. Measured across the junction on the built base with a 0.02 × 0.2 mm probe:
**1.414 mm**, which is 2c/√2 at c = 1.0. See C5 for the disclosure.

**MESH.** The built base tessellates to 2580 triangles forming a closed,
manifold, consistently wound shell: every directed edge appears once and every
edge has its opposite. This is the baseline's stated reason for the chamfers, and
it is checked rather than assumed.

## C5. Deviation from the set's 3 mm minimum feature rule

The 1.414 mm diagonal bridge is below the 3 mm minimum feature width the rest of
this set observes. It is disclosed here with its reasoning and its measured
number, and it was not engineered away.

It is **not a freestanding feature**. It is a ridge 2.0 mm tall fused along its
whole length to a continuous 9.0 mm slab — nothing that can snap off, and nothing
a slicer has to bridge. `check_thickness` passes `part_base` at a 0.4 mm nozzle;
1.414 mm is about 3.5 extrusion widths.

The baseline's own gate-passed product carries the same detail at 2c/√2 = 2.828 mm
on a 42 mm square. Scaled to this 22 mm square that is 2.828 × 22/42 = **1.482 mm**,
so 1.414 mm is **4.55 % under** the baseline's own proportion. The whole of that
shortfall is the chamfer being rounded from 1.048 down to 1.0.

The correction brief's fallback, if it will not print, is to raise the chamfer,
and there is room: the seat calculation above shows c could go to 7.36 mm before
the chamfer line reached the counter's 10.0 mm radius, and c = 1.048 alone
restores the baseline's proportion exactly. That headroom is recorded here so the
next revision does not have to rediscover it. It was not taken now because 1.0 mm
is the brief's stated intended value and the measured bridge clears the nozzle
minimum by a wide margin.

## C6. One disclosed limitation, deferred by the host: the open reveal and the loose inlays

These two facts are recorded together because they are one problem.

- **The perimeter reveal is open.** The base wall drops to z 17.000 along the four
  side spans, retaining z 24 corner piers, and the roof plate underside seats at
  z 21.000. Measured on the built base, the reveal is **4.000 mm** tall and runs
  right round the perimeter.
- **The 32 inlays are loose.** They are gravity-seated with no retention feature,
  2.000 mm thick, and 2.000 mm is less than 4.000 mm. Tip the closed box and the
  inlays can leave through the reveal.
- A **counter** cannot. Its smallest dimension is its 7.000 mm thickness, against
  a 4.000 mm reveal, so no counter passes through it in any orientation. That is
  the measurement, and it is stated here rather than softened: the loss on tipping
  is the inlays, and the counters stay in.

Closing the box would resolve both at once. **The host scoped this out of this
revision and it was not attempted.** `LEDGE_TOP` and `SILL_TOP` are untouched.
Civic Skyline, whose fit layer this is, does not self-store and never had to
answer this; Periastra does, and this is the answer it currently has.

## C7. Part count before and after

| | archive | this revision |
|---|---:|---:|
| geometry families (print entries) | 4 | **5** |
| printed objects | 26 | **58** |
| `groups/observatory.json` part keys | `base`, `roof`, `single_01..12`, `forked_01..12` | the same 26, plus `inlay_01..inlay_32` |

`measure/revision_diff.py` asserts that every archive part key is still present
and that the only additions are the 32 inlays.

## C8. The counter hashes, asserted and unchanged

The two counters are finished and come out of this revision byte for byte
identical to the archive:

| part | sha256 | verdict |
|---|---|---|
| `part_sun_counter.step` | `262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b` | **unchanged** |
| `part_moon_counter.step` | `588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e` | **unchanged** |

`measure/check_fit.py` asserts both on every run and fails the build if either
moves. The crescent, the sun, the rim band, the field depth, the symbol relief,
the tip fillets and `COUNTER_DIAMETER` were not touched. For reference, the two
parts this revision does change hashed `157a1fee7b99...` (roof) and
`590aa6c78a84...` (base) in the archive; both are expected to move and do.

## C9. Motion is unverified for this revision

The immutable run-root `MAKE-OPTIONS.json` has `check_motion: false`. No motion
sweep, no motion manifest, no operating animation and no independent motion
review were run. Motion is **unverified, never passed**. Nothing here claims the
roof is assemblable, that it seats, or that the inlays seat. The roof's 0.8 mm
per-side lateral clearance and the inlays' 0.25 mm per-side clearance are
algebraic and boolean fit results from `measure/check_fit.py`, not motion results.

## C10. What this revision changes in Part II

Part II is kept verbatim. Two of its statements are superseded by revision C and
are listed here rather than edited out of the history:

- **Part II section 6, second bullet** ("The board has no colour contrast… the 32
  dark cells are distinguished by a 0.8 mm recess in a single-material print") is
  the defect this revision corrects. The dark cells are now 32 separate inlays in
  a contrasting filament; see C2.
- **Part II section 6, first bullet** describes the closed box as retaining its
  contents. That remains true of the counters and is re-measured in C6, but it is
  now incomplete: the inlays this revision adds are thinner than the reveal and
  can leave through it. C6 is the current, complete statement.

Everything else in Part II still holds. In particular Part II section 1 — the
counters' `check_overhang` span-proxy failure and the resulting
`digitally-verified-not-print-ready` status with `print_ready_claim: false` — is
unchanged, because the counters are frozen and could not be altered here even if
it were wanted. Revision C adds two print entries to that table:

| part | gate | verdict |
|---|---|---|
| `part_base` (rebuilt with pockets) | overhang, thickness | PASS |
| `part_inlay` (new) | overhang, thickness | PASS |
| `part_roof` (rebuilt with the centred yoke) | overhang, thickness | PASS |
| `part_sun_counter`, `part_moon_counter` | thickness | PASS |
| `part_sun_counter`, `part_moon_counter` | overhang | **FAIL**, unchanged and disclosed |

Because two printable parts still fail a print gate, **this product makes no
print-ready claim**, its sealed status stays
`digitally-verified-not-print-ready`, and the signature review binds no
print-gate reports.

## C10b. One re-measured diagnostic number

`measure/bridge_audit.py` is a diagnostic script, not a gate: it approximates the
crescent's filleted outline with shapely erode/dilate buffers to find the largest
circle that fits inside the unsupported field floor. Re-run in this environment
it reports the Moon counter's unsupported area as **108.59 mm2** where the
archive recorded **112.08 mm2**. The counter's STEP is byte-identical
(`588d285baf2e...`, asserted), the free bridge is unchanged at 9.75 mm, the Sun
counter's figures are identical to the archive's, and both gate verdicts are
unchanged. The difference is in the script's own polygonal approximation of the
0.45 mm tip fillets, not in the geometry. Both numbers are recorded here rather
than one being quietly replaced.

## C11. On the isolated-component gate

Every one of the five print entries was given its own isolated `make_round`
review-and-fix loop. `base`, `inlay` and `roof` pass theirs outright.
`sun_counter` and `moon_counter` pass build, wall and visual inspection and fail
only the `check_overhang` span proxy described above, so their component rounds
are recorded as failed. The assembled-object round was therefore run **without**
`--require-component-passes`: that flag's precondition cannot be satisfied
without changing counter bytes this correction freezes. The failure is reported
unchanged at component level, at assembly level and in the product's sealed
status. No threshold was lowered and no gate was skipped.

## C12. The evidence set, and the two frames section C of the brief required

Every frame the archive carried is regenerated here from the new geometry and
none is removed; `cad/render_family.py` is the frame table, so the set is
reproducible rather than assembled by hand. The brief required two additions in
the FIRST review round, because both of the defects it corrects survived the last
review only for want of a frame that pointed at them:

- `snap/roof/slit-plan_el90.png` and `snap/roof/slit-plan-close_el90.png` —
  straight down on the roof, the second cropped to the slit at about 21.7 pixels
  per millimetre. The blind critic was asked directly whether the mount is in the
  middle of the slot or off to one side.
- `snap/board/empty-plan_el90.png` and `snap/board/populated-plan_el90.png` —
  the whole board, empty and set out, at 1800 px. An unprimed critic was asked
  whether the playing surface is chequered and to point out the squares.

Neither requirement was allowed to be matched on an oblique frame or a close-up.
Two further added frames, `board/empty-oblique_az-45_el35.png` and
`board/populated-oblique_az-45_el35.png`, and a close crop
`board/inlay-seat_az-60_el22.png`, carry the seated-player angle and the joint
between an inlay and its pocket.

**One evidence repair was made after the blind read, and no geometry moved with
it.** The critic found that `board/populated-plan_el90.png` at 1200 px was
byte-identical to the carried-forward `playing/top_el90.png` and therefore added
nothing. Both board plan frames were re-rendered at 1800 px, which is what "at
whole-board scale" was asking for. The part STEPs, `snap/iso.png` and
`snap/signature.png` are byte-identical to the ones read blind.

## C13. A divergence between the frozen sun counter and its reference art

The independent critic, measuring pixels rather than reading the source, found
that the Sun counter's eight wedges do not have the proportions drawn in
`ref/ref-02-ref-2-sun-face.png`. It is right, the divergence is real, and it is
recorded here rather than argued away — but it is **not a change this revision
made**, and this revision is forbidden to close it.

**The part did not move.** Three independent facts:

| evidence | archive | this revision |
|---|---|---|
| `part_sun_counter.step` sha256 | `262ccc86f6e4c403…afe5f3b` | **the same bytes** |
| `snap/counters/sun-plan_el90.png` sha256 | `245bd93d86cd36f9…` | **byte-identical image** |
| `snap/counters/sun-oblique_az-90_el22.png` | `017525622497d206…` | **byte-identical image** |

The archive carries its own renders of its own counter, made by the same renderer
at the same cameras. Not one pixel differs. The renderer is therefore removed
from the question entirely.

**What actually differs.** From the source, the wedges run from radius 4.25 to
radius 6.25 — a radial length of 2.00 mm — and are 1.8 mm wide at the inner end
and 2.2 mm at the tip, so about 2.0 mm mean width. Aspect **1.0 : 1**, a square
nub. The critic measured 0.93 : 1 off the render, which is the same number within
its error. `ref-02` draws its rays at roughly **2.8 : 1**: long, slim and
strongly tapered, spanning the field. It is stylised reference art with soft
lighting, gradients and a textured ground, not a render of the CAD, and the built
part has never matched it in that respect — in the archive or here.

**Why it is not closed here.** The brief freezes the counters twice over: by
sha256, and in words — "Do not touch the crescent, the sun, the rim band, the
field depth, the symbol relief, the tip fillets, or COUNTER_DIAMETER." Restoring
the reference art's ray proportion means changing the sun, which breaks the
byte-identity the same brief requires. The two cannot both be satisfied, and the
brief resolves it itself: the hashes are the binding requirement, and the
references are "shown so you can confirm the counter you must not touch."

Recorded with the critic's numbers for whoever commissions the next revision:
at matched disc scale the archive's reference ray measures about 46 x 130 px
against the built part's 75 x 70 px, and the dimensionless ratio of wedge radial
length to island radius is 1.0 in the reference art against 0.55 in the part.

## C14. Two inherited blemishes this revision is not permitted to touch

Both were found by the independent critic on this revision's own frames, both are
unchanged from the archive, and both are outside the two defects the brief names.
"Nothing else in this object may move," so neither is repaired.

- **The two orientation marks sit one whole cell off the board centreline.**
  `STAR_X` is 22.0, which is a file boundary one 22 mm cell to the right of the
  board's own centre at x = 0. Measured on the solid, each mark is a **raised**
  half-disc 0.8 mm proud spanning y 88.0 to 91.0, and the board field ends at
  y 88.0, so a mark abuts the edge of its rank-8 square along a line and does not
  cut into the playing surface. At 1800 px the offset is unmistakable; the
  critic's reading of it as a 2.7 mm bite out of a square is a tangency at that
  resolution. They appear on the top and bottom margins only.
- **The yoke's foot block projects outboard of the drum face and terminates in
  raw untreated flats,** visible in `snap/roof/three-quarter_az-135_el28.png`.
  The pier, its y extent and the keel are all on the brief's frozen list; only
  the arms' x position was permitted to change. The critic recorded it as a
  non-blocking caveat: the one part of an otherwise clean corrected assembly that
  still looks like stock rather than a designed detail.

## C15. The five print designs are byte-reproducible; the combined assembly is not

Measured, because the archive's README made a reproducibility claim and this
revision had to check whether it still holds and how far it reaches.

**It holds for everything that gets printed.** Exporting the whole delivery twice
in succession reproduced all 58 production STEP files byte for byte, and the five
print designs regenerate to the same sha256 across runs — which is exactly why
the frozen-counter gate in `measure/check_fit.py` works at all.

**It does not hold for the combined `periastra.step`.** Three consecutive
`gen periastra.step.py --write --force` runs produced three different sha256 for
the same source and the same geometry. Diffing two of them: identical size,
identical line count, 787 differing lines, all of them in the STEP's
`STYLED_ITEM` / `OVER_RIDING_STYLED_ITEM` colour-assignment block. The colour
*content* is correct and stable — a census of the delivered assembly finds each
of the five colours exactly twice, and the delivered `assembled.step.json`
package assigns 32 indigo, 1 teal, 1 slate, 12 terracotta and 12 cream across its
58 occurrences — but the order in which cadgen emits those style entities varies
between runs.

This is a property of the toolchain's assembly styling, not of this source, and
it touches no printable part and no dimension. It is recorded so that a
byte-comparison of `assembled.step` against a fresh rebuild is not mistaken for a
geometry change. `parts/*.step` is the stable per-part record, and
`groups/observatory.json` seals all 58 of those hashes.

---

# Part II — notes carried forward from the archive being corrected

Kept verbatim. See C10 for the two statements revision C supersedes.


## 1. The product makes no print-ready claim

`check_overhang` **fails** both counters. It is not a build failure and it is not
a wall failure; it is the gate's span proxy.

| part | gate | span proxy | allowance | verdict |
|---|---|---|---|---|
| `part_base` | overhang, thickness | — | — | PASS |
| `part_roof` | overhang, thickness | 7.9 mm bridge | 12 mm | PASS |
| `part_sun_counter` | thickness | — | — | PASS |
| `part_sun_counter` | overhang | 13.7 mm | 12 mm | **FAIL** |
| `part_moon_counter` | thickness | — | — | PASS |
| `part_moon_counter` | overhang | 13.7 mm | 12 mm | **FAIL** |

The unsupported region is the field floor of the face that lies on the bed: the
flat annulus from the raised symbol at Ø12.5 out to the field wall at Ø14.0, plus
the bay inside the crescent. It is connected all the way round, so the gate's
proxy — the smaller plan dimension of the whole connected region — reports the
full field diameter, 14.0 mm as designed and 13.7 mm as tessellated.

`measure/bridge_audit.py` measures the physical number, the largest circle that
fits inside that unsupported region, which is the longest straight run of
filament with no supported material under either end:

| part | gate span proxy | real free bridge | unsupported area |
|---|---|---|---|
| `part_sun_counter` | 14.0 mm | **2.40 mm** | 89.3 mm2 |
| `part_moon_counter` | 14.0 mm | **9.75 mm** | 112.1 mm2 |

The physical number is the free bridge, and both are inside the 12 mm allowance.
The counter has not been redesigned around the proxy: the 0.75 mm of clear field
between the symbol and the field wall is a requirement of the correction, and it
is what makes the region connected. The honest consequence is recorded rather
than engineered away — the sealed product status is
`digitally-verified-not-print-ready`, `print_ready_claim` is `false`, the
signature review binds no print-gate reports, and nothing in this product calls
itself print-ready.

## 2. The crescent's horn rounding is 0.45 mm, not the 0.9 mm the brief named

This is a deliberate, measured departure from a number in the correction brief,
made under the brief's own instruction to verify every number before building and
to preserve, above all, the two conditions it named: the crescent stays slim, and
its horns wrap past the middle.

The two circles that draw the crescent meet at a **27.13 degree cusp**. A tangent
fillet of radius R in a cusp of angle A consumes R / tan(A/2) of horn along each
flank — 3.74 mm at R = 0.9. Built at 0.9 mm and then measured on the profile the
CAD actually extrudes:

| built rounding | surviving area | wrap | horn tip at |
|---|---|---|---|
| none (sharp outline) | 37.85 % | 232.7 deg | x = +2.77 |
| **0.45 mm (built)** | **36.95 %** | **206.6 deg** | **x = +1.36** |
| 0.90 mm (as the brief named) | 34.11 % | 178.6 deg | x = **-0.07** |

At 0.9 mm the horns stop just short of the middle and the shape spans 178.6
degrees. That is the 180 degree banana the host rejected on sight, reproduced
exactly. The brief's own "resulting wrap 233 degrees" and "horn tips at (+2.78,
+/-5.60)" describe the sharp outline before any fillet, and its "1.8 mm rounded
nose" is that fillet's chord; the two cannot both survive.

0.45 mm is the smallest rounding that still works, and the limit is not
arbitrary: the correction also requires a 0.3 mm 45 degree bevel round the top of
every raised island, which needs 0.6 mm of nose before it can be cut at all. At
0.25 mm the part **fails to build** — the chamfer operation throws. At 0.45 mm
the nose is 0.88 mm across, it carries its bevel, and `check_thickness` passes
the part at a 0.4 mm nozzle.

Nothing else about the crescent moved. The belly was not thickened, the two
circles were not changed, the horns were not shortened by any other means, and no
tip is cut square. Measured cost against the sharp outline: 26.1 degrees of wrap
and 0.90 points of area. `measure/crescent-metrics.json` and
`snap/counters/moon-symbol-notes.md` carry every number.

## 3. The 0.88 mm horn noses are below the set's 3 mm minimum feature width

This is the deviation the correction brief disclosed and accepted, at a smaller
size than it expected — 0.88 mm rather than 1.8 mm, for the reason in section 2.
They resolve as about 2.2 extrusion widths at a 0.4 mm nozzle. They are the
tapering ends of a raised band 1.5 mm tall that is fused to the disc along its
whole length: not a standing wall, not a cantilever, and nothing that can snap
off. `check_thickness` passes `part_moon_counter` at 0.4 mm with 0.0 % of its
surface below the 0.80 mm limit. The brief's fallback was to raise the fillet to
1.2 mm; that was not taken, because it moves in the wrong direction — a larger
fillet eats more horn, and 1.2 mm would leave roughly 165 degrees of wrap.

## 4. Motion is unverified

The immutable run-root `MAKE-OPTIONS.json` has `check_motion: false` for this
run. No motion sweep, no motion manifest, no operating animation and no
independent motion review were run. Motion is **unverified, never passed**.
Nothing here claims that the roof is assemblable, that it seats, or that any
mechanism works. The roof seats by gravity on four ledges with 0.8 mm of nominal
lateral clearance per side; that clearance is an algebraic fit result from
`measure/check_fit.py`, not a motion result.

## 5. Nothing physical has been tested

Digital verification only. No physical print, tactile fit, strength, durability,
comfort, discoverability or human playtesting has occurred. Playtest was not run
for this Spark route. Renders are appearance evidence; they cannot establish a
dimension, a clearance or a successful print.

## 6. Two open characteristics inherited from the unchanged base

The correction requires the base to come out byte-identical, so neither of these
was touched, and neither is a defect introduced by this revision. Both were
raised by the independent reviewer and are recorded rather than argued away.

- **The closed box is not sealed, but it does retain its contents.** The base
  wall drops to z17 along the four side spans, retaining z24 corner piers, and the
  roof plate seats at z21, so an open reveal runs round the perimeter through
  which the stored counters are visible. That is the published set's deliberate
  sightline. The independent reviewer read it as a spill risk and said the
  question was one measurement: reveal height against counter thickness. Measured
  on the solid, the reveal is **4.0 mm** and a counter is **7.0 mm** thick and
  20.0 mm across, so no counter can pass through it. `measure/check_fit.py`
  asserts that. The box is open to the eye and closed to its contents.
- **The board has no colour contrast.** The 32 dark cells are distinguished by a
  0.8 mm recess in a single-material print, not by colour, so the chequer pattern
  is quiet at a distance.
  **SUPERSEDED.** This has been untrue since the inlays landed. The 32 dark cells
  are 32 separate inlay parts printed in a contrasting filament and finishing
  flush with the board floor; the recess mechanism this sentence describes no
  longer exists. See section C2 of this file. This is the only edit made to the
  inherited notes.

## 7. Render limitations

`render_review` applies deterministic flat shading with no ambient occlusion.
Where the top of a raised symbol and the top of the rim band are coplanar — which
is exactly what the correction requires — a straight-down frame gets no shading
difference between them, so the plan frames understate the relief and, for the
crescent, reduce it nearly to an outline. **The oblique frames are the evidence
for relief and step height; the plan frames are not offered as proof of
legibility on their own.** The dome and the disc rims are visibly faceted in the
renders; that is the renderer's tessellation, not the geometry. The delivered
STEP is exact.

## 8. Wish tension, already disclosed

The frozen Wish for the published set says "English draughts between two comet
streams". The previous correction removed the comets in favour of the Sun and the
Moon and this correction continues that. The Wish is hash-bound and has not been
edited, rewritten or re-summarised. The revision no longer matches the Wish
wording, the change was host-directed, and the mismatch is not evidence that the
correction failed.

## 9. Crowning has one honest shortage

A player crowns by stacking one of their own captured counters on the promoted
piece, which is how an ordinary draughts set works. A position exists in which a
player reaches the far row before any of their counters has been captured, and in
that position the set supplies nothing to stack. It is uncommon but it is real.
The host chose to keep the set at twelve a side rather than add spares. The
game's rules, powers, probabilities and legal choices are unaffected; what is
affected is the token, and players resolve it as they would with any twelve-a-side
set.
