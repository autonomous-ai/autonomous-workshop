# Antisol — design contract

Dou Shou Qi, unchanged, played with the eight planets ranked by their real
measured diameters. Matter faces antimatter, and you win by walking one of your
worlds into the rival sun.

Provenance tags, one on every line that carries a hard millimetre:
`[observed]` is a measured fact — a real-world value, a value read off the
sealed reference images, or a dimension measured on the exact CAD solids or
reported by a deterministic gate; `[inferred]` is derived from an observed
value by the arithmetic stated here; `[assumed]` is a build decision this
project made and is answerable for.

## 1. What the rules need from the plastic

The source game is Dou Shou Qi, traditional Chinese, public domain, taken from
the Leiden rules page. Nothing is added, removed or altered. Every row below is
a restatement of a rule already in that source; the right-hand column is what
the plastic does about it, and in every case the answer is "shows", never
"enforces". **Nothing in this set makes an illegal move physically impossible.**

| rule | physical expression |
|---|---|
| Two players, eight pieces each | Sixteen worlds, eight per side |
| One orthogonal step | Every land cell is flat field inside an engraved 1.20 mm grid groove; all sixteen pieces seat on all of them [assumed] |
| Equal or higher strength captures | Strength is globe diameter and the seven-segment numeral. Read, never enforced |
| Only the Rat may enter the water | **Not enforced by geometry.** Every belt tile carries a flat Ø26.00 landing pad level with the field, and any piece will sit on it |
| Lion and Tiger leap the water | Saturn and Uranus. Unchanged, unenforced |
| A piece in an opponent's trap has strength 0 | Trap cells are corona wells: a tile floors the terrain pocket and leaves a 3.00 mm well, so a trapped piece sits 3.00 mm lower than on open ground [assumed] |
| Win by entering the opponent's den | The den plug stands 2.20 mm proud of the field on a flat top face; a piece seats on it exactly as on any land cell, one step higher [assumed] |
| Win by eliminating all opposing pieces | Empty tray |

## 2. The measurement system

### 2.1 Globe diameter = fifth root of real equatorial diameter

    globe_diameter_mm = 13.785 * (D_planet_km / 4879) ** 0.2

The exponent is exactly 0.2000. Equatorial diameters are `[observed]` NASA
planetary fact-sheet values; axial tilts are `[observed]`; every millimetre
below is `[inferred]` from them.

| rank | planet | D km | globe Ø | globe centre Z | seat land Ø | total height | axial tilt |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Mercury | 4,879 | 13.78 | 9.89 | 10.36 | 16.78 | 0.03° |
| 2 | Mars | 6,779 | 14.72 | 10.36 | 11.12 | 17.72 | 25.19° |
| 3 | Venus | 12,104 | 16.53 | 11.27 | 12.60 | 19.53 | 177.36° |
| 4 | Earth | 12,742 | 16.70 | 11.35 | 12.73 | 19.70 | 23.44° |
| 5 | Neptune | 49,244 | 21.89 | 13.95 | 16.96 | 24.89 | 28.32° |
| 6 | Uranus | 50,724 | 22.02 | 14.01 | 17.06 | 25.02 | 97.77° |
| 7 | Saturn | 116,460 | 26.00 | 16.00 | 20.30 | 29.00 | 26.73° |
| 8 | Jupiter | 139,820 | 26.97 | 16.49 | 21.09 | 29.97 | 3.13° |

Derivations, all `[inferred]`:

- `globe_centre_Z = 3.00 + globe_Ø / 2` — the globe is sunk 2.00 mm into a 5.00 mm disc. [assumed]
- `seat_contact_Ø = 0.7431 * globe_Ø` — the seat cone springs from latitude −42.0°.
- `seat_land_Ø = seat_contact_Ø + 2 * (0.3309 * R − 2.00) * tan(12°)`.
- `total_height = 3.00 + globe_Ø`.

**Height ladder strictly increasing: 16.78 → 29.97 mm, measured on the built [observed]
solids.** The widest object on the board is Saturn's ring at Ø30.00, which is
3.87 mm narrower than its own disc; no piece overhangs its own base. [assumed]

### 2.2 The twins

Venus and Earth differ by 0.17 mm of globe diameter, Uranus and Neptune by [assumed]
0.13 mm. They are separated by three redundant channels that cost no invented [assumed]
data: the seven-segment numeral at 0° and 180° on the disc wall; the surface
markings; and the filament colour.

