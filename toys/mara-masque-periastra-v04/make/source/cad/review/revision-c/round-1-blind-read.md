# Revision C, review round 1 — blind read

One independent critic. It was given the fourteen canonical image paths below and
**nothing else**: no Wish, no correction brief, no concept, no README, no source,
no dimensions, and no name for the object. It was instructed not to search the
filesystem for any specification and not to read anything but the images. It was
told only how the renderer shades (surface normal only, no cast shadows or
ambient occlusion, so colour differences between parts are real and tone
differences across one curved surface are lighting).

Images read, all under `cad/snap/`:
`iso.png`, `signature.png`, `closed/az0_el8.png`, `playing/iso.png`,
`playing/top_el90.png`, `board/populated-plan_el90.png`,
`board/empty-plan_el90.png`, `roof/slit-plan_el90.png`,
`roof/slit-plan-close_el90.png`, `roof/side-on_az0_el6.png`,
`roof/three-quarter_az-135_el28.png`, `counters/sun-oblique_az-90_el22.png`,
`counters/moon-oblique_az-90_el22.png`, `kings/board_az-90_el45.png`.

The two frames this correction brief required in the FIRST round are in that set
and were asked about directly, as questions G and H, before anything was
revealed: the straight-down frame cropped to the slit at about 25 pixels per
millimetre, and the populated and empty board at whole-board scale.

This transcript is recorded before the reveal and is not edited afterwards.

---

## A. Held object

> A small palm-sized draughts set in a lidded tray, where the lid is a model
> astronomical observatory — a domed roof with a slit and a telescope in it.

## B. Volumetric form

> Three stacked volumes. At the bottom, a shallow square tray with plain vertical
> walls and four L-shaped posts standing up at the corners… Inside it, a flat
> square board plate, essentially the full inner footprint, a couple of
> millimetres thick. On top, a flat square lid plate of the same footprint…
> Sitting centrally on that sheet is the dominant mass: a hemispherical dome
> about 76 mm across and 41 mm tall (very slightly taller than a true
> hemisphere), standing on a thin skirt/collar ring of slightly larger diameter
> that gives one crisp reveal line around its foot. The dome is 80% of the plate
> width… A rectangular trough with a cylinder in it breaks out of the dome's
> lower flank and projects outward past the silhouette.

(The critic calibrated its millimetres off the stated 25 px/mm of the close-up
crop, which applies only to that one frame, so its absolute sizes are about half
the true ones. Its proportions are correct.)

## C. Subjects

> 1 tray/box, grey, with 4 integral corner posts. 1 board plate, pale grey-blue,
> carrying **32 dark blue chequer tiles**. 2 shallow half-round scoops in the
> board's pale margin… 1 lid plate, teal. 1 dome shell, teal, with 1 slit cut
> through it… 1 tube (telescope/barrel) with a bored, thick-walled mouth. 1
> mount, consisting of 1 flat triangular fin and 1 rectangular pedestal block.
> 24 counters: 12 orange "sun" counters (8 raised blocks in a ring around a
> central boss) and 12 cream "moon" counters (a single raised crescent). In the
> kings render… kings are made by stacking two counters.

## D. Action

> signature.png shows the lid coming off: frame 1 closed, with the dome sitting
> on the box and the edges of the counters showing through a slot around the rim;
> frame 2 with the dome-and-plate lifted clear and hanging above, exposing the
> set-up board; frame 3 the open tray alone. So the object does one thing: it
> opens. The dome lid lifts off vertically to reveal a ready-set 12-a-side
> draughts game.

## E. Relationship

> The tray carries everything. The board plate lies in the bottom of the tray;
> the 32 blue tiles are set into it as very shallow pockets; the counters rest
> loose on top of the tiles… the lid is held proud of the tray rim, so there is a
> continuous open slot right around the perimeter through which the outer rank of
> counters is plainly visible… The dome stands on the lid plate via its skirt
> ring, dead centre. Inside the dome, a rectangular pedestal block stands on the
> lid plate at the foot of the slit; a flat triangular fin rises from that block;
> the tube rests on the fin and pokes out through the slit.

## F. Anti-generic signature

> The telescope. It is a real, separate, bored tube on its own plinth and fin,
> sitting inside the dome and breaking out through the slit — you can see the
> annular mouth and the bore hole from three-quarter and iso views. Combined with
> sun-versus-moon counters instead of plain red/white discs, that is the one
> thing that stops this being "a draughts box with a dome on it".

## G. DIRECT QUESTION ONE — "is the mounted thing in the middle of the slot, or off to one side?"

> **Across the slot's width it is dead centre, not off to one side.** Measured:
> the slot's cut edges are at x = 403 and x = 796 in slit-plan-close; the tube
> spans x = 436 to 762. That leaves 31 px of clearance on the left and 34 px on
> the right — the tube's centreline is at 599, the slot's at 599.5, i.e. centred
> to within 0.04 mm. The same holds in the wide view: the dome's centreline, the
> slot's centreline and the tube's centreline all land on x = 600.
>
> What I see either side of it: a narrow flat strip of identical tone and
> identical width on both sides… At the far end of the slot there are two small
> hard black rectangles, one each side of the tube's rounded top, **symmetric to
> within a pixel**.

It also observed, correctly, that the tube occupies only the outer 43 % of the
slot's *length*, the rest being open sky through the slit.

## H. DIRECT QUESTION TWO — "is the playing surface chequered? point out the squares"

> **Yes, it is an 8 × 8 chequer.** There are **32 dark blue tiles** in the
> standard alternating arrangement (4 per rank, offset rank to rank), within a
> grid… perfectly square and perfectly centred on the plate, with an equal margin
> on all four sides.
>
> They read as squares by **colour**… There are no light squares as separate
> parts: the other 32 cells are the continuous pale plate. Each dark tile has a
> corner cut and a small gap on every side, so diagonally adjacent dark tiles
> never touch at their corners.

## I. Desirability

> Half-finished. The idea is genuinely good and I would want the finished version
> — an observatory that opens into a draughts game is a strong object, and the
> sun/moon counters earn their place. But as rendered I would not buy it.

## J. Defects, most serious first

The critic listed fifteen. They are reproduced in full in
`round-2-reveal-and-comparison.md`, where each is classified against what this
revision was permitted to change.

1. Spout silhouette — the telescope and its trough break out of the dome's lower
   flank and read as a teapot spout from `roof/side-on_az0_el6.png`.
2. Unresolved pedestal at the foot of the slit.
3. The two half-round orientation scoops on the board are one whole cell off the
   board centreline and clip a first-rank dark tile.
4. The slit is 57 % empty along its length.
5. Counters are 91 % of the square pitch.
6. The sun motif reads as a cog: eight identical extruded blocks placed around a
   circle without being rotated.
7. The moon motif reads as a letter C, and shares no design language with the sun.
8. Chequer geometry: no light squares as parts, corners cut, a gap on all sides,
   and (its pixel estimate) a very shallow pocket.
9. The lid does not close the box — an open slot right round the perimeter.
10. Coincident-surface artefacts at the dome/drum seam.
11. Faceting on the dome and the tube bore.
12. The telescope reads as a cannon or mortar, not an instrument.
13. Two unexplained black tabs at the closed end of the slit.
14. No edge treatment on the plates or tray.
15. Weak signature sequence: frames 2 and 3 of `signature.png` differ only by the
    lid, and `playing/top_el90.png` duplicates `board/populated-plan_el90.png`.

It closed: "Nothing is floating unsupported, nothing is missing from the piece
count (12 v 12, 32 tiles, all correctly placed on the dark cells), and the board
grid itself is exactly square and exactly centred — those are clean."
