Verdict: FAIL `mask_disc_a`'s 3mm underside relief pocket leaves the entire 171mm-diameter window track floating 3mm above the bed, attached only at the outer rim — 22,740mm2 of dead-flat 0deg overhang that cannot print without supports.

# Printability review — armillary

Lens: does this print in practice on a Bambu Lab P2S. Gate numbers
(watertight, one body/part, bed envelope, overhang %, bridge span) are taken
as given and are not re-litigated. What follows is measured off the exported
STLs in `project/armillary_parts/` in each part's **as-modelled** orientation
— the orientation the brief's print plan tells the customer to use — plus the
per-part renders.

Method: per-part facet classification. `bed_contact` = down-facing facets at
the part's own z-min. `flat ceiling in air` = facets with normal within ~18deg
of straight down sitting above z-min, i.e. horizontal roof with nothing under
it. `sloped` = everything between.

| part | bed contact mm2 | flat ceiling in air | sloped |
|---|---|---|---|
| plinth_ring | 30991 | 126 @ z=30 | 7369 (45deg skirt) |
| mask_disc_a | **6608** | **22740 @ z=3** | 0 |
| mask_disc_b | 29161 | — | 0 |
| mask_disc_c | 29130 | — | 0 |
| star_tile | 200 | 176 @ z=1.2 | 0 |
| moon_tile | 157 | 218 @ z=1.2 | 0 |
| void_tile | 213 | 163 @ z=1.2 | 0 |
| reserve_column | 4244 | — | 0 |
| score_rail_tri | 3900 | 139 @ z=6.0 | 0 |
| score_rail_square | 3900 | — | 226 (45deg) |
| score_rail_penta | 3900 | 94 @ z=3.53 | 0 |
| score_rail_hex | 3900 | — | 160 (60deg) |

## Blocking — `mask_disc_a`

`parts/mask_disc.py::make_mask_disc(..., undercut=True)` cuts a full annular
pocket, `circle(track_r).circle(bore_r).extrude(3.0)`, out of the **underside**
of the window track. `track_r` is 98mm and `bore_r` is 12.5mm, so the cut
removes every bit of material from z=0 to z=3 across an 85.5mm-wide annulus.
The STL confirms it: `mask_disc_a` has z-levels {0, 3, 6, 9}, and the only
material touching the bed is the 10mm-wide outer rim band plus the paddle tab
— 6,608mm2, versus 29,161mm2 for the otherwise identical `mask_disc_b`.

The physical consequence: printed rim-down, as the brief instructs ("Print
flat, rim-down, windows as plain vertical through-holes — no supports"), the
printer lays a 10mm-wide ring, goes up three millimetres, and then at layer
~15 is asked to start a 3mm-thick, 171mm-diameter plate in mid-air. It is not
a bridge — there is no second anchor to bridge *to*; the interior is a
cantilevered roof over open air, 85mm of unsupported reach from the rim inward
toward a bore that has no material below z=3 either. The first perimeter drops
onto the plate and the print becomes spaghetti within a few layers.

Flipping the part does not help: the track sits at z=3..6 inside a rim that
spans z=0..9, so the geometry is symmetric about its mid-plane — turn it over
and you get exactly the same 3mm void, now on the other face. The only
orientations that avoid it are on-edge (a 216mm disc balanced on a 9mm-wide
line contact, which will not survive the first toolhead acceleration) or
supported (dense supports under nearly the whole disc, whose scarred underside
is the bearing face that slides on `mask_disc_b`).

There is also a knock-on: the undercut leaves `mask_disc_a`'s bore only 3mm
tall where it rides a 40mm axle, and reduces the working part of the disc to a
3mm membrane 171mm across pierced by six 38mm holes, rotated by a rim paddle.
Even if it were printed with supports it would flop visibly in hand.

The fix is orientation, not geometry: cut the knob-clearance relief into the
**top** face of `mask_disc_a`'s track instead of the bottom (or, better, raise
the rim band on one side only so the relief is an upward-facing recess). A
3mm-deep upward pocket over the same annulus is a plain vertical cut, prints
with no supports, keeps the full 216mm bed footprint, and clears the resting
knob just as well since the disc's clearance requirement is on its underside
gap, which is what a raised rim gives you.

## Non-blocking findings

**`score_rail_tri` and `score_rail_penta` end finials print in air.** The
finial is built on a YZ workplane and translated to `z = rail_h / 2 = 10`
(`parts/score_rail.py::_finial`), so its cross-section is centred 10mm up
rather than sitting on the bed. For the triangle the flat base lands at z=6,
for the pentagon at z=3.53 — 139mm2 and 94mm2 of horizontal surface,
cantilevered 10mm off the rail's end face with no anchor at the far end. These
are small enough that the part will still complete, but the first finial layer
will droop into visible strings and the "tell the rails apart by shape" cue
gets mushy on exactly two of the four. The square and hex finials happen to
present 45deg and 60deg faces and are fine. Dropping the finial's z-centre so
its lowest point lands on the bed (or sinking it into the rail body) removes
this entirely, and would make all four rails consistent.

**Tiles are fine, including the face-down relief.** 30 tiles at 15mm tall on a
~200mm2 footprint (a 2mm rim ring plus the motif island) is a modest adhesion
margin but not a risky one at 22mm diameter and low height; there is no lever
arm. The 1.2mm ceiling over the relief pocket is a genuine bridge, but the
longest span is ~6mm radially (star, rim r=9 to motif inner r=3.2) at 1.2mm
height — routine. The moon crescent's horns taper to a knife edge below one
extrusion width and will round off into small blobs; cosmetic on a face-down
motif, and the crescent body is 4.4mm at its thickest so the symbol stays
readable. The 16-flute knurl is a 0.7mm-deep scallop on a solid 10mm boss, not
a freestanding rib — nothing to snap. Losing one tile of thirty does not kill
the game.

**Warping.** No part is the thin-wide-plate signature. `mask_disc_b`/`c` are
216mm across but 6mm thick with a 9mm x 10mm rim band acting as a stiffening
hoop, and 29,000mm2 of bed contact; `plinth_ring` is a 30mm-tall drum on a
200mm-diameter face. Both are well past the thickness where corner lift
matters.

**Adhesion / tipping.** `reserve_column` is the only tall part: 150mm on a
4,244mm2 base (70mm square less the bore and slot), aspect ~2.1, tapering
inward 4.6deg from vertical. That is a stable, self-supporting print. The
`plinth_ring` skirt chamfer is a symmetric 45deg — the 7,369mm2 in the sloped
column is entirely that chamfer, and 45deg prints clean.

**Piece count.** 39 parts, 30 of which are the same 22mm tile. Each is a
stubby solid; none has a feature that can shear off in a bag. The count is a
print-time problem, not a print-failure problem.