## 3. Ownership: parity inversion

Ownership never touches a planet's own appearance. It lives in three places:

1. **Lean direction.** Every marking pattern is rotated about the +Y axis by
   that planet's true obliquity. Sol worlds lean their north pole toward +X,
   Anti-Sol worlds toward −X. On Saturn the ring leans with it, and that is a
   silhouette cue; on the other seven the lean is carried by the colour pattern.
2. **Disc taper.** The Sol disc flares outward as it rises, Ø33.00 at the bed to
   Ø34.00 at the top of the wall. The Anti-Sol disc tapers inward, Ø34.00 to
   Ø33.00. Both draft at 6.5° from vertical, and both measure Ø33.87 at their
   widest once the 0.60 mm top round is taken. [inferred]
3. **Disc colour.** Sol `white` with a `black` numeral; Anti-Sol `black` with a
   `white` numeral — the widest lightness separation the palette allows, and
   every disc is read against the `dark_gray` field.

## 4. The board

Field: 7 files (a–g) x 9 ranks (1–9) at 36.00 mm pitch = 252 x 324 mm. Board [assumed]
268 x 340 x 9.00 mm including an 8.00 mm border, `dark_gray`. [assumed]

- **Dens** `[observed, Leiden]`: d1 and d9.
- **Traps** `[observed, Leiden]`: c1, d2, e1 and c9, d8, e9.
- **Belt** `[inferred]`: files b–c and e–f, ranks 4–6.
- **Opening setup** `[inferred]`: Saturn a1, Uranus g1, Earth b2, Mars f2,
  Mercury a3, Neptune c3, Venus e3, Jupiter g3; mirrored 180° for Anti-Sol.

**The field is flat and the grid is cut into it.** Every boundary between two
land cells, and the field perimeter beside a land cell, is a 1.20 x 0.60 mm [assumed]
square-bottomed groove centred on the boundary — three extrusion widths at a
0.4 mm nozzle, leaving 8.40 mm of floor under it. Depth is reserved for terrain. [assumed]

**Every terrain pocket is the same blind 6.00 mm hole**, 34.80 mm across in the [assumed]
open and 34.40 mm across where one of its edges lands on a panel seam; only [assumed]
what drops into it differs. A pocket edge on a seam is inset 1.00 mm instead of [assumed]
0.60 mm, so each panel owns a wall it can print: 0.60 leaves each panel half a [assumed]
rib, and half a rib is under the 0.80 mm wall floor at this nozzle. The board's [assumed]
thinnest material is the 1.20 mm rib between two adjacent pockets inside one [assumed]
panel; across a seam the two panels together part their pockets by 2.00 mm. [assumed]

**Panel split** — 268 x 340 mm exceeds a 200 mm bed, so the board is cut after [assumed]
file c and after rank 4:

| panel | size mm | contains |
|---|---:|---|
| `panel_southwest` | 116 x 152 | files a–c, ranks 1–4; trap c1; belt b4, c4 |
| `panel_southeast` | 152 x 152 | files d–g, ranks 1–4; den d1; traps d2, e1; belt e4, f4 |
| `panel_northwest` | 116 x 188 | files a–c, ranks 5–9; trap c9; belt b5, b6, c5, c6 |
| `panel_northeast` | 152 x 188 | files d–g, ranks 5–9; den d9; traps d8, e9; belt e5, e6, f5, f6 |

## 5. The asteroid belt

One geometry, twelve parts, one tile per cell, so the cell lines survive across
the water. `belt_cell` is 33.50 x 33.50 x 6.00 mm, `cocoa_brown`, four-fold [assumed]
symmetric about its own centre, dropping into the pocket with 0.25 mm per [assumed]
side where that pocket's edge lands on a panel seam and 0.65 mm where it does [assumed]
not: one tile size is cut for the tightest pocket in the set, so it enters
every pocket and rattles a little in the open ones.
Its rubble is a field of forty-eight faceted boulders, radius 1.60 to 2.60 mm, [assumed]
standing on a floor 2.00 mm below the field datum. No rock touches another and [assumed]
none of them ends in a point: every one is a flat-topped frustum, kept clear of
tangency with its neighbours, with the landing pad and with the tile's own edge
by 0.35 mm. Measured on the built tile, nothing reaches above the field datum [assumed]
at all, and the four crests that reach it exactly are in the plane of the
smooth Ø26.00 landing pad at the tile's centre, which is itself flush with the [assumed]
field — so a seated disc rests on 532.9 mm² of coplanar contact and cannot [observed]
rock. `measure/belt-pad-coplanarity.md` records the measurement.
**The belt is a picture of an exclusion, not an enforcement of one.**

## 6. The star and its corona

Dou Shou Qi already puts three cells around every den. That ring is the corona:
the rule that a piece standing there has strength 0 is the star stripping a
world of its rank, and on this board you can see why.

### `den_plug` — the star, the one component marked `signature`

A 36.00 mm flange standing 2.20 mm proud of the field — the highest ordinary [assumed]
surface on the board — on a 33.50 mm spigot buried in the den pocket. The top [assumed]
face is flat, so a winning piece seats on it the way it seats anywhere else,
one step higher. Two tapered prominences rise from the two corners that face
the board border, leaning 12° outward, reaching 18.00 mm above the field. Each [assumed]
foot is Ø6.00 and the pair sits 20.80 mm apart on the flange diagonal, so the [assumed]
outermost lean falls 17.71 mm from the cell centre against an 18.00 mm flange [assumed]
half-width and each foot keeps 0.86 mm from the disc of a world seated on the [assumed]
den. Both constraints are met by the feet themselves, so the flames stand whole
and the part is exactly one cell square in plan. Hexagonal granulation is
engraved 0.40 mm into the four corners the seated disc never covers. Sol `sunflower_yellow` with `orange` flames; Anti-Sol `black` [assumed]
with `cyan`.

**What the hero costs, accepted in writing.** The two flames rise 18.00 mm at [assumed]
the board edge. From the seat opposite that den they stand between the eye and
the den cell's far edge. That is the seat attacking the den, and it is the
sightline the hero is paid for. No other component is permitted any of it: the
corona tongues are held to 4.00 mm above the field, 12.78 mm below the crown of [assumed]
the shortest globe in the set, so a corona cell can never occlude a piece.

### `corona_cell` — the trap, and the ring

Six parts, three per den, one geometry in three rotations. A 33.50 x 33.50 x
3.00 mm tile drops onto the floor of the terrain pocket, and the board's own [assumed]
pocket wall makes the 3.00 mm well above it, so a seated disc drops exactly [assumed]
3.00 mm below the field with slip on every side. Its face carries a star and [assumed]
sixteen radiating flame tongues, **engraved 0.40 mm** — raised relief under a [assumed]
seated disc would make a trapped piece rock, which is the one thing a corona
well must not do. Two tapered tongues rise from the two corners furthest from
the den, so every tongue points away from the star.

## 7. The worlds

Each world is a single printed part in several filaments: a disc, a numeral
inlaid flush in its wall, a globe on an integral seat cone, and the markings
that name the planet. No assembly, no fastener, no fit, nothing that can come
apart in play.

- **Disc** Ø34.00 x 5.00 mm, top edge rounded 0.60 mm, bottom edge left sharp [assumed]
  so the piece sits flat. Sol flares outward, Anti-Sol tapers inward, both at
  6.5°; neither presents a face shallower than 45° from vertical.
- **Numeral** — seven-segment digits 3.60 mm tall, 2.80 mm wide, 1.00 mm [assumed]
  stroke, at 0° and 180°, centred at Z 2.20, **inlaid flush 0.60 mm into the [assumed]
  wall** in the contrasting filament.
- **Globe** — a sphere at the ladder diameter, sunk 2.00 mm into the disc top [assumed]
  face, carried by an integral seat cone that springs from latitude −42.0° and
  spreads outward at 12° from vertical down to the disc face. The seat is
  material added around the globe's foot and finished in the globe's own
  colour. It exists because a sphere resting tangentially on a flat disc leaves
  an unsupported cap underneath it.
- **Markings** — flush colour inlays reaching 1.20 mm into the globe, described [assumed]
  in the planet's own frame by latitude, longitude and angular size, then
  rotated by that planet's true obliquity. Describing them as angles is what
  lets one minimum outline width hold from Mercury to Jupiter.

| planet | markings | filaments |
|---|---|---|
| Mercury | albedo plains | `dark_gray` on `gray` |
| Mars | dark albedo, both polar caps | `cocoa_brown`, `white` on `red` |
| Venus | the ultraviolet cloud Y, inverted with the planet | `orange` on `beige` |
| Earth | continents, dryland, northern ice | `green`, `beige`, `white` on `blue` |
| Neptune | the Great Dark Spot, white cloud streaks | `dark_gray`, `white` on `blue` |
| Uranus | one band, upright because the pole lies past horizontal | `white` on `cyan` |
| Saturn | four belts, the ring | `cocoa_brown`, `white` on `yellow` |
| Jupiter | six belts, the Great Red Spot | `cocoa_brown`, `red` on `orange` |

### Saturn's ring

A flat annulus in Saturn's equatorial plane, therefore leaning 26.73° from the
board — the one place in this set where the ownership lean is a silhouette cue.
Inner edge continuous with the sphere, outer Ø30.00, 1.40 mm thick, 3.87 mm [assumed]
inside its own disc on every side.

A tilted flat annulus presents an underside no printer holds unaided, so the
volume between that underside and the first material below it is filled by a
web whose own outer surface is held at 47° from horizontal. The web is thickest
at the ring's low azimuth, where it runs down to the disc, and thins to a
fraction of a millimetre at the high azimuth, where the globe already carries
the ring. **On the table the low side of Saturn's ring reads as thickened.
That is accepted**, and it is why the ring is Ø30.00 rather than Ø32.00: at a
3.00 mm projection the same web reads as a funnel rather than as a ring. [assumed]

## 8. Storage

`orbit_tray`: 164 x 88 x 6.00 mm, `gray`, printed twice, one per player. Eight [assumed]
blind sockets Ø34.40 x 3.50 mm on a 38.00 mm pitch, 4 x 2. Every socket is [assumed]
identical, because every disc is identical.

## 9. Colour

Thirteen filaments, all from one PLA stock, so the whole set prints in one
material family on one machine.

| filament | used for |
|---|---|
| `white` | Sol disc, Anti-Sol numeral, Mars caps, Earth ice, Uranus band, Neptune streaks, Saturn ring |
| `sunflower_yellow` | Sol den plug — the only part in the set that carries it |
| `black` | Anti-Sol disc, Anti-Sol den plug, Sol numeral |
| `yellow` | Saturn globe |
| `orange` | Sol flames and corona, Jupiter globe, Venus cloud Y |
| `cyan` | Anti-Sol flames and corona, Uranus globe |
| `dark_gray` | board panels, Mercury plains, Neptune dark spot |
| `cocoa_brown` | belt tiles, Mars albedo, Saturn bands, Jupiter bands |
| `gray` | Mercury globe, trays |
| `red` | Mars globe, Jupiter Great Red Spot |
| `beige` | Venus globe, Earth dryland |
| `blue` | Earth globe, Neptune globe |
| `green` | Earth land |

**One colour collision, stated rather than hidden.** Earth and Neptune share
`blue`. They are 5.19 mm apart in globe diameter, Earth carries `green` land [assumed]
and Neptune does not, and they carry different numerals.

## 10. Print stance and gate compliance

42 PLA parts, all flat at Z0; 0.4 mm nozzle, 0.2 mm layers, 200 mm bed, no [assumed]
supports, no hardware.

| gate | requirement | worst case in this set | how it was checked |
|---|---|---|---|
| minimum wall | 0.80 mm | 1.20 mm rib between two adjacent pockets in one panel | `check_thickness` on all 24 printed geometries [observed] |
| overhang | 45° from vertical | 48° where the globe meets its seat at latitude −42° | `check_overhang` on all 24 printed geometries |
| bed fit | 200 mm | 188 mm on `panel_northeast` | `check_fit` [observed] |
| widest object vs cell pitch | < 36.00 mm | Ø33.87 disc; Ø30.00 Saturn ring | measured on the built solids [observed] |
| height ladder strictly increasing | required | 16.78 → 29.97 mm | measured on the built solids [observed] |

Fits are derived, never typed twice: pocket = cell pitch − 2 x inset, tile =
pocket − 2 x 0.25 mm clearance, tray socket = disc + 0.20 mm per side. **There [assumed]
is no press fit anywhere in the set**, because there is nothing to assemble.

## 11. Changes this build made to the design it was handed

Each of these was forced by a deterministic gate, and each is recorded with the
measurement that forced it.

1. **The rank numeral is a flush colour inlay, not a 0.45 mm raised relief.** [assumed]
   A 1.00 mm seven-segment stroke standing 0.45 mm proud leaves a down-facing [assumed]
   ledge on a wall that drafts away beneath it; it cannot be chamfered to the
   45° gate at 2.80 x 3.60 mm without the segments merging. Flush keeps all [assumed]
   three rank channels and costs no ledge, and the sealed reference images read
   the numeral as flush colour.
2. **Surface markings are flush colour inlays 1.20 mm deep, not 1.00 mm relief [assumed]
   with 45° chamfered edges.** A raised patch on the lower half of a sphere
   presents a rim shallower than the gate allows. The consequence is recorded:
   the obliquity lean is a colour cue on seven of the eight planets rather than
   a silhouette cue, and ownership rests on disc colour, disc taper and the
   lean of the pattern. On Saturn the ring keeps the lean in the silhouette.
   Total piece heights therefore lose the 1.00 mm of relief: the ladder runs [assumed]
   16.78 → 29.97 instead of 17.78 → 30.97, and is still strictly increasing.
3. **The den plug stands 2.20 mm proud, not 1.00 mm.** Its flange skirt has to [assumed]
   draft off the spigot at more than 45° and still leave a vertical rim thicker
   than 0.80 mm; 1.00 mm of proud height leaves a 0.05 mm lip that [assumed]
   `check_thickness` measured as a 116 mm² wall.
4. **The star's granulation is engraved 0.40 mm, not raised 0.50 mm.** A grain [assumed]
   half a millimetre tall is thinner than the nozzle can hold as a wall.
5. **The corona tile is 33.50 mm square, not 35.50.** A 35.50 mm tile cannot [assumed]
   enter its own 34.80 mm pocket. The corona tongues moved with it, to Ø5.00 on [assumed]
   a 20.20 mm diagonal, which keeps 0.70 mm to that cell's own seated disc and [assumed]
   0.37 mm inside the tile edge. [assumed]
6. **Sixteen corona tongues starting 6.50 mm out, not twenty-four from the [assumed]
   centre.** Run in to the middle they merge into one blob whose boundary
   leaves 0.13 mm webs; a separate engraved disc stands in for the star they [assumed]
   radiate from.
7. **Saturn's ring is Ø30.00 with a 1.40 mm section, not Ø32.00 x 1.60.** The [assumed]
   Wish's own fallback, taken for the reason the Wish gives.
8. **Terrain pockets on a panel seam are inset 1.00 mm rather than 0.60.** [assumed]
   Measured: at 0.60 each panel carried a 0.50 mm wall, and `check_thickness` [observed]
   failed all four panels.
9. **The prominence feet are Ø6.00 on a 20.80 mm diagonal and stand wholly on [assumed]
   the flange, not Ø11.00 on a 23.40 mm diagonal cantilevered outside the [assumed]
   cell.** §7.2 says the part of each base that crosses the cell boundary
   floats above the field and that nothing needs to be under it. Built exactly
   as written, `check_overhang --angle 45` returns NEEDS SUPPORT: two
   unsupported regions of 53.3 mm² and 51.6 mm² at the two feet, each spanning
   10.5 mm with 9.2 mm of air below. The measurement is kept at [assumed]
   `measure/wish-7.2-flare-overhang.md`. Clipping the floating part back to a
   45° roof does print, but it cuts a straight face through every flame, and a
   blind reader given only the renders called that unresolved interpenetration
   rather than a finished moulding. Ø11.00 cannot be rescued by moving it: to
   stand on the flange the foot's outer edge must fall within the 18.00 mm [assumed]
   half-width, and to clear the disc of a world seated on the den its inner
   edge must fall beyond 17.44 mm — 5.5 mm of radius cannot satisfy both, and [assumed]
   the two conditions are 5.3 mm apart. Ø6.00 at 20.80 mm satisfies both at [assumed]
   once: outermost lean 17.71 mm, foot-to-disc clearance 0.86 mm. Cost: the [assumed]
   flames are slimmer than §7.2's Ø11.00, and the printed envelope is
   36.00 x 36.00 rather than the 44.10 x 40.10 §7.2 predicts. §16's
   instruction for this part — *increase the outward lean, do not shorten the
   flare* — is honoured: the 18.00 mm height and the 12° lean are untouched and [assumed]
   the taper is unbroken from foot to tip.

10. **Every marking longitude is chosen so the marking faces the camera; the
    Wish fixes latitudes only.** §8.4 gives the Great Red Spot as "at 22°
    south" and Venus's cloud Y as "laid out about a pole 2.64° from vertical
    pointing downward", and neither names a meridian — Jupiter turns in ten
    hours and this set fixes no prime meridian on any world. Built on the
    meridians the first draft happened to use, both features sat on the hidden
    hemisphere of both armies in every rendered view: measured against the view
    axis, the Great Red Spot scored −0.49 and −0.45 and Venus's Y scored −0.72
    and −0.68, and a blind reader given only the renders reported Jupiter as
    "banded belts" with no spot and Venus as "a slightly larger plain white
    ball", the only one of the eight it could not name. The spot was carried
    110° and the Y 135° around their own axes, which is free: after the shift
    the spot measures +0.44 / +0.62 and the Y +0.63 / +0.81 against the two
    frames the product is photographed from, on both armies. This is what §13
    asks for in so many words — Venus's "`orange` cloud Y breaks the outline" is
    a requirement of the frame, and it could not be met on the old meridian.
11. **The product image is rendered at the Wish's own fixed frame, 35° azimuth
    and 22° elevation (§13), not at a 45°/35° isometric.** §13's azimuth is
    measured off the rank axis, from the Sol end — that is what puts file a on
    the left and file g on the right along "the near back rank", and the near
    star in front. In this build's axes, where ranks run along Y, that is
    azimuth −55°. §13 designs the
    composition for that camera — "at 35°/22° the wells catch shadow and the
    tongues catch light", "the cut grid catches light along one wall of every
    groove" — and the low elevation is what puts the globes, rather than the
    board, in front of the eye. The three-state sheet stays at the higher
    isometric, because at 22° the far ranks foreshorten into each other and the
    three positions stop being separable.

12. **A marking's patches are clipped to the globe one at a time, not as a
    fused union.** `inspect validate` measured the earlier build's colour
    bodies as `selfIntersecting` on Mercury, Mars and Venus — ten occurrences
    in all. The cause was exact: a marking's outer face *is* the globe's own
    sphere, and intersecting a union of overlapping patch tools with that same
    sphere leaves a neighbouring tool's face running tangent to it along the
    seam where two patches meet. Clipping each patch on its own and fusing the
    lenses afterwards gives the kernel only well conditioned operands, and the
    result is then measured rather than assumed: the colour bodies themselves,
    not the region tools that made them, are tested for self-intersection, and
    the marking is widened by a graded fraction of a degree and retried until
    they pass. Every one of the sixteen worlds now passes on both armies. One
    visible consequence, and it is an improvement: Mars's polar caps are cut
    after its dark albedo is subtracted rather than before, so they measure
    16.65 mm³ instead of the 0.81 mm³ sliver the earlier order left. [observed]
13. **The belt's rubble is forty-eight disjoint flat-topped boulders, not a
    dense mat of a hundred and seventy-six overlapping ones.** `inspect
    validate` reported `invalidTopology` on all twelve belt tiles in the
    assembly package. Measured on the built tile: a face of 0.00034 mm² and an [observed]
    edge 1.2 micrometres long, made wherever two tapered prisms crossed at a [observed]
    shallow angle — which a taper guarantees, because two prisms overlapping at
    the base grow tangent on the way up. Twelve seeds were tried and every one
    produced slivers; `ShapeFix_Shape` and `ShapeUpgrade_UnifySameDomain` left
    them untouched, because the slivers are real geometry and not a tolerance
    artefact. Making the rocks disjoint removes the rock-to-rock boolean
    entirely: worst face 0.00090 mm², worst edge 0.0125 mm, face count 906 down [observed]
    to 248, and the whole 180-occurrence assembly now validates clean. Cost,
    stated: the belt reads as scattered rock rather than as a continuous
    crumbly mat.

## 12. What this run does not prove

No part of this run demonstrates physical printing, dimensional accuracy on a
real bed, material durability, tactile comfort, colour accuracy against real
filament, or human play. Motion verification is switched off for this run and
is recorded as unverified, never as passed. The clearances, wall thicknesses
and overhang margins above are geometric measurements on the exact CAD solids
and predictions for the printer named in `README.md`.
