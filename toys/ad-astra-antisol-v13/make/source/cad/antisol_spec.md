# Antisol Jove Mirror — design contract

Dou Shou Qi, unchanged, played with the eight planets ranked by their real
measured diameters. Matter faces antimatter, and you win by walking one of your
worlds into the rival sun.

*Jove* is Jupiter's older Latin name, and this revision is Jupiter's. It
finishes the correction items 26 and 27 began: Jupiter's two armies were the
same object photographed twice, measured and named as such by the previous
run's own reviewer and deliberately left in scope for a later brief. Section
11, item 28 is the correction; **nothing else in the set changed, and
`part_world_jupiter_sol` is not part of it and did not move.**

The section headings and item text below accumulate. Each correction adds its
own item and leaves the earlier ones as they stand rather than back-dating
them, so "this revision" inside an earlier item means the run that wrote it.
Item 26's closing paragraph says Jupiter is deliberately not in scope; item 28
is where that changed, and it supersedes that paragraph and nothing else.

Provenance tags, one on every line that carries a hard millimetre:
`[observed]` is a measured fact — a real-world value, a value read off a
reference image, or a dimension measured on the exact CAD solids or
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
| 6 | Uranus | 50,724 | 22.02 | 14.01 | 17.06 | 25.98¹ | 97.77° |
| 7 | Saturn | 116,460 | 26.00 | 16.00 | 20.30 | 29.00 | 26.73° |
| 8 | Jupiter | 139,820 | 26.97 | 16.49 | 21.09 | 29.97 | 3.13° |

¹ Uranus is the one world in the set whose ring, not its globe, is the highest
point. Its globe crown is at 25.02 mm like every other row's, and the [inferred]
upright hoop this revision added stands 0.96 mm above it. [inferred] Saturn's ring is a
near-horizontal plate and sits below its globe's crown, so its 29.00 needs no
footnote. The heights still climb with rank, all eight of them:
`measure/uranus-ring.md`.

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

Ownership lives in three places, and on six of the eight worlds none of them
touches the planet's own appearance:

1. **Lean direction.** Every marking pattern is rotated about the +Y axis by
   that planet's true obliquity. Sol worlds lean their north pole toward +X,
   Anti-Sol worlds toward −X. On Saturn the ring leans with it, and that is a
   silhouette cue; on the other seven the lean is carried by the colour pattern.

   **On three worlds the lean has nothing to give, and there the mirror is
   carried by the map instead.** Mercury's obliquity is 0.03°, Jupiter's is
   3.13° and Venus's is 177.36°, so their two pieces differ by 0.06°, 6.26°
   and 5.28° of lean — a mirror with nothing in it. Those three Anti-Sol
   pieces therefore carry the same features at the same latitudes arranged the
   other way round, reflected about that piece's own facing meridian, so that
   **every pair in the set reads as a pair**. The obliquities did not move,
   `lean_sign` did not move and `planet_frame` did not move; items 26 and 28
   are the whole of it, and `parts/markings.markings_for` is the one place it
   lives. It costs a mirror-image map on those three worlds and nothing else,
   and what is mirrored there is a longitude this project chose for its
   cameras rather than an observation it made.
   `measure/mirror-set-consistency.md` gives all eight worlds' obliquities and
   inter-piece angles beside the rule, so which three are mirrored can be
   checked rather than trusted.
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
sightline the hero is paid for. No other component is permitted any of it. That was
first written when the corona tiles carried two raised tongues, held to 4.00 mm [assumed]
above the field and 12.78 mm below the crown of the shortest globe in the set so [inferred]
that a corona cell could never occlude a piece. Item 27 removes those tongues on
the owner's instruction, so the rule now holds absolutely rather than by margin:
**nothing else on the board rises above the field at all**, and the star's two
flames are the only raised flames in the box.

### `corona_cell` — the trap, and the ring

Six parts, three per den, one geometry placed six times. A 33.50 x 33.50 x
3.00 mm tile drops onto the floor of the terrain pocket, and the board's own [assumed]
pocket wall makes the 3.00 mm well above it, so a seated disc drops exactly [assumed]
3.00 mm below the field with 0.40 mm of slip on every side. Its face carries a [assumed]
star and sixteen radiating flame tongues, **engraved 0.40 mm** — raised relief [assumed]
under a seated disc would make a trapped piece rock, which is the one thing a
corona well must not do.

**And nothing else.** Two tapered tongues used to rise from the two corners
furthest from the den, so that every tongue pointed away from the star, and the
tile was placed in one of three rotations to keep them pointing that way. Item
27 removes them on the owner's instruction: the trap is now the tile and its
engraving and nothing more, its highest surface is the floor a trapped world
stands on, and with a sixteen-fold engraving on a rounded square it is the same
tile at any quarter turn — so the rotation is gone too. Its printed height is
3.00 mm, not 10.00. [assumed]

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
  in the planet's own frame in angles rather than millimetres, then rotated by
  that planet's true obliquity. Describing them as angles is what lets one
  minimum outline width hold from Mercury to Jupiter. **Uranus is no longer described at
  all**: it was one latitude band, then two polar hoods drawn as `cap` regions,
  and since this revision it carries no marking of any kind. It is the one
  world in the set with a bare globe. The measured case for the hoods is kept
  in full at item 23 and in `parts/markings.py`; item 25 records who overruled
  it. Saturn is described both ways, and so is
  Neptune: its clouds went from three closed latitude bands to eight short
  outline arcs and, in this revision, back to the three bands by owner
  decision, while its dark spot stays an outline oval
  (`parts/neptune_atlas.py`). Item 24 records the reversal and item 22 keeps
  the measured case it reversed.
  **Earth, Mars, Mercury and Venus are described entirely by outline**: a
  closed ring of longitude/latitude vertices per feature, taken from a stylised
  outline atlas (`parts/atlas.py` for Earth, `parts/mars_atlas.py` for Mars,
  `parts/mercury_atlas.py` for Mercury, `parts/venus_atlas.py` for Venus),
  swept into the globe as the radial cone through the ring and trimmed to the
  same 1.20 mm depth. [assumed]

  **Jupiter is the eighth and is described both ways**, and that split is
  itself a measurement rather than a preference. Its four narrow belts are
  plain bands of latitude, 5 to 7° wide. Its two widest — the South Equatorial [observed]
  at 13° and the North Equatorial at 10° — are outline rings carrying a 2.5° [observed]
  wave on each boundary, because an exact circle of latitude reads as a
  machined edge and only those two have room for a wave that does not close
  them; a belt encircles the globe and one radial cone cannot, so each is six
  60° longitude sectors abutting on exact radial planes. Its Great Red Spot and [assumed]
  the collar around it are outline ovals. Its five bright zones are the one
  region kind nothing else in the set uses, a constant-depth latitude shell:
  each is drawn wider than it is shown and trimmed by the belt beside it, so
  where the trim lands must not decide how deep the inlay is.
  `parts/jupiter_atlas.py` holds all of it and item 20 records why.

  Those four and not the others, because those four are the worlds in this
  set with a real mapped surface. Three of them carry a shape that can be
  checked against a picture — Earth's coastlines, the dark triangle of Syrtis
  Major which every telescope owner has drawn since 1659, and the long
  equatorial sweep of Aphrodite Terra — and drawing any of those as circles
  throws that recognition away. Mercury carries no such silhouette: its
  albedo boundaries are soft and its plains are unnamed, so nothing there can
  be checked against a shape anybody remembers. It earns outlines for the
  other half of the same argument. A union of discs does not merely lose a
  recognisable shape; on a Ø13.78 ball it reads as a beach ball, and terrain
  is the one thing it does not read as. The remaining ones keep their
  bands, and for a band system a belt of latitude is not a compromise but the
  honest shape. A storm is not a circle, though, and neither is a cloud.
  **Neptune left that group and this revision puts it back**: its three closed
  latitude bands became eight short tapered arcs, and the owner, shown both,
  prefers the bands and has reversed it. Item 22 carries the measured case for
  the arcs in full and item 24 records the reversal and who made it. Its dark
  spot does NOT go back: it stays the one oval twice as wide as it is tall,
  because two overlapping circles read as a smudge and that decision was not
  reversed. The bright companion cloud beside the spot went with the arcs and
  is not drawn. Jupiter's spot went the same way
  earlier: the real
  spot is 16,000 by 11,000 km on a planet 139,820 km across, which is 13° of [observed]
  arc by 9, so it is drawn as one oval half again wider than it is tall. Three
  overlapping circles, which is what stood there, read as a lozenge.

  **Venus alone in this set is drawn from radar rather than from what the eye
  would see.** Its surface is under an opaque atmosphere, so the only picture
  of it is the Magellan global radar mosaic, and the owner of the set chose
  that picture over the visible one deliberately: a cloud pattern and a
  surface map are two pictures of two different objects, and this world was
  to show the object the other seven show — the ball itself, not the weather
  over it. [assumed] Items 14, 16, 18 and 19 of section 11 record what each
  of the four cost at its own globe size. [inferred]

| planet | markings | filaments |
|---|---|---|
| Mercury | the smooth plains as outlines — seven lobed regions on the centres the round-patch build used, fusing into four; and the **Caloris basin** at latitude +30, longitude −50, 36° of arc across, built as a bright floor inside a rim annulus. The third of the three worlds drawn from outlines, not circles. No craters | `cocoa_brown`, `white` on `gray` |
| Mars | the classical albedo map as outlines — Syrtis Major's dark triangle, Mare Acidalium, Sinus Sabaeus and Meridiani, and the southern belt of Erythraeum, Sirenum, Cimmerium and Tyrrhenum; both polar caps, their rims broken by lobes. The second of the three worlds drawn from outlines, not circles | `cocoa_brown`, `white` on `red` |
| Venus | the Magellan radar surface as outlines — seven highland provinces led by **Aphrodite Terra**, the long equatorial sweep the piece is recognised by, and three lowland plains with the highlands subtracted out of them. The fourth of the four worlds drawn from outlines, and the only one drawn from radar. Inverted with the planet, as it was. No clouds, no cloud Y, no texture | `beige`, `cocoa_brown` on `sunflower_yellow` |
| Earth | continent coastlines, dry interiors, northern ice — the first of the three worlds drawn from outlines, not circles | `green`, `beige`, `white` on `blue` |
| Neptune | **three closed white latitude bands** — −46/−41, +11/+15 and +30/+33, so their widths run 5, 4 and 3° of arc, which on this Ø21.89 globe is 0.955, 0.764 and 0.573 mm, the narrowest band family in the set; each a plain `band` region, each running the whole way round the planet; and the **Great Dark Spot** at latitude −22 as one outline oval 28 by 14° of arc [inferred], unchanged by this revision. No companion cloud. The widest bare gap between two bands is 52° of latitude, 9.93 mm. `b1` at −46/−41 is south of the latitude the Sol piece's two product cameras can reach, so on that piece it is an Anti-Sol-only feature at those two frames and is shown on the per-world frames instead. `measure/neptune-atlas-resolution.md`, `measure/neptune-facing.md` | `dark_gray`, `white` on `blue` |
| Uranus | **nothing.** This world carries no surface marking of any kind: no hood, no cap, no band, no spot, no replacement in a quieter tone. Its globe is one undivided `cyan` sphere. It wore an upright `white` equatorial band, then a `beige` polar hood at each pole; the owner looked at the finished hoods and took them out, and the appearance of the toy is his to decide. A bare world is the right answer on this one: `ref/uranus-sol.png` is an almost featureless sphere — pale, very nearly uniform, with one faint soft-edged lighter region and no stripe anywhere in it — and what carries this piece's identity is the ring, the size and the `cyan`. The measured case for the hoods is kept whole at item 23; item 25 records the reversal. `measure/uranus-bare.md` proves on the solids that nothing survives on either globe. Plus the ring, which is geometry rather than a marking, did not move, and now prints in `white` — the set's default and Saturn's spool. No banding, no storms, no moons | nothing on `cyan` |
| Saturn | five bands at unequal widths and unequal spacing — +46/+55, +18/+33, +2/+10, −14/−30 and −38/−50, so their widths run 9, 15, 8, 16 and 12° — with the two widest drawn as outline rings carrying a 2.5° wave on each boundary and the other three as plain bands; four of the five in `sunflower_yellow`, the mid tone, and only the widest in `cocoa_brown`; and a bright `white` cap above +58 on the north only, an exact parallel with no lobed rim. **Lower in contrast than Jupiter's on purpose**: the reference's bands are soft-edged and barely darker than their neighbours, Saturn is the quiet planet next to Jupiter's loud one, and both stand on the board at once. Plus the ring, which is geometry rather than a marking and is unchanged by this revision. No hexagon, no storms, no ring divisions, no ring shadow | `sunflower_yellow`, `cocoa_brown`, `white` on `yellow` |
| Jupiter | six belts at their real, unequal latitudes — +38/+43, +24/+31, +7/+17, −7/−20, −27/−34 and −40/−46, so their widths run 5, 7, 10, 13, 7 and 6° — with the two widest drawn as outline rings carrying a 2.5° wave on each boundary and the other four as plain bands; five bright zones between and beyond them, the Equatorial the widest; and the **Great Red Spot** as one 13 by 9° oval at latitude −22 with a collar just outside it, the South Equatorial Belt bending 7° north around it. Poles above +46 and below −46 left bare | `cocoa_brown`, `beige`, `red` on `orange` |

### The two ringed worlds

**This set now has two worlds with rings, and the orientation is what tells
them apart.** A ring lies in its planet's equatorial plane, so the obliquity
this set already builds every world at decides what the ring looks like without
anyone choosing: Saturn leans 26.73° and its ring is a near-horizontal plate, a
brim projecting sideways past the globe; Uranus leans 97.77°, which stands its
equatorial plane 7.77° past vertical, and its ring is an upright hoop standing
over the globe. The two are not confusable in silhouette even before size
enters it, and size then separates them again — Ø30.00 against Ø24.02, with
Saturn still the widest world in the set. That is measured in
`measure/uranus-ring.md` and it is the reason rank 7 keeps the silhouette the
ladder gives it.

### Saturn's ring

**Unchanged by this revision, and that is a requirement of it rather than an
accident.** `RING_INNER_D` 26.00, `RING_OUTER_D` 30.00, `RING_THICKNESS` 1.40,
`RING_GLOBE_BITE` 1.00, `RING_WEB_SECTORS` 96, `RING_WEB_INNER_R` 5.00,
`RING_WEB_OVERLAP` 0.45, `RING_WEB_DROP` 0.30 and `RING_WEB_SLOPE` 1.08 are
all exactly where the published set left them. The ring is what
`LADDER_CONSTANT` was solved against and it carries the whole set's size
ladder, so moving it would reach far outside a surface correction. Because it
is a solid rather than an inlay, it is checked on solid count, exact volume and
bounding box in `measure/occurrence-geometry.md` rather than on colour alone.

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

### Uranus's ring

Geometry rather than a marking, recorded the way Saturn's is. Its constants
live in their own parallel block in `params.py` — `URANUS_RING_PROJECTION`
1.00, `URANUS_RING_INNER_D` 22.02, `URANUS_RING_OUTER_D` 24.02,
`URANUS_RING_THICKNESS` 1.00, `URANUS_RING_GLOBE_BITE` 0.80,
`URANUS_RING_FOOT_SLOPE` 1.08, `URANUS_RING_FOOT_REACH` 1.30 and
`URANUS_RING_FOOT_RISE` 1.50 — and Saturn's block above is untouched.

**Where it comes from is the owner, not the reference.** `ref/uranus-sol.png`
shows no ring. Every other requirement in this chain forbids inventing what the
reference does not show, and this one is an explicit owner instruction that
overrules an earlier version of its own brief. It is defensible on its own
terms — Uranus really does have thirteen narrow rings, too faint for the
reference image to carry — but it is recorded here and in the product's
limitations as an owner decision so that a later reader is not confused about
which rule applied.

A flat annulus in Uranus's equatorial plane, therefore standing 7.77° past
vertical: an upright hoop, not a brim. Inner edge tangent to the equator and
continuous with the sphere the whole way round, so no part of it bridges
unsupported air. Outer Ø24.02, 1.00 mm thick, 1.00 mm of projection per [assumed]
side — a little over half Saturn's 2.00, which is what "small" was asked for.
In plan it adds nothing: its greatest reach from the axis is 12.01 mm [inferred]
against the disc's 17.00, so the piece's footprint is the disc's and every fit
in the set is the fit it already was. In height it adds 0.96 mm and [inferred]
makes this the one piece whose ring, not its globe, is the highest point.

**The junction needed a wedge, and that is the whole difficulty of a small
upright ring.** Everything below the disc top is cut away, and a hoop meets
that flat cut on the steep part of its own curve: the rim leaves the disc at
48.6° from vertical and does not clear the 45° gate until Z 5.52, half a
millimetre higher. The smaller the ring the worse it is, because a smaller hoop
meets the disc plane further down its own curve. Growing the ring until the cut
lands somewhere shallower takes the projection to Saturn's own 2.00 mm [inferred]
and throws the instruction away, so the junction is wedged instead, at
`RING_WEB_SLOPE` 1.08 — 47.2° from horizontal, the angle this set already
trusts under Saturn's ring for exactly this problem. The wedge is a cone about
the piece's axis intersected with the ring's own plane slab, so it exists only
at the two feet and nowhere else; it stands 1.30 mm proud of the hoop [inferred]
where it leaves the disc and is gone 1.50 mm further up, inside the [inferred]
globe. **The
steepest downward-facing angle anywhere on the finished ring is 44.3°, at Z
5.68 and plan radius 8.66, and the 45° gate passes** — on the ring measured on
its own and on the whole printed part, which reports 0 unsupported regions and
0 bridges. `measure/uranus-ring.md` carries the sweep.

**The ring prints in `white`, and after this revision the set's rule that rings
are white holds without an exception for the first time.** Both ringed worlds
print their ring from the same spool, which is the value `RING_COLOUR` has
always held as the default.

It has not always been so, and the history belongs here because the second
change reverses the first. The Uranus edition took `white`, then moved off it
on a measured reading: `white` separates 38.9 of 255 luma levels from the [observed]
globe, louder than the hood's 27.8, which made the ring the loudest thing on a
piece that exists to be quiet; and an independent reader shown the board cold
named both Uranus pieces as tennis balls, twice, giving the mechanism in his
own words -- "a bold white curved line arcing down one side of a
saturated-colour ball, and a large pale panel on the opposite side". `gray` was
tried and measured worse in use: quieter as a number at 7.0 and a MORE
convincing seam to read, because a tennis seam is a dark curve on a bright
ball. So the ring was given the globe's own `cyan` and stopped being a marking
at all.

**The owner has reversed that.** The geometry did not move by a micron -- this
is one existing body changing spools -- and the reviewer's mechanism is worth
reading again before assuming the old problem is back, because it has two
halves and this revision removes one of them: after the hoods came off there is
no pale panel anywhere on the piece. Whether a white hoop ALONE on a bare
`cyan` ball still reads as a seam is a different question, and it is put to this
build's blind review unprimed rather than assumed in either direction; the
answer is recorded in `snap/SIGNATURE-REVIEW.json` beside the measured
separation, which `measure/uranus-ring-tone.md` puts at 38.7 to 39.3 luma [observed]
levels across the three canonical frames. `measure/uranus-ring.md` carries the
decision and what it costs. Saturn's ring is untouched and still prints
`white`.

## 8. Storage

`orbit_tray`: 164 x 88 x 6.00 mm, `gray`, printed twice, one per player. Eight [assumed]
blind sockets Ø34.40 x 3.50 mm on a 38.00 mm pitch, 4 x 2. Every socket is [assumed]
identical, because every disc is identical.

## 9. Colour

Thirteen filaments, all from one PLA stock, so the whole set prints in one
material family on one machine.

| filament | used for |
|---|---|
| `white` | Sol disc, Anti-Sol numeral, Mercury Caloris floor, Mars caps, Earth ice, Neptune's three cloud bands, Saturn ring and northern cap, **Uranus ring** |
| `sunflower_yellow` | Sol den plug, Venus globe, Saturn's four light bands |
| `black` | Anti-Sol disc, Anti-Sol den plug, Sol numeral |
| `yellow` | Saturn globe |
| `orange` | Sol flames and corona, Jupiter globe |
| `cyan` | Anti-Sol flames and corona, Uranus globe |
| `dark_gray` | board panels, Neptune dark spot |
| `cocoa_brown` | belt tiles, Mercury plains and Caloris rim, Mars albedo, Venus lowlands, Saturn's one dark band, Jupiter belts and spot collar |
| `gray` | Mercury globe, trays |
| `red` | Mars globe, Jupiter Great Red Spot |
| `beige` | Earth dryland, Venus highlands, Jupiter zones |
| `blue` | Earth globe, Neptune globe |
| `green` | Earth land |

**Two colour collisions, stated rather than hidden.** Earth and Neptune share
`blue`. They are 5.19 mm apart in globe diameter, Earth carries `green` land [assumed]
and Neptune does not, and they carry different numerals. This revision changed
Neptune's surface, so the pair was measured again rather than inherited:
`measure/neptune-earth-separation.md` renders the two side by side at the
product's own frame and answers on size, silhouette and surface separately.

Venus's globe and the Sol den plug now share `sunflower_yellow`. That is [assumed]
stated rather than accidental: the amber was chosen for Venus because it is
the closest thing the shop stocks to the Magellan mosaic's colour, and it was
preferred to a new spool precisely because the set already carried it. The two
are never confused — the den is a 36.00 mm square flange lying flat on [assumed]
the board with two 18.00 mm flames rising off it, and Venus is a Ø16.53 [assumed]
ball on a Ø34.00 disc — and the den plug never moves while Venus does.

One near-collision is worth the same sentence, and this revision makes it
tighter rather than looser. Venus's globe is `sunflower_yellow` #FFB549 and [assumed]
Saturn's is `yellow` #FFD834, which are neighbours in hue, and **since this
revision Saturn's four light bands are `sunflower_yellow` as well**, so the two
pieces are built out of the same two spools rather than merely similar ones.
That was measured after the change rather than predicted before it, and
`measure/venus-saturn-separation.md` answers it on three counts separately.
Size and silhouette carry it easily: 9.47 mm of globe diameter, a Ø30.00 ring [observed]
on one and nothing of the kind on the other, numerals 3 and 7, and at the hero
frame Saturn stands 36% the taller in pixels. **The surface does not, and that [observed]
is the weakest of the three cues and got weaker here.** What keeps the two
apart on surface at all is which way round the colours sit: Venus's globe is a
flat field of the amber with two small provinces on it, Saturn's is a lighter
ball wearing the amber as four soft stripes with a white cap over its north,
and white is the one tone Saturn has that Venus has nowhere.

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
   a 20.20 mm diagonal, which kept 0.70 mm to that cell's own seated disc and [assumed]
   0.37 mm inside the tile edge. The tile's size stands; the tongues do not — [assumed]
   item 27 removes them, and `CORONA_TONGUE_BASE_D`, `CORONA_TONGUE_H`,
   `CORONA_TONGUE_TIP_R` and `CORONA_TONGUE_DIAGONAL` are retired from
   `params.py` with them. 0.70 mm was the tightest clearance on that tile and [inferred]
   it is now a constraint the part does not have.
6. **Sixteen corona tongues starting 6.50 mm out, not twenty-four from the [assumed]
   centre.** Run in to the middle they merge into one blob whose boundary
   leaves 0.13 mm webs; a separate engraved disc stands in for the star they [assumed]
   radiate from. These are the ENGRAVED sixteen and they are untouched by item
   27 — count, inner radius, eye and 0.40 mm depth all unchanged. They were [assumed]
   never the horns the owner objected to.
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
    south" and named no meridian for it — Jupiter turns in ten hours and this
    set fixes no prime meridian on any world. Built on the meridian the first
    draft happened to use, the spot sat on the hidden hemisphere of both
    armies in every rendered view: measured against the view axis it scored
    −0.49 and −0.45, and a blind reader given only the renders reported
    Jupiter as "banded belts" with no spot. It was carried 110° around its own
    axis, which is free: after the shift it measures +0.44 / +0.62 against the
    two frames the product is photographed from, on both armies.

    Item 26 is downstream of this one and could not exist without it: because
    these longitudes are camera decisions rather than map facts, they are the
    thing on Mercury and Venus that a mirror can be taken from — and because
    they are camera decisions, the mirror has to be the one reflection that
    does not move them off the camera.

    Venus was carried the same way and for the same reason, and its number has
    since been taken twice. The first was −135°, chosen for the ultraviolet
    cloud Y §8.4 asked for. That pattern is gone — item 19 — and its offset
    went with it rather than being inherited, because a meridian chosen for a
    cloud pattern says nothing about where a surface map should sit. Venus now
    carries **+90°**, swept from scratch against Aphrodite Terra and measured
    in `measure/venus-facing.md`. Aphrodite is the feature the piece is
    recognised by; at +90 it scores +0.98 / +0.94 on the Sol world and +0.97 /
    +0.92 on its mirror, and every one of its 24 vertices is on the near
    hemisphere in all four cases. The old −135 scores −0.47 on the same test.
11. **The product image is rendered at the Wish's own fixed frame, 35° azimuth
    and 22° elevation (§13), not at a 45°/35° isometric.** §13's azimuth is
    measured off the rank axis, from the Sol end — that is what puts file a on
    the left and file g on the right along "the near back rank", and the near
    star in front. In this build's axes, where ranks run along Y, that is
    azimuth −55°. §13 designs the
    composition for that camera — "at 35°/22° the wells catch shadow and the
    tongues catch light", "the cut grid catches light along one wall of every
    groove" — and the low elevation is what puts the globes, rather than the
    board, in front of the eye. (Quoted as it was written. Since item 27 the
    only tongues on a corona tile are the sixteen ENGRAVED into its floor, and
    at 22° of elevation they are still what catches the light in a well; what
    is gone is the two that stood above it.) The three-state sheet stays at the higher
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

14. **Earth's surface is drawn from coastline outlines; the worlds that
    carry no recognisable outline stay round patches.** A blob union is honest
    for a band system, because that is what a band system is. (Written when
    Neptune's dark spot was the other example; item 22 records why it stopped
    being one.) It is not honest for Earth: at a glance a union of green and
    beige circles reads as a mottled marble rather than as the planet, and
    Earth is one of the worlds here whose outline a player already knows;
    Mars is the second and item 16 records it, Mercury the third at item 18
    and Venus the fourth at item 19. (Written when Earth was the only one, and
    left standing: at that point six worlds still carried patches, and three
    of those six have since earned outlines of their own.) The
    three Earth markings are now built from closed longitude/latitude rings —
    the Americas, Africa, Eurasia and Australia in `green`; the Sahara, the
    Kalahari, inner Asia, the American southwest and the Australian outback in
    `beige`, subtracted out of the land; the parallel at 72° plus seven ice
    lobes and Greenland in `white`. The ordering, the filaments, the 1.20 mm [assumed]
    depth and the subtraction structure are unchanged, and so is every
    dimension of the piece: the built `part_world_earth_sol.step` and
    `part_world_earth_anti.step` solids are byte-identical to the ones this
    build was handed, because a flush inlay partitions the same volume however
    its boundary is drawn. What changed is where the colour boundary falls.

    The tool is new and is the third region kind in `features/patches.py`. A
    ring becomes two planar sections square to the ring's own axis, one placed
    inside the 1.20 mm depth surface and one outside the globe, each vertex [assumed]
    contributing the point where its radial line crosses that plane; the two
    are lofted ruled. Both of a vertex's points sit on the same radial line, so
    each side of the loft is the plane through the globe centre and one ring
    edge — the lateral surface *is* the radial cone through the ring, and the
    shell arithmetic trims it to depth without the tool leaning anywhere. The
    globe's outer surface stays a true sphere, no wall of an outline tool is
    ever exposed, and nothing an outline adds can face downward, so the
    overhang-driven wall lean the source atlas was drawn for is not present
    here and was not added. The northern cap encloses the pole and so has no
    ring: it is the radial cone through the parallel at 72°, with the lobes and
    Greenland unioned onto it, because a bare cap ends on an exact circle of
    latitude and reads as a lid laid on the globe.

    What it cost at this size is measured in [observed]
    `measure/earth-atlas-resolution.md`. One degree of arc is 0.1457 mm on a [inferred]
    Ø16.70 globe and the nozzle is 0.40 mm, which is 2.74° of arc. Every ring [assumed]
    clears it: the shortest edge in the atlas is Greenland's at 0.49 mm and the [observed]
    narrowest neck is the same 0.49 mm, the tightest sea channel is the [observed]
    Mediterranean at 0.94 mm, and the Bering Strait and the Red Sea hold at [observed]
    1.43 mm and 1.21 mm. **One outline was simplified**: the Australian [observed]
    outback's north-west corner moved from (119°E, 20°S) to (121°E, 21°S),
    2.24° of arc and 0.33 mm here. As drawn it ran 0.14 mm inside Australia's [observed]
    west coast and left 1.17 mm of green strip too thin to print; moved, the [observed]
    narrowest green along it is 0.40 mm. The outback is an interior beige [observed]
    patch, so the silhouette a player recognises does not move at all. Nothing
    else was simplified and no landmass was dropped. What the supplied atlas
    never drew is listed separately in the same report, with a reason for
    each: Japan, New Zealand, the Indonesian and Philippine arcs, the British
    Isles as a shape of their own, the Mediterranean's islands, and
    Antarctica with it any southern ice. Most are narrower than the nozzle
    here; none of them is a silent drop.

    The cap is measured rather than looked at. [observed]
    `measure/earth-ice-cap.md` classifies points 0.10 mm under the sphere [assumed]
    against every colour body of the built world: above 72 degrees there is no
    ocean sample at any longitude, so the cap is solid all the way round, and
    the only thing reaching into it is `land`, which is what the subtraction
    order asks for. The dark channel a polar render shows near the date line
    is open water in the atlas itself -- lobe 4 ends at 176 east and lobe 5
    begins at 178 west -- and it closes at exactly 72 degrees where the cap
    starts. That channel is the point of the lobes.

    One consequence of the correction is worth stating because a reader meets
    it before anyone explains it. The two Earth pieces carry the *same* rings
    in the planet's own frame -- ownership never touches a planet's own
    appearance -- and what is mirrored between them is the lean. Photographed
    one at a time from the same camera, the Sol world therefore tips its north
    pole toward the lens where the Anti-Sol world tips it away, and the same
    Atlantic reads as two different framings. `snap/worlds/earth-pair-*.png`
    puts the two under one camera for that reason: side by side the inversion
    reads as the cue it is, and the continents read as the same continents,
    with the same handedness, on both armies. Mirroring the map itself would
    be the error -- one army would be wearing a reflected Earth.


15. **The colour split is accepted only when the topology checker accepts it,
    not only when it stops crossing itself.** `inspect validate` reports
    `selfIntersecting` and `invalidTopology` as separate findings, and they
    are separately reachable. The clip loop this build was handed asked only
    the first question, and one body slipped past it: Earth's Sol Africa lens
    came back with no self-crossing, no lost volume, and a topology the final
    gate refused, measured at 37.02 mm³ against the Anti-Sol mirror's 37.29 -- [observed]
    the difference is the disc's own cut, which the lean puts in a different
    place on each army, and where Africa's southern coast meets it at a
    shallow angle the split hands back a sliver. Both questions are now asked,
    of the same bodies, with the same two checkers the gate uses
    (`bool3d.invalid_topology`, `BRepCheck_Analyzer` with the gate's own flag).

    Widening a patch cannot move a marking off that configuration, because the
    disc's cut is a plane through the piece and stays where it is however wide
    the patch is drawn: all eight widenings failed. So the retry gained a
    second axis, `_CLIP_SPINS`, which turns the whole marking frame a fraction
    of a degree about the planet's own axis. The largest of them is 0.23°, [assumed]
    which on the smallest globe in the set is 0.03 mm of arc -- a seventh of [inferred]
    one extrusion width. Nothing the eye can find, and enough to move the
    boundary off a configuration the kernel answers badly.

    One consequence, stated because it is the kind of thing that looks like a
    fault later. This kernel's boolean answers are not bit-reproducible
    between processes: the same source built twice gave Earth's Sol Africa
    body as 37.0419 mm³ once and 37.0247 mm³ the next time, valid the first [observed]
    time and invalid the second. The printed solids are not affected -- all
    twenty-four are reproducible, because `build_world` fuses a disc, a ball
    and a ring and never touches a marking -- but the sixteen worlds' colour
    bodies can land a few hundredths of a cubic millimetre apart from one run
    to the next. What this build guarantees is not the exact number; it is
    that whatever the kernel returns has been measured, covers the globe
    exactly, crosses nothing, and passes the topology checker before it is
    accepted.

16. **Mars's albedo map is drawn from outlines too, and it is the second of
    the three worlds that earn them.** The six round patches this build was handed
    sat on real classical albedo features and in the right places -- Syrtis
    Major, Mare Acidalium, and the southern maria -- and every one of those
    centres is kept. What was wrong was the shape. Syrtis Major has been drawn
    by every telescope owner since 1659 and it is a dark triangle; the southern
    maria run together into one belt along the mid-latitudes; a union of six
    discs says neither. Mars's `albedo` marking is now eight closed
    longitude/latitude rings in `parts/mars_atlas.py`, sitting beside Earth's
    atlas and using the same `outline` region kind, the same ruled-loft tool
    and the same flush-inlay discipline, unchanged. The marking key, the
    `cocoa_brown` filament, the ordering and the subtraction structure are as
    they were; no wall lean was added and no tool breaks the globe's outer
    sphere.

    The two polar caps keep the geometry they had -- a blob centred on a pole [assumed]
    *is* a polar cap -- at the same 23° and 21° of angular radius, and they
    stay cut back by `albedo`. One thing changed: both rims were exact circles
    of latitude, and the Earth run established that a bare circular rim reads
    as a lid laid on the globe rather than as ice. Each rim is now broken by
    lobes unioned onto the cap, six on the north and four on the south, the
    north reaching 0.77 mm past its rim at the deepest against the south's [observed]
    0.51 -- the larger and the more irregular of the two, as the reference
    shows. The caps were not made bigger and no dark collar was added around
    them.

    Nothing was added that the reference does not show. **No craters** -- at
    this radius a crater reads as a print defect, which is the judgement the
    markings table already recorded and which still holds. No Olympus Mons, no
    Valles Marineris, no Hellas, no bright beige highlands, no third filament.
    Mars keeps exactly `red`, `cocoa_brown` and `white`.

    What it cost at this size is measured in [observed]
    `measure/mars-atlas-resolution.md`. This globe is Ø14.72 against Earth's [inferred]
    Ø16.70, so one degree of arc is 0.1285 mm here and the 0.40 mm nozzle is [inferred]
    3.11° -- every outline on Mars is finer than Earth's was. Nothing falls
    under it: the shortest ring edge is Sinus Meridiani's at 0.64 mm, the [observed]
    narrowest neck is Sinus Sabaeus's at 0.85 mm, the tightest red channel is [observed]
    Sabaeus/Meridiani at 0.46 mm, and the widest ring reaches 32.3° from its [observed]
    own axis against the outline tool's 72° limit. **Four vertices were
    moved**, all of them to clear the nozzle and none of them on a silhouette [observed]
    the eye reads: Sirenum's eastern edge 4° east and Cimmerium's western edge
    3° west, closing a 0.32 mm thread of red between two rings the atlas means [observed]
    to fuse; Cimmerium's eastern vertex 5° east and Tyrrhenum's south-western
    vertex 5° west, closing the same fault at 0.34 mm on the belt's other [observed]
    join. Both joins now overlap -- 0.46 mm² and 0.24 mm² of shared surface, [observed]
    biting 0.37 mm and 0.53 mm -- rather than merely approaching, and every [observed]
    moved vertex ends up buried inside a neighbouring ring, so the belt's own
    outline does not move. The fourth is Sinus Meridiani's south-western
    corner, lifted 1° of latitude, which opens the red channel between it and
    Sabaeus from 0.36 mm to 0.46 mm; those two are *not* a fused pair, so the [observed]
    channel was opened rather than closed, and one degree is the smallest move
    that clears the nozzle.

    **Sinus Sabaeus is carried vertex for vertex.** The Wish names it as the
    ring most at risk -- it is deliberately a thin streak, and a thin streak is
    what a nozzle cannot hold -- so it was measured rather than assumed. Its
    narrowest printable width is 0.85 mm, twice the nozzle. It was neither [observed]
    widened nor dropped, and it was not turned into a blob.

    As on the Earth run, the two printed solids come out byte-identical to the
    ones this build was handed: `part_world_mars_sol.step` and
    `part_world_mars_anti.step` are unchanged, because a flush inlay partitions
    the globe's volume without moving the printed solid's boundary. The
    corrected geometry lives in the per-colour bodies under `product/parts/`,
    and `measure/occurrence-geometry.md` is what compares them.

17. **Two things an independent reader of this build's renders got wrong,
    and one they got right.** The canonical images were given to a critic who
    had not been told what the product is. Three of their findings were
    structural and are answered here with booleans rather than with argument,
    because a board-scale render cannot settle any of them.

    *A cone passes through a sphere.* It does not.
    `measure/seated-piece-clearance.md` places all eight worlds at the two
    exact heights the assembly gives them -- 3.00 mm in a corona well and [inferred]
    5.20 mm on a star -- beside the exact corona tile and star plug, and [inferred]
    measures the volume they share. It is 0.000000 mm³ in all sixteen cases, [observed]
    Jupiter's Ø26.97 globe included. What the sheet shows at those cells is
    two parts overlapping in projection.

    *The ring passes through its own base, and a disc straddles two terrain
    levels.* Neither happens. `inspect interfere` on the whole 182-occurrence
    opening assembly reports `clashCount 0`, and `inspect validate` reports [observed]
    the assembly sound. The ring and the disc share surfaces by design -- the
    ring's web is carried down to the disc precisely so the ring can print
    without support -- and a shared surface renders as coincident-face flicker,
    which is what was seen.

    *The albedo patches are lighter than the globe they sit in.* They measured
    the images correctly and the conclusion about the product is still wrong,
    and the gap between those two sentences is worth the space.
    `measure/filament-value.md` measures both ends of it. On the **sealed**
    channels -- which are what the shop and the listing read, and which
    `colors.py` authors as the catalogue sRGB hex unconverted, as the Make
    contract requires -- `red` is #FF0000 at a relative luminance of 0.2126 [observed]
    and `cocoa_brown` is #8E3C06 at 0.0900. The albedo is the darker of the
    two. But `cad/scripts/render_review`, which drew every image in `snap/`,
    carries a `_linear_to_srgb` and applies it to the channels it is handed;
    those channels are already sRGB, so every colour in those images is
    encoded twice. A double encode lifts a mid-tone hard and cannot lift a
    channel already at 1.0, so in `snap/` `cocoa_brown` is displayed as [inferred]
    **#C5852A** at a luminance of 0.2884 while `red` does not move at all --
    and in those images, and only in those images, the albedo really is
    lighter than the globe. That is the ochre the critic saw, and it predicts
    the rendered pixel exactly.

    Two things follow and both are stated rather than fixed. The printed piece
    has the albedo darker, as the Wish asks. And the margin is thin even so:
    the sealed contrast ratio is **1.88:1**, under the 3:1 at which a value [inferred]
    difference reads as lightness rather than as hue, and `cocoa_brown` is the
    warmer and yellower of the pair, so at a glance the markings will read as
    a change of colour more than as darkness. Mars is required to keep exactly
    `red`, `cocoa_brown` and `white` -- the same answer, and for the same
    reason, as Earth's pale `beige` dryland against its `white` ice. Every
    visual judgement in this run, including the blind review, was made on
    double-encoded images; that is a limitation of this run's evidence and is
    recorded as one.

    What the same reader got right, and it is the thing this revision exists
    for: shown the Mars pieces cold, with no idea what they were, they picked
    one dark region out and gave it a shape -- "a shield or blunt arrowhead,
    flat across the top-left, tapering to a rounded point at the bottom". That
    is Syrtis Major, and it is the first time a reader of this set has named a
    Martian feature by its shape rather than calling it a patch. They read the
    southern maria as "a chain of three or four joined lozenges running
    horizontally right across the body -- a belt", which is what the three
    fused rings are for, and they described both cap rims as "irregular and
    angular, like torn paper, not a drawn circle". They did not name the
    planet Mars from the markings, and said so plainly. At Ø14.72 with three
    filaments and no relief -- and with the albedo shown to them lighter than
    the globe rather than darker -- that is the honest ceiling.

    One requirement they could not judge at all, and they were right not to
    try: whether the north cap is the larger and more irregular of the two.
    **No render in this set shows the south cap**, because there is almost
    nothing of it left to show. The globe is sunk 2.00 mm into its disc and [assumed]
    cut at the disc's top face, and at 25.19° of obliquity that cut takes the
    south pole with it: `measure/mars-surface.md` finds white at latitude -70
    and nothing at all below it. No camera can recover it either, and that is
    geometry rather than a gap in the evidence: every disc is Ø34.00 and every [assumed]
    globe is smaller, so a camera placed under the equator sees the underside
    of the disc and almost nothing of the ball. This build rendered one at 25°
    below the horizon to check, and that is exactly what it showed, so no such
    frame is carried in `snap/worlds/`. The asymmetry is real in
    the geometry -- six northern lobes reaching 0.77 mm past their rim against [observed]
    four southern ones reaching 0.51 -- and it is measured in
    `measure/mars-atlas-resolution.md`. It is not visible on the finished
    piece and is not claimed to be.

18. **Mercury is the third and last world drawn from outlines, and its
    defect was contrast before it was shape.** Both Mercury pieces read as
    featureless grey balls in the previous run's `iso.png`, and the obvious
    explanation is the wrong one. The patches were not hiding round the back:
    measured against the hero view axis, three of the seven face the camera
    and one of those at +0.55, and four face the state-sheet camera.
    `measure/mercury-facing.md` is that measurement, and the same numbers are
    recorded in `parts/markings.py` in the form Venus's and Jupiter's
    longitude corrections use. Venus and Jupiter each had a genuine far-side
    problem and each was carried in longitude to fix it; Mercury did not, and
    carrying it would not have helped.

    What Mercury had is a contrast problem on the smallest globe in the set.
    `measure/mercury-tone-separation.md` renders the same piece twice at one
    canonical camera -- once with a region in the candidate filament, once
    with it in the globe's own `gray` -- so the pixels that move are the patch
    and nothing else moves at all. On those pixels `dark_gray` #6F6E6D against
    the `gray` #9FA19F globe measures **21.8 of 255 luma levels** at the hero [observed]
    frame and 22.0 at the state sheet. On a Ø13.78 ball occupying a few dozen
    pixels of a product image, that is invisible, and it is what the reader
    was looking at.

    **The plains are now `cocoa_brown`**, which measures 45.5 and 45.9 on the [observed]
    same test -- a little over twice the separation. On the sealed channels
    the shop prints, the three candidates are 50.3, 86.9 and 160.4 for [observed]
    `dark_gray`, `cocoa_brown` and `black`. `black` was available and was not
    taken: it measures 139.6 rendered, and a black patch on a small grey ball [observed]
    reads as a hole in the print rather than as terrain, while the reference's
    darkest terrain is a mid grey-brown. The seven patches keep their marking
    key, their ordering, their empty subtraction structure and the exact
    centres they had. Only the filament and the outline changed.

    **The plains are shapes rather than circles.** Each is a closed ring
    generated from a documented deterministic formula in
    `parts/mercury_atlas.py`: a mean angular radius about the patch's own
    centre modulated by harmonics one to three, so no two are the same egg
    turned round. A formula rather than survey data because there is no survey
    to carry -- Mercury's albedo boundaries are soft and unnamed, and the thing
    that had to be true of them is that they are not discs. Three of the seven
    run together into one larger smooth plain and two more into a second, as
    the reference shows; `measure/mercury-surface.md` classifies the built
    solids point by point and finds exactly those two fusions, leaving four [observed]
    regions where the round-patch build left four discs.

    **Caloris is built as a ringed basin.** It is about 1550 km across on a
    planet 4879 km in diameter, which is 36° of arc and **4.33 mm** on this [inferred]
    globe, at latitude +30. Its longitude is free -- this set fixes no
    meridian on Mercury -- so it was placed by measurement at −50, the
    midpoint of the two camera azimuths, where it measures **+0.99** against [observed]
    the view axis at both photographed frames on both armies: the most nearly
    dead-on any marking in this set gets. It is two concentric outlines rather
    than a circle union: a `white` floor 2.53 mm across, and the rim annulus [observed]
    left when that floor is subtracted out of the outer ring, in the same
    `cocoa_brown` as the plains. The rim measures 0.640 mm at its narrowest, [observed]
    0.902 mean and 1.214 widest, all clear of the 0.40 mm nozzle. Both [assumed]
    outlines are scalloped; a true circle at this size reads as a drilled hole
    or a moulding pip, and the reference's basin edge is visibly scalloped.

    **Mercury costs a third filament.** The floor has to be brighter than the
    globe, and the only stocked filaments lighter than `gray` are `beige`
    #F7E6DE and `white` #FFFEF7. Measured the same way, `white` separates 36.9 [observed]
    luma levels from the globe against `beige`'s 35.3, and leads by more on
    the boundary a reader actually reads -- the floor against the rim -- at
    114.3 against 104.9. Both clear the 21.8 that vanished by half as much [observed]
    again, so the third filament is worth loading, and `white` is the one
    taken. `beige` against `white` measures 9.4 as rendered and is this
    palette's known weak pair, but only one of the two is used here, so that
    pair never occurs on this globe. Mercury now prints in `gray`,
    `cocoa_brown` and `white` where it printed in two.

    **No craters, and here is the number.** The reference shows craters
    everywhere and none is drawn. One degree of arc is 0.120 mm here, so the [inferred]
    0.4 mm nozzle is 3.33° and the largest crater outside Caloris subtends [assumed]
    three to six degrees -- one or two nozzle widths, with no room for a rim
    and a floor inside that. It would print as a pit one extrusion wide and
    read as a print defect, and the set's material rules forbid deliberate
    grit. Caloris is the exception precisely because at 36° of arc it is
    eleven nozzle widths across. This is stated with the number so a later
    reader does not reopen it.

    What it cost at this size is measured in [observed]
    `measure/mercury-atlas-resolution.md`. Nothing falls under the nozzle: the
    shortest ring edge is the Caloris rim's at 0.52 mm, the narrowest neck the [observed]
    same, the tightest gray channel between two plains 0.69 mm, and the [observed]
    narrowest part of the rim annulus 0.640 mm. The vertex count is not fixed [observed]
    but derived -- the most vertices a ring can carry with every edge at or
    above 0.50 mm, measured against that ring's own least radius -- which puts [assumed]
    the strongly lobed plains on 12 to 16 steps and the nearly round Caloris [observed]
    rim on 23. **One ring was simplified**: `plain_south_lead` is drawn at a
    mean 20° rather than 22° with the strongest northward bias of the seven,
    because at 22° its southern boundary reached latitude −44, past the −42
    parallel where the seat cone springs and the visible sphere ends. Pulled
    north it stands at −37.6 and leaves 0.53 mm of visible gray between the [observed]
    plain and the seat. Its centre did not move.

    As on the Earth and Mars runs, the two printed solids come out
    byte-identical to the ones this build was handed:
    `part_world_mercury_sol.step` and `part_world_mercury_anti.step` are
    unchanged, because a flush inlay partitions the globe's volume without
    moving the printed solid's boundary. The corrected geometry lives in the
    per-colour bodies under `product/parts/`, and
    `measure/occurrence-geometry.md` is what compares them.

19. **Venus is the fourth world drawn from outlines, and the only one drawn
    from radar. It stopped showing its atmosphere and started showing its
    surface.** That is a decision of the owner of the set, not a drafting
    accident, and it reverses what this document used to say.

    What stood here was the Mariner-10 ultraviolet cloud Y: ten overlapping
    circles in `orange` #FF671F on a `beige` #F7E6DE globe. Three things were
    wrong with it and the third decides. `orange` on `beige` was the
    highest-contrast pairing anywhere in this set, higher than Jupiter's brown
    on orange and higher than Earth's green on blue. Ten overlapping circles do
    not read as a Y — in the previous run's `iso.png` they read as one orange
    smear down the side of a cream ball. And it was the wrong subject: the
    cloud Y is a feature of the atmosphere and the reference for this
    correction, `ref/venus-radar-surface.png`, is the surface underneath it. A
    cloud pattern and a radar map are two pictures of two different objects and
    they cannot both be on the globe, so the Y is gone and nothing stands in
    for it — no clouds, no terminator shading, no crater, no named volcano, no
    polar cap.

    **The reference changed with the subject.** `ref/venus-sol.png` and
    `ref/venus-anti.png` show the pale cream cloud tops, which is what Venus
    looks like in visible light. For these two parts they are superseded on the
    globe's surface and the globe's colour, and on nothing else: the disc, the
    numeral, the proportions, the seat collar, the lean and the disc filaments
    are still read off them and still hold. The new authority is a supplied
    photographic dataset image — the Magellan global radar mosaic, 224x224 —
    and its provenance is different from every other image in `ref/`: the
    twenty sealed references were AI-generated and their notes state that no
    web imagery was used, while this one is **supplied by the owner**. The
    reference set is no longer wholly AI-generated and is not described that
    way anywhere.

    **The globe is amber.** `beige` is a pale pink-cream and the mosaic is a
    saturated golden amber; no marking closes that gap. Venus's globe is now
    `sunflower_yellow` #FFB549, the closest amber the shop stocks, already in
    the set as the Sol den plug, so the change costs no new spool. Section 9
    records both the collision that creates and the near-collision with
    Saturn's `yellow`. That second one was checked rather than assumed:
    `measure/venus-saturn-separation.md` renders the two pieces side by side at
    the product's own frame, and read off that image, Saturn is plainly the
    bigger ball — it overhangs its disc where Venus sits well inside its own —
    it wears a white ring leaning clear of the board on both sides, and it
    carries four loud `cocoa_brown` belts where Venus has one pale sinuous
    highland and no band system at all. The two ambers do read as one family of
    colour, Saturn's lighter and greener and Venus's deeper and oranger, and
    that is the weakest of the cues. Measured: 9.47 mm of globe diameter apart, [observed]
    36% taller in rendered silhouette, and exactly as wide, because on both
    pieces the Ø34.00 disc rather than the globe is the widest thing. **The
    silhouette carries it easily; the colour alone would not.**

    **Two marking tones, measured before they were committed.** The mosaic has
    three values — mid amber plains, brighter rough highlands, darker smooth
    lowlands — so with the globe as the mid tone the markings need one filament
    above it and one below. `measure/venus-tone-separation.md` renders one
    Venus piece twice at one canonical camera, once with a region in the
    candidate filament and once with it in the tone it is compared against, so
    the pixels that move are that region and nothing else moves at all. The
    three numbers the correction asked for, as rendered: `beige` highlands
    against the amber globe **20.2** of 255 luma levels, `cocoa_brown` lowlands
    against it **33.3**, and the two against each other **43.0**. `black` [observed]
    measures 91.1 and would read as a hole in the print; `dark_gray` 19.0 and
    would vanish; `white` would give the highlands 27.9 rather than 20.2 and
    was not taken, because `white` is already the brightest feature on three
    other worlds here. **The darker tone does not swamp the globe**, so all
    three plains are drawn and none was dropped.

    The 20.2 is the thinnest marking separation anywhere in this set and it is
    below the 21.8 that item 18 rejected as invisible on Mercury. It is stated
    rather than softened. Two things make it read here where that one did not,
    and both are measured: area — Aphrodite covers about 17,400 pixels of a
    900-pixel frame and its widest row is 117° of longitude, 16.9 mm of arc, [observed]
    the longest continuous marking in the set, where Mercury's plains were
    separate patches a few millimetres across — and hue, since `beige` is a
    pink-cream against an amber and carries a colour step luma does not count.
    `snap/worlds/venus-sol-aphrodite.png` and its Anti-Sol mirror are where

    **Venus now prints in three filaments** — `sunflower_yellow`, `beige` and
    `cocoa_brown` — where it printed in two. Earth takes four; Mercury, Mars,
    Neptune, Saturn, Jupiter and now Venus take three; Uranus alone takes two.
    All thirteen spools are the ones the set already loaded. (Jupiter has since
    taken a fourth of its own; item 20 has the tally as it now stands.)

    **The structure is Earth's, one level down.** `highland` in the brighter
    tone from seven rings, `lowland` in the darker one from three, with
    `highland` subtracted out of `lowland` so that where the two overlap the
    highland wins. The ordering, the `outline` region kind, the ruled-loft
    tool, the 1.20 mm inlay depth and the subtraction discipline are [assumed]
    unchanged. No wall lean was added, no tool breaks the globe's outer sphere,
    and every marking on Venus is still a flush colour inlay: the five colour
    bodies add up to 6678.5853 mm³ and the printed part built from the disc [observed]
    and the ball directly is 6678.5853 mm³, two independent constructions
    agreeing to 0.000002 mm³.

    **The obliquity is untouched and still inverts the pattern.** 177.36° is
    the dimension this correction is forbidden to move and it did not move.
    Every ring in `parts/venus_atlas.py` is in ordinary Venusian latitude and
    longitude and none of it is pre-inverted; the planet frame does the
    inverting, and `measure/venus-surface.md` checks it province by province on
    both armies — a northern province lands low on the piece and a southern one
    high, on all ten, on both.

    That inversion has a price and it is paid by **Ishtar Terra**. The globe is
    sunk 2.00 mm into its disc and carried by a seat cone springing at [assumed]
    piece-latitude −42, and at 177.36° the planet's *north* pole is what points
    into that collar. Ishtar runs from Venusian +54 to +76 and lands entirely
    inside it on both armies, so it is drawn in full and cannot be seen; 36% of [observed]
    Atalanta Planitia goes the same way. It is not nothing in the solid, and
    the number is measured on the built part rather than assumed: the part of
    Ishtar above the disc's own cut survives as a 3.04 mm³ body of `beige` [observed]
    spanning piece-latitude −49.29 to −41.89, which the shop prints and nobody
    sees — its top edge clears the parallel where the collar springs by 0.11°,
    0.016 mm of arc. Neither province is a fault and neither was [observed]
    dropped — the reason they are invisible is the inversion itself.

    **The longitude offset was measured from scratch**, not inherited: item 10
    has it. **One simplification**, and it is a construction one:
    `features/patches.py` refuses an outline ring reaching more than 72° from
    its own mean axis, and Aphrodite as drawn reaches 77.23°, so the build
    sweeps it as two rings overlapping across 28° of longitude whose union is
    the drawn ring exactly. No vertex moved and no width changed. Its waist is [observed]
    1.184 mm — 8.21° of arc, 2.96 nozzle widths — so it never needed [observed]
    widening, and `measure/venus-surface.md` confirms the two halves come out
    as one fused highland of 228 cells rather than two.

    **None of the radar texture survives, and none is faked.** One degree of
    arc is 0.1443 mm on this Ø16.53 globe and the 0.4 mm nozzle is 2.77° of [inferred]
    arc, so a radar filament a few tens of kilometres wide is about a fifth of
    one nozzle width. The piece carries the continents and the plains and none
    of the texture: it is a simplified map of the reference, not the reference.
    No stippling and no fine ribs stand in for it — the set's material rules
    forbid deliberate grit and at this size it would print as noise.
    `measure/venus-atlas-resolution.md` tabulates every ring's vertex count,
    perimeter, shortest edge, narrowest neck and half-angle against the nozzle,
    with every simplification and every omission and its reason. Nothing falls
    under the nozzle: the shortest ring edge is Themis Regio's at 0.66 mm and [observed]
    the narrowest neck the same, against a 0.40 mm floor. All four small [observed]
    Regios are held at printable width, so none was dropped, none was shrunk
    to a dot and none was replaced by a circle.

    As on the Earth, Mars and Mercury runs, the two printed solids come out
    byte-identical to the ones this build was handed:
    `part_world_venus_sol.step` and `part_world_venus_anti.step` are unchanged,
    because a flush inlay partitions the globe's volume without moving the
    printed solid's boundary. The corrected geometry lives in the per-colour
    bodies under `product/parts/`, and `measure/occurrence-geometry.md` is what
    compares them.

20. **Jupiter's bands were regular, and regularity is the one thing a planet
    never is.** Six `cocoa_brown` belts stood here, every one of them exactly
    12° wide, at −56/−44, −36/−24, −16/−4, 4/16, 24/36 and 44/56: equal width, [observed]
    equal spacing, perfectly symmetric about the equator. That is a beach ball.
    `ref/jupiter-sol.png` is not — its bands differ in width by a factor of
    three, the belts north and south of the equator are visibly unequal, and
    the broad bright equatorial zone is the widest feature on the planet.

    **The belts are now Jupiter's own.** Six of them still, so the print cost
    of the belt system does not change, at the latitudes the real belts occupy:
    North North Temperate +38/+43, North Temperate +24/+31, North Equatorial [observed]
    +7/+17, South Equatorial −7/−20, South Temperate −27/−34 and South South [observed]
    Temperate −40/−46. Their widths run 5, 7, 10, 13, 7 and 6°; no two of the [observed]
    pairs are mirror images and no two gaps between them are equal. The South
    Equatorial is the widest and is the one a reader meets first after the
    spot. All six are one filament, so "darkest" is carried by width rather
    than by tone, and that is stated rather than implied.

    **The reference is three-toned and the build was two-toned.** With
    `orange` and `cocoa_brown` only, the bright zones between the belts were
    bare globe and the alternating rhythm that makes Jupiter legible was
    missing. Five zones are added — Equatorial −7/+7, North Tropical +17/+24,
    South Tropical −27/−20, North Temperate +31/+38, South Temperate
    −40/−34 — in `beige` #F7E6DE. The filament was measured, not chosen:
    `measure/jupiter-tone-separation.md` renders one Jupiter piece twice at one
    camera with only the zones repainted, so the pixels that move are the zones
    and nothing else moves at all. Averaged over the hero, state-sheet and
    per-world frames, `beige` separates **46.3 of 255 luma levels from the [observed]
    globe and 77.9 from the belts**. The three rivals were measured on the same [observed]
    pixels and refused: `sunflower_yellow` at 28.6 is the narrowest of the four [observed]
    and is now Venus's whole globe as well as the Sol den plug; `yellow` at
    37.1 is Saturn's globe; `white` at 52.6 measures furthest and is already [observed]
    the brightest feature on four other worlds here, and the reference's zones
    are cream rather than white. The gap between `white` and `beige` is 6.3 [observed]
    luma levels and that is what the choice cost. Because `sunflower_yellow`
    was not taken, Jupiter's globe and Venus's stay `orange` and
    `sunflower_yellow` and no new pairing was created.

    **The poles are left bare above +46 and below −46.** The reference darkens
    toward the poles rather than brightening, and bare `orange` is closer to
    that than a bright zone would be. `snap/worlds/jupiter-sol-polar.png` and
    `snap/worlds/jupiter-anti-polar.png` are what that looks like down each
    piece's own axis.

    **Two belt boundaries are outlines rather than circles of latitude.** The
    Earth run established that an exact circle of latitude reads as a machined
    edge. The two widest belts carry a 2.5° wave on each boundary — two [assumed]
    harmonics of longitude apiece, with different periods and phases so no two
    of the four boundaries move together — drawn as closed longitude/latitude
    rings in six 60° sectors that abut on exact radial planes and fuse back
    into one belt. A belt encircles the globe and no single radial cone is an
    annulus, which is why it is sectored. The four narrow belts stay plain
    `band` regions, and that is arithmetic rather than taste: 2.5° either way
    on both boundaries is 5° of swing, which is the whole width of the North
    North Temperate Belt. Measured along its own length the North Equatorial
    Belt never falls below 7.03° and the South Equatorial below 7.20°, because [observed]
    the two boundaries never reach their extremes at the same longitude.

    **The Great Red Spot is an oval.** It was three overlapping circles and
    read as a lozenge. The real storm is 16,000 by 11,000 km on a planet [observed]
    139,820 km across, so one degree of arc is 1,220 km and the spot is 13° by [inferred]
    9 — half again wider than it is tall, which is what the reference shows and
    not the long thin oval of nineteenth-century drawings. It is drawn at
    latitude −22, the real one, as one 13-vertex outline ring, with an 18-vertex
    `cocoa_brown` collar 2.00° of arc outside it so the spot has an edge rather [assumed]
    than floating. The South Equatorial Belt's southern boundary bends 7.0° [assumed]
    north over it, so the belt goes round the spot instead of running past it;
    that hollow is what makes the spot belong to the weather rather than sit on
    it like a sticker.

    **The −110° longitude carry is preserved and re-measured.** The spot's
    centre is still longitude −48, where the original build's carry put it, and
    nothing here moved it. Re-measured against the oval rather than the three
    circles, its centre faces the view axis at +0.69 and +0.74 at the hero [observed]
    frame and +0.51 and +0.57 at the state sheet, Sol then Anti-Sol, and the [observed]
    worst vertex of the whole ring over both armies and both frames is +0.41. [observed]
    The original build measured −0.49 before the carry.
    `measure/jupiter-facing.md` is the table.

    **Nothing else was added.** No white ovals, no polar hoods, no festoons, no
    plumes, no turbulent texture along a belt edge beyond the single wave, and
    no fourth marking colour beyond globe, belts, zones and spot — the collar
    is the belts' own filament. The reference has far more detail than that and
    almost none of it survives the nozzle: the white ovals subtend 2 to 4° of [observed]
    arc, one to two nozzle widths with no room for a boundary either side, and
    the festoons and the filamentary turbulence are finer again.
    `parts/jupiter_atlas.py`'s `NOT_DRAWN` carries the arithmetic.

    **The zones are a region kind nothing else in the set uses.** A `band` is a
    lens that reaches its full depth at its own middle and tapers to nothing at
    its own edges — the right shape for a band drawn where it is shown, and the
    wrong one for a band drawn wider than it is shown and trimmed by its
    neighbour, because then the trim decides the depth. Each zone is therefore
    a `shell`: the frustum through two parallels, hollowed by a depth sphere,
    so it is the same depth edge to edge. It is inlaid 1.14 mm rather than the [assumed]
    1.20 mm the belts, the spot and the collar reach, a clearance of 0.06 mm. [assumed]
    That gap is not decoration: at equal depth the zones' floor and the outline
    lenses' floor are one sphere described twice, and the split left a 0.0342 [observed]
    mm³ shard of bare globe floating six micrometres under the surface, which
    came out as two solids of `orange` on one army and three on the other — so
    the two armies stopped being exact mirrors. At that 0.06 mm clearance every [assumed]
    body is a single solid and the two armies agree to 1.5e-5 mm³. The [observed]
    clearance is under the globe's surface and nothing can see it.

    **And a zone stops at a plain belt's exact latitude, not past it.** A
    `band` lens tapers to nothing at its own edge, so a zone drawn past one is
    not trimmed by it: it runs underneath the belt's feather at full depth.
    Drawn a whole degree past, that buried `beige` cut the orange globe into
    three separate solids. Drawn a quarter of a degree past, the globe stayed
    whole but the two bodies interlocked along the feather's knife edge, and
    the interference gate could not answer the pair — `inspect interfere`
    reported the South Temperate Belt's entire 51.52 mm³ as a clash with the [observed]
    South Tropical Zone on the Anti-Sol world and nothing at all on the Sol
    world, from geometry that is its mirror. Drawn to the exact latitude, the
    two bodies meet on a curve instead of interlocking and the gate is clean on
    both armies. One world's five zone bodies total 780.6941 mm³, and its [observed]
    fifteen colour bodies add up to 14736.3985 mm³ against the 14736.3985 the [observed]
    printed part built from the disc and the ball directly measures — two
    independent constructions agreeing to 0.000008 mm³.

    **The zones are trimmed by split order, not by subtraction.** Every other
    world here makes two markings disjoint by subtracting one from the other,
    which necessarily describes their shared boundary twice — once as the lens
    the globe was split by, once as the solid cone taken out of the sibling.
    Jupiter's four markings are cut in priority order instead — belts, spot,
    collar, zones — so each is trimmed by the face the previous cut left and
    the boundary is described once. Built the other way, the two descriptions
    differed by about a ten-thousandth of a millimetre and left a 0.0016 mm² [observed]
    spline sliver with no area to triangulate, which took the whole set's
    renderer down on a null triangulation. Both failures were measured on this
    build and both are recorded in `parts/jupiter_atlas.py` and
    `features/patches.py` rather than in a commit message.

    **Nothing else about Jupiter moved.** Its globe is still Ø26.97, the
    largest in the set; its obliquity is still 3.13°, its rank still 8, its
    globe still `orange`, its disc still Ø34.00 with the 5.00 mm wall and the [assumed]
    2.00 mm sink and the −42° seat, and the Sol world still leans its north [assumed]
    pole toward +X against the Anti-Sol world's −X. The two remain exact
    mirrors: every colour body on the Anti-Sol world has the same volume as its
    Sol twin, the largest disagreement being 1.5e-5 mm³ on a 8,920 mm³ globe. [observed]
    `measure/jupiter-atlas-resolution.md` tabulates every belt width, zone
    width, ring edge and annulus neck against the 0.40 mm nozzle; nothing falls [assumed]
    under it. The narrowest belt along its own length is 1.18 mm, the narrowest [observed]
    zone 1.06 mm, the collar annulus 0.471 mm, the bright zone between the [observed]
    collar and the hollowed belt above it 0.507 mm, and the shortest edge of [observed]
    either oval ring 0.514 mm. [observed]

    **Jupiter now prints in four filaments** — `orange`, `cocoa_brown`, `beige`
    and `red` — where it printed in three. That ties it with Earth as the most
    expensive world in the set; Mercury, Mars, Venus, Neptune and Saturn take
    three and Uranus takes two. All thirteen spools are the ones the set
    already loaded: `beige` was already on Earth's dryland and Venus's
    highlands.

    One thing the collar costs, stated rather than buried: the spot is 9° of
    arc tall centred at −22 and the South Tropical Zone is 7° deep, so a collar
    wide enough to print at all reaches past −27 into the South Temperate Belt.
    Biting a second hollow out of that belt is not available — it has to stay a
    plain circle of latitude — so the collar gives way there instead, and over
    11.7° of longitude, 2.56 mm of arc, the collar and that belt are one [observed]
    continuous `cocoa_brown` region. Both are the same filament, so nothing
    prints differently; what a reader sees is the spot's collar touching the
    belt below it.

    As on the Earth, Mars, Mercury and Venus runs, the two printed solids come
    out byte-identical to the ones this build was handed:
    `part_world_jupiter_sol.step` and `part_world_jupiter_anti.step` are
    unchanged, because a flush inlay partitions the globe's volume without
    moving the printed solid's boundary. The corrected geometry lives in the
    per-colour bodies under `product/parts/`, and
    `measure/occurrence-geometry.md` is what compares them.

21. **Saturn was not too plain; it was too loud, and this is the first
    correction in the chain that runs that way.** Four `cocoa_brown` bands
    stood here, every one of them exactly 12° wide, at −51/−39, −21/−9, 9/21 [observed]
    and 39/51: equal width, equal spacing, perfectly symmetric about the
    equator — Jupiter's fault exactly — and in `cocoa_brown` #8E3C06 against
    `yellow` #FFD834, one of the highest-contrast pairings the palette offers.
    The piece read as a hard-striped gold ball. `ref/saturn-sol.png` is the
    softest image in the reference set: its globe runs cream to pale tan, its [observed]
    bands are wide and soft-edged and low in contrast, the strongest of them is
    barely darker than its neighbours, and its northern part is lighter than
    its southern. Saturn stands on the board beside Jupiter, which is loud on
    purpose, and that contrast between the two pieces is worth keeping.

    **The band tone came down, and the number is the smallest this project has
    committed to.** `cocoa_brown` stops being Saturn's band colour. The four
    light bands are `sunflower_yellow` #FFB549, a genuine mid tone between the
    globe and the dark browns, already loaded for the Sol den plug and for
    Venus's globe, so it costs no new spool. Measured the same two-render way
    the rest of this set uses — one piece built once and rendered twice at one
    camera with a single region repainted and nothing else altered — it
    separates **9.4** of 255 luma levels from the globe, averaged over the [observed]
    hero, state-sheet and per-world frames. That is below the 20.2 this set
    calls its thinnest and below the 21.8 it rejected on Mercury as invisible,
    and it is reported that way rather than softened. It reads here for the two
    reasons Venus's `beige` reads at 20.2: area and hue. The bands cover about
    102,000 pixels of a 900-pixel frame where Mercury's plains were patches a [observed]
    few millimetres across, and `sunflower_yellow` is an amber against a
    green-yellow, so the boundary carries a hue step luma does not count.
    The Wish's fallback tone was measured beside it and **not** taken: `beige` [observed]
    #F7E6DE separates **10.1**, seven tenths of a level better, which is not a
    difference. `measure/saturn-tone-separation.md` is all of it.

    **One band is still `cocoa_brown`, and only one.** The widest, −14/−30. It [observed]
    measures 39.5 against the globe and 34.7 against the light bands, between
    the 33.5 this set accepted on Venus's lowlands and the 45.5 it accepted on
    Mercury's plains, and it covers under a tenth of the marked area on the
    piece. `snap/worlds/saturn-dark-band-kept.png` and `-dropped.png` are the
    same piece with and without it, so "distinguishable without dominating" is
    a picture as well as a number.

    **Five bands, unequal and asymmetric.** +46/+55, +18/+33, +2/+10, −14/−30
    and −38/−50: widths 9, 15, 8, 16 and 12°, five different spacings, no pair [observed]
    a mirror of another. On a Ø26.00 globe one degree of arc is 0.2269 mm and [inferred]
    the 0.4 mm nozzle is 1.76° of it, so those widths print at 2.04, 3.40, [inferred]
    1.82, 3.63 and 2.72 mm — the narrowest 4.5 nozzle widths. [inferred] Five bands in a
    cheaper colour is still a simpler print than four in the loudest one.

    **The two widest wave; the three narrow ones do not.** +18/+33 and −14/−30
    carry 2.5° of wave on each boundary, two harmonics per boundary with
    different periods and phases and none of them Jupiter's, drawn as six
    longitude sectors abutting on exact radial planes — the Earth lesson about
    circles of latitude, applied as it was on Jupiter. Swept at a tenth of a
    degree over the whole globe, the wave takes the North Temperate Band down
    to 10.53° at its narrowest and the South Temperate Belt to 11.89°, which is [observed]
    2.39 and 2.70 mm; the shortest edge of any of the twelve sector rings is [observed]
    1.114 mm and the narrowest neck 2.399 mm. At 8 to 12° a wave would eat the [observed]
    three narrow bands, so they stay plain. `measure/saturn-atlas-resolution.md`
    carries every one of those numbers.

    **The northern third is lighter.** A `cap` above +58, no lobed rim. That
    was deliberate and it is the opposite of the Earth decision: the lid lesson
    is about a small bright cap on a dark globe, and this is a wide soft
    brightening on an already light one, where an exact parallel is what the
    reference shows. The tone is `white` #FFFEF7, the lightest this piece
    already carries — it is the ring — so it loads no new spool, and in the
    reference the ring and the northern globe are the same cream. It measures
    **16.0** against the globe, which is *below* the 21.8 this set called [observed]
    invisible: the brightness it appears to have in the renders is the specular
    highlight sitting on the pole the piece leans toward the light, not the
    tone step. A `beige` cap was rendered beside it at 11.2 and not taken.

    **The cap is on the north only, and that is visible on one army and nearly
    gone on the other.** Saturn's obliquity is 26.73° and a Sol world leans its
    north pole toward +X, so at the product's own frame the Sol piece shows its
    cap over 29,333 pixels of a 700-pixel frame and the Anti-Sol piece over [observed]
    8,882 — 30%, a crescent along the upper limb rather than a region on the
    face of the ball, because the Anti-Sol pole stands +0.095 against that view [observed]
    axis. It is never hidden completely, and this says so rather than repeating
    the expectation. Each piece's own polar frame shows its own cap at 42,908 [observed]
    and 41,874 pixels — 2.4% apart — which is the same cap on both.
    `measure/saturn-cap-visibility.md` is that measurement.

    **What the two pieces share and where they differ.** They are the same
    description built twice. Ring, cap and the four light bands agree in volume
    to 7.1e−05, 1.4e−03 and 9.6e−04 mm³, and the light bands' x bounds mirror [observed]
    to 2e−15 mm. [observed] Two roles differ by design — the Sol disc flares where the
    Anti-Sol disc tapers, and the disc and numeral swap colours — and two
    differ by 0.103 and 0.074 mm³, the globe and the one dark band, which is [observed]
    0.0013% and 0.0248% of themselves. That has one cause and it is measured
    rather than guessed: the globe is cut flat at Z = 5.00 where it enters the
    disc, which is piece latitude −57.79°, so a marking is buried by the disc [inferred]
    wherever it reaches below planet latitude −31.06° at the meridian the piece
    leans along — and that meridian is longitude 0 on the Sol piece and
    longitude 180 on the Anti-Sol one. The South Temperate Belt's wavy south
    boundary stands at −30.51 at longitude 0 and −32.48 at longitude 180, so [observed]
    the Anti-Sol piece buries a little more of that band inside its own base
    than the Sol piece does. It is the same band from the same five numbers;
    what differs is which part of it the disc hides, and it is below the seat
    line on both. Narrowing one boundary's wave until it cleared that line on
    both meridians would have been a visible change made to hide an invisible
    one, so it was not made.

    **Nothing else was added, and each rejection has arithmetic rather than
    taste behind it.** The north polar hexagon is real and it is at the pole
    this piece is looked at from, which is why it was considered at all: it
    spans about 29,000 km, 28.5° of arc, 6.47 mm here, so the figure would fit. [inferred]
    Its visible edge is a jet-stream boundary a few hundred kilometres wide —
    take the most generous reading, 500 km, and that is 0.49° or 0.11 mm, a [inferred]
    quarter of one nozzle width, where the nozzle needs 1.76° or 1,792 km.
    Printed at the width the machine can lay down it would be four times too
    fat and would read as a moulding line round the pole; printed at the width
    it really is, it cannot be printed. The polar vortex eye inside it is finer
    again. The Great White Spot storms appear once a Saturnian year and are not
    what the reference shows. Ring spokes are transient radial shadowing, light
    rather than material, and a solid annulus cannot carry them. The ring
    divisions fail on the same arithmetic: the printed ring projects 2.00 mm [inferred]
    past the globe and that 2.00 mm stands for 62,117 km of real ring, so the [inferred]
    Cassini division at 4,700 km is 0.15 mm [inferred] and the Encke gap at 325 km is
    0.010 mm. [inferred] And the shadow the ring casts on the globe is light rather than
    material: printed it becomes a permanent dark band, which is the opposite
    of the soft surface this correction exists to produce. No stippling and no
    fine ribs stand in for any of them.

    **What could not be done, and it is the real limitation of this
    correction.** A flush inlay has a hard edge and there is no way to make it
    soft. The reference's bands fade into one another; this piece's cannot, and
    every boundary on it is a colour change at a line. Lowering the contrast is
    the available substitute for softening the edge, which is why the filament
    mattered more than the wave and is recorded here as such.

    **Saturn now prints in four filaments** — `yellow`, `sunflower_yellow`,
    `cocoa_brown` and `white` — where it printed in three. Earth, Jupiter and
    Saturn take four; Mercury, Mars, Venus and Neptune take three; Uranus takes
    two. All thirteen spools are the ones the set already loaded. The ring
    plate's own `white` sits directly against the globe all the way round the
    equator, because the plate's bore is 1.00 mm [assumed] inside the globe's radius —
    that is the largest value step on the piece after the numeral, and it is
    the step that reads the ring as a separate object rather than as a flange
    of the ball.

    As on the Earth, Mars, Mercury, Venus and Jupiter runs, the two printed
    solids come out byte-identical to the ones this build was handed:
    `part_world_saturn_sol.step` and `part_world_saturn_anti.step` are
    unchanged, because a flush inlay partitions the globe's volume without
    moving the printed solid's boundary. The corrected geometry lives in the
    per-colour bodies under `product/parts/`, and
    `measure/occurrence-geometry.md` is what compares them — including the
    ring, compared on solid count, volume and bounding box rather than on
    colour.

22. **Neptune's clouds circled the planet, and the reference's do not.**
    Three closed `band` regions stood here, at −46/−41, 11/15 and 30/33. A [observed]
    closed latitude band runs the whole way round the globe, so on the finished
    piece those read as three painted stripes on a blue ball, and in `iso.png`
    the two Neptunes were the most beach-ball-like objects in the set.
    `ref/neptune-sol.png` shows something else entirely: its white clouds are [observed]
    **short**. Each is a wisp that starts and stops inside a few tens of
    degrees of longitude, they sit at slightly different angles to the
    parallel, they are scattered across the face rather than ringing it, they
    are thin, and they are the brightest thing on the piece. Not one of them
    circles the planet.

    **A streak is a closed outline ring, and no new region kind was needed.**
    An arc is a long thin closed ring running along a parallel, and the
    outline machinery the Earth correction built — `features/patches.outline_tool`,
    a radial cone through a closed longitude/latitude ring, trimmed to the
    same 1.20 mm [assumed] depth — draws one directly. `parts/neptune_atlas.streak_ring`
    walks it: down one side of a parallel segment, round a half-disc at the
    far end, back up the other side, round the half-disc at the near end. The
    centreline is a segment of the PARALLEL rather than of a great circle, and
    that is measured rather than stylistic: a great-circle arc through latitude [observed]
    −52 running east rises to −45 within 26° of arc, so a streak drawn on one
    is not at the latitude it is declared at, and two streaks 15° apart
    collided at 0.01 mm [observed] on the first build. Cloud bands follow latitude in any
    case; that is what a zonal wind is. The whole ring is then turned a few
    degrees about its own centre, which is the tilt, and a rotation about a
    point of a sphere moves nothing else.

    **Eight streaks, and no two of them alike.** 46, 54, 58, 60, 72, 76, 84 and [assumed]
    90° of longitude long, at latitudes −52, −37, −10, +4, +17, +28, +38
    and +47, at eight different longitudes spanning 133° [inferred], each tilted
    3 to 12° off its own parallel with the signs alternating so the family does
    not read as a set of level rules, and each bowed 1 to 2° off that parallel
    at its middle and back to it at both ends so that no two of them are the
    same line. The latitudes are unevenly spaced on purpose: regularity is the
    single thing that tells a viewer they are holding a manufactured object,
    which is the lesson item 20 took off Jupiter.

    The longitudes were SOLVED rather than chosen. The objective was the widest
    span of longitude the eight can cover while a clear majority of them still
    face all four product cameras at a floor of +0.30, and the answer covers
    **211 of 360 degrees** [inferred]. The 149 degrees it does not cover are the
    far side, and that is the one thing about this piece a reader complains
    about; it is the arithmetic consequence of the facing requirement and it is
    recorded in the product's limitations rather than argued away.

    **They taper, they are skewed, and the first build of this correction was
    neither.** Drawn at
    one width from end to end, the eight of them rendered as a set of parallel
    hatching strokes — constant width is what a ruled line has — and the
    reference's wisps are plainly thickest in the middle and thin where they
    run out. Each streak now falls to 40 per cent of its width at each end and [assumed]
    is closed there by a half-disc of that narrowed radius, so the end is
    rounded AND tapered. The taper is also SKEWED: each streak is at its widest
    a fifth to a third of the way along rather than exactly in the middle, and
    which end that is alternates, because a symmetric taper is a leaf and eight
    leaves read as cut-out lozenges. 40 per cent rather than a point, and that number is
    the nozzle: the narrowest streak is 1.35 mm, so its ends are 0.69 mm, and a [inferred]
    taper to nothing would run the colour boundary under the printer's 0.40 mm [assumed]
    for the last stretch of every streak.

    **1.5 mm [assumed] wide is an owner's decision, recorded as one.** The nozzle is
    0.40 mm, which is 2.09° of arc on this Ø21.89 globe, so a streak must be [inferred]
    at least that to print at all and nearer 3° for the boundary not to be a
    single bead. An earlier run drew them at 0.50 to 0.69 mm [observed] on exactly that
    reasoning; it was right about printing and wrong about seeing. At that
    width a streak is under two pixels in the whole-set render and Neptune
    becomes the one world in the set whose surface does nothing at the scale
    the set is actually looked at. Saturn's bands are 3.63 to 7.26 mm [observed] and
    Jupiter's belts 2.35 to 6.12 mm, so at 1.35 to 1.65 mm this family is still [inferred]
    the narrowest marking anywhere in the box by a factor of 1.6, and at 5.4:1
    to 7.8:1 longer than it is wide it is a streak rather than a band.

    **The cost of that, which is real.** The reference's own clouds scale to
    0.13 to 0.26 mm on this globe, so at 1.5 mm these are six to twelve times [inferred]
    the reference width. That is a large, deliberate departure from the
    reference, taken by the owner on 2026-09-19 with those numbers in front of
    them, choosing legibility at the set's own viewing scale over fidelity of
    width. It is not an oversight and nothing here drifts back toward the
    nozzle to make the number look better.

    One arithmetic correction, made in the open. The brief states the width
    twice and the two statements do not agree: it gives 0.191 mm per degree of [observed]
    arc, which is right for this globe, and then calls 1.5 mm [assumed] "3.93 degrees of
    arc", which is what 0.75 mm [inferred] is. The same factor of two runs through its
    quoted 7:1 and 23:1 aspect ratios. The millimetre is what the printer, the
    eye and the comparison against Saturn's and Jupiter's belts are all in, and
    the instruction is given in millimetres three times, so the millimetre is
    followed and the degree figure is corrected: 1.5 mm is 7.85° of arc here. [inferred]

    **Latitude is a lever, not a fixed input, and that is what the previous
    attempt at this correction got wrong.** A Sol world leans its north pole
    toward +X and both of the product's cameras stand on that side, so the Sol
    piece's sub-latitudes are +35.6 at the hero frame and +51.5 at the state [inferred]
    sheet. A camera whose sub-point is at +51.5 reaches a marking at latitude
    L with a dot product of at best cos(51.5 − L), whatever longitude the
    marking is drawn at, so at a facing floor of +0.30 it cannot reach anything
    south of −21 AT ALL. An earlier run put five of eight streaks in the south,
    passed its own centre-dot test at 6/5/6/6, and was rejected anyway because
    everything was crowded onto the Sol piece's lower limb; it then spent all
    four of its review rounds moving longitudes and could not fix it, because
    longitude is not the free variable there. Here the latitudes and the
    longitudes were solved together, with the spot's own facing in the
    objective rather than checked afterwards, against a floor of +0.30 rather
    than 0 — 0 is the limb, and a marking on the limb is a sliver.

    The result, measured in `measure/neptune-facing.md`: **six of the eight
    streaks clear +0.30 at both frames on the Sol piece and all eight clear it
    at both frames on the Anti-Sol piece**, and at the per-world spot frame it
    is eight of eight on both. The two that the Sol piece's cameras cannot
    reach are `s1` at −52 and `s2` at −37, and they are **Anti-Sol-only
    features**, named as such in the source, in the facing report and in the
    product's limitations. They are kept rather than moved north because the
    reference's clouds are southern-weighted and because the Anti-Sol piece
    shows them plainly. What that cost is the reference's southern majority:
    three of the eight streaks are in the southern hemisphere rather than five.
    The southern half is not empty — it carries the dark spot, which is the
    largest marking on the piece — but it carries fewer streaks than the
    reference does, and that is stated rather than hidden. A streak nobody can
    see is not a southern streak; it is an absent one.

    **The spot is an oval with a companion.** Two overlapping `blob` circles at
    −22 and −20 stood here and read as a smudge. Neptune's Great Dark Spot was
    about 13,000 by 6,600 km on a planet 49,244 km across, so one degree of arc [observed]
    is 429.7 km and the spot is 30.3 by 15.4° — drawn as 28 by 14, the exact [inferred]
    2:1 the correction asks for and within 8 per cent of the measured object.
    The latitude, −22, is the real one and the correction fixes it; the
    longitude is free, because Neptune turns in sixteen hours and this set
    fixes no meridian, and −68 is where the facing solution put it. Just off
    its equator-facing — northern — edge sits the small bright cloud that
    trails it on the real planet, a wisp of its own rather than an oval -- 22° of longitude
    long and 1.30 mm wide, a quarter of the spot's length, [inferred] across a gap of **0.72 mm** measured on the two rings rather than
    eyeballed — half a nozzle clear of the 0.40 mm [assumed] the printer can lay
    down. The correction's rule if that gap were short is to move the companion
    rather than shrink it, and the companion's latitude is set by exactly that
    rule: its size was chosen against the spot's first and the gap decided
    where it sits.

    **The spot's +0.28 at the Sol state sheet is a ceiling, not a mistake.** At
    latitude −22 no longitude does better against a sub-point of +51.5, and the
    correction fixes the latitude. It clears the floor comfortably at the other
    three product cameras and at both per-world spot frames.

    **Nothing else is on this globe.** No second dark spot, no polar
    brightening, no ring arcs — Neptune has rings, the reference does not show
    them, this set does not draw them, and a ring on rank 5 would collide with
    Saturn's role at rank 7, where the ring IS the rank. No fourth filament,
    so the faint darker centre the reference shows inside the spot is not
    drawn. The reference's own fine cloud texture scales to under one nozzle
    width and is not faked with stippling or ribs.
    `parts/neptune_atlas.NOT_DRAWN` carries each refusal and its arithmetic.

    **What the opposite face shows, and why it is rendered.** Every streak is
    short and every one of them is placed where the product's cameras look, so
    the hemisphere opposite the dark spot carries nothing but the eastern ends
    of three of them coming round one limb and bare blue globe across the
    middle. `snap/worlds/neptune-sol-opposite.png` and its Anti-Sol mirror are
    that picture, and it is the proof of this correction's negative
    requirement: a band would have been there in full. The polar frames show
    the same thing the other way — from straight down the leaning pole a closed
    latitude band would be a complete concentric ring, and what is there is a
    set of open arcs.

    As on the Earth, Mars, Mercury, Venus, Jupiter and Saturn runs, the two
    printed solids come out byte-identical to the ones this build was handed:
    `part_world_neptune_sol.step` and `part_world_neptune_anti.step` are
    unchanged, because a flush inlay partitions the globe's volume without
    moving the printed solid's boundary. The corrected geometry lives in the
    per-colour bodies under `product/parts/`, and
    `measure/revision-part-hashes.md` and `measure/occurrence-geometry.md` are
    what compare them.

23. **Uranus's one band stood upright and read as a tennis ball; a band is
    also the wrong feature for this planet.** One `white` #FFFEF7 latitude band
    from −9 to +9 stood here. Because the pole lies 7.77° past horizontal that [observed]
    equatorial band stood UPRIGHT on the visible face, and a bold white upright
    stripe on a `cyan` #00FFFF globe is a tennis ball: in the published
    `iso.png` the two Uranus pieces were, with Neptune, the most toy-like
    objects on the board. `ref/uranus-sol.png` is the second-quietest image in [observed]
    the reference folder — a pale, almost uniform sphere with one very faint
    lighter region, soft-edged and off-centre, and no stripe anywhere in it.

    **The truth problem underneath the contrast problem.** A latitude band is
    the wrong feature for Uranus. It points a pole at the Sun for forty years [observed]
    at a time, so what its atmosphere actually shows is a **polar hood** — a
    brighter region around whichever pole is facing out — and the same
    obliquity that stood the old band upright turns a hood face-on. That is the
    shape the reference carries, and it is a different feature from an
    equatorial band that happens to look upright. The band is replaced by a
    `cap` region, the kind the Earth correction added and Saturn's northern cap
    reuses, with its boundary at latitude 60: 30° of arc from the pole, 11.53 mm [assumed]
    across the surface, wide enough to project as a broad region rather than a
    spot. No lobed rim — the Earth lesson about lids was about a small bright
    cap read edge-on against a dark globe, and this is a wide soft brightening
    read face-on.

    **A hood at each pole, and that was measured rather than chosen.** The two
    armies lean opposite ways, so at the product's own two frames the Sol piece
    turns its north pole 61.6° and 60.4° off the view axis and the Anti-Sol [inferred]
    piece turns the same pole 125.3° and 130.5° away — past the limb at both.
    A single northern hood would have been a marking one whole army never
    shows, which is a defect rather than an acceptable asymmetry. Two hoods is
    also what the planet has: the bright polar region follows whichever pole
    faces the Sun, and over one orbit that is both. `measure/uranus-facing.md`
    carries the sweep.

    **`beige` #F7E6DE rather than `white`, measured.** Every filament the shop
    stocks was rendered against the `cyan` globe on this piece by the method
    Mercury's, Venus's, Jupiter's and Saturn's tone corrections used — one
    build, two renders, one region repainted between them, so the pixels that
    move are the hood and nothing else moves at all.
    `measure/uranus-tone-separation.md` carries the table. `white` stayed
    available as the fallback and was not needed.

    **A ring, and it is the largest piece of work in this run.** An earlier
    version of this brief ruled rings out; the owner overruled that and asked
    for a small one. `parts/world.py`'s `_ring_plate`, `_ring_web` and
    `_ring_body` were generalised rather than duplicated:
    `params.RINGED_WORLDS` now names which worlds carry a ring and the
    constants each one is built from, Saturn's block restates its own published
    numbers unchanged, and Uranus's are a parallel block of its own.
    Section 7's "Uranus's ring" carries the geometry, the 1.30 mm wedge [inferred]
    that gets the junction past the 45° gate at 1.00 mm of projection, [assumed]
    and the measured 44.3° steepest downward-facing angle.

    **The ring's colour was decided by the review, not by the rule.** It began
    `white`, which is what this set's other ring wears. An independent reader
    shown only the images, and not told what the set was, named both Uranus
    pieces as tennis balls and gave the mechanism: a bold white curve on a
    saturated ball beside a pale panel. `gray` was tried next and read as a
    MORE convincing seam, because a tennis seam is a dark curve on a bright
    ball. Both were measured: `white` sits 38.9 of 255 luma levels from the [observed]
    globe, `gray` 7.0, and neither number predicted the reading. What did was
    the ring being a different MATERIAL from the ball. In the globe's own
    `cyan` the hoop stops being a marking and becomes relief, read by
    silhouette and self-shadow; its luminance against the globe barely moves,
    so it is no less visible at board scale. The same reader's third pass
    reported the tennis ball gone and the ring still legible both up close and
    across the board. The hood's boundary went from 55 to 60 in the same [assumed]
    repair, which took the cap from about a third of the visible face to about
    a fifth. `measure/uranus-ring.md` carries the decision, the numbers and
    what it costs: this set's two ringed worlds no longer wear the same kind of
    ring.

    **This is the first correction in the chain whose printed parts were
    expected to change.** Every previous one moved a colour boundary, and a
    flush inlay partitions the globe's volume without moving the printed
    solid's boundary, so the corrected parts came out byte-identical and that
    was the right answer. A ring is added material. Both Uranus parts changed
    and the other 22 did not; `measure/revision-part-hashes.md` says which of
    the two statements the hashes support rather than asserting either.

    **Uranus still prints in two filaments** — `cyan` and `beige` — counting
    the globe and its markings and not the disc or the numeral, which every
    world shares. The ring shares the globe's spool, so the set's tally is
    unchanged by this correction: Earth, Jupiter and Saturn four; Mercury,
    Mars, Venus and Neptune three; Uranus two. Items 19, 20 and 21 record the
    tallies of their own runs and are left as they stand. All thirteen spools are the ones the
    set already loaded: `beige` was already Earth's dryland and Jupiter's and
    Saturn's zones, and `white` was already Saturn's ring.

    **One thing this correction cannot fix and does not try to.** `cyan`
    #00FFFF is a saturated neon and `ref/uranus-sol.png` is a pale desaturated [observed]
    ice blue. There is no pale blue in the thirteen filaments this set stocks,
    so the gap between the globe's own colour and the reference cannot be
    closed inside two printed parts, and a paler marking on a neon globe does
    not make the globe paler. It is recorded in the limitations and in
    `product.json` rather than compensated for. Acquiring a pale blue spool
    would reach the belt, the corona flames and the Anti-Sol flames, so it is
    left as a recommendation for a future revision.

24. **Neptune's three cloud bands are back, and that is an owner decision on
    appearance taken against a measured argument that is still in this
    document.** Item 22 is that argument. It was not wrong: `ref/neptune-sol.png` [observed]
    shows clouds that are SHORT, each starting and stopping inside a few tens
    of degrees of longitude, none of them ringing the planet, and three closed
    bands on a blue ball are three painted stripes. The run that made it built
    eight tapered, bowed, tilted streaks and a bright companion wisp, and an
    independent reader confirmed that the beach ball had gone. **The owner has
    looked at both drawings and prefers the older one.** Item 22 stays where it
    is, in full, as the case that was heard and lost; this item records who
    overruled it and on what grounds, which are taste rather than measurement.

    **What went back.** Exactly the three `band` regions the build carried
    before item 22: −46/−41, +11/+15 and +30/+33, `white`, one marking with one
    key. The three pairs were read back off the source's own record of what it
    replaced — the comment in `parts/markings.py` quoting them — rather than
    off the revision brief, and the two agreed.

    **What did not go back.** The **dark spot**. The owner was explicit that it
    stays as item 22 left it: one clean `dark_gray` oval 28 by 14° of arc at
    latitude −22, drawn by `SPOT_RING`. The two overlapping circles that
    preceded it read as a smudge and that finding is not reversed. Measured
    rather than assumed: the `spot` body comes out at 11.9319 mm³ on both [inferred]
    armies, which is what the archived build measured it at, and its dot
    products at the two product frames reproduce the archived +0.53/+0.86 and
    +0.28/+0.70 to two decimals. `measure/neptune-mirror.md` and
    `measure/neptune-facing.md`.

    **What was lost with the reversal, and it is a loss rather than a
    tidy-up.** The spot's **bright companion cloud** is gone. It was `white`,
    and the marking key in this set is the filament, so it was one of the nine
    bodies of the marking that went back to bands; the drawing being reverted
    to did not have one. The reference does show a bright cloud beside the dark
    spot and this build does not draw it. Whether it should survive as a fourth
    white region is a live recommendation rather than a settled question, and
    it is in the product's limitations and in this run's report in those terms.

    **The bands against the nozzle, derived rather than quoted.** One degree of
    great-circle arc on a Ø21.89 globe is π·21.89/360 = 0.1910 mm — **not** [inferred]
    π·d/180, which is 0.3821 and twice the truth. The three bands are 5, 4 and
    3° wide, so **0.955, 0.764 and 0.573 mm**, which is 2.39, 1.91 and 1.43 [inferred]
    nozzle widths at 0.40 mm. The narrowest clears, so **no band was widened**. [inferred]
    The widest bare gap between two of them is 52° of latitude, **9.93 mm**, [inferred]
    between `b1` and `b2`; the tightest gap anywhere on the globe is the 12°,
    **2.29 mm**, between `b1` and the dark spot. [inferred]
    `measure/neptune-atlas-resolution.md` measures all of it.

    **A false claim this chain sealed, corrected in the same report.** The
    archived `measure/neptune-atlas-resolution.md` said this set's other band
    systems are "3.63 to 7.26 mm (Saturn) and 2.35 to 6.12 mm (Jupiter)" and [inferred]
    concluded that Neptune's streaks were "the narrowest marking family
    anywhere in the set". Both figures carry the π·d/180 doubling above.
    Saturn's own report measures its narrowest band, the Equatorial Band, at
    **1.82 mm**; Jupiter's measures its narrowest belt at **1.18 mm** and its [inferred]
    narrowest zone at **1.06 mm**. 3.63 is exactly twice 1.82 and 2.35 exactly [inferred]
    twice 1.18. The conclusion was false even at the corrected numbers: the
    streaks, at 1.35 – 1.65 mm, were WIDER than Jupiter's narrowest zone. The [inferred]
    rewritten report reads those three figures back out of the two reports at
    run time rather than copying them, and states where the comparison now
    falls: Neptune's bands at 0.573 mm are the narrowest **band** family in the [inferred]
    set by a factor of 1.85, though not the narrowest marking of any kind —
    Earth's outback boundary leaves a 0.40 mm strip of green, exactly one [inferred]
    nozzle. `measure/uranus-atlas-resolution.md` had already caught the Saturn
    half of this and left the Neptune report to a future run; this is that run.

    **`b1` is an Anti-Sol-only feature at the two product frames, and it is
    named rather than left to be reported as a missing band.** The Sol piece
    leans its north pole toward the lens, so both of its product cameras look
    DOWN on the northern hemisphere — the state-sheet sub-point sits at +51.5 — [inferred]
    and a camera there reaches a marking at latitude L at best at cos(51.5 − L)
    whatever longitude it is drawn at. `b1` at −46/−41 is south of that reach:
    it measures +0.23 at the Sol hero frame and **−0.04** at the Sol state
    sheet, which is behind the limb. On the Anti-Sol piece it measures +0.70
    and +0.58 and is plainly visible, and at the two level per-world frames it
    is visible on both pieces. That is the same geometric fact item 22 recorded
    about its own `s1` and `s2`, inherited by the band that stands where they
    stood. It is not repairable without moving the band, which the owner's
    instruction forbids. `measure/neptune-facing.md`.

    **Expected to read as a beach ball, and asked anyway.** A closed latitude
    band runs the whole way round the planet, and item 22 called three of them
    on a blue globe the most beach-ball-like object in the set. That judgement
    was not wrong; it was overruled. The blind review of this build is asked
    the question in the same words the Uranus run used — shown `iso.png`, does
    any piece read as a beach ball or a tennis ball, name them — and the answer
    is recorded in `snap/SIGNATURE-REVIEW.json` beside the owner's decision.
    The bands were not softened, moved, narrowed or broken to make that answer
    come out nicer.

    **Nothing else in the set changed.** Both Neptune printed STEPs come out
    byte-identical to the archived build's, which is the whole statement that a
    marking here is a flush colour inlay: it partitions the globe's volume
    without moving the printed solid's boundary.
    `measure/revision-part-hashes.md` and `measure/occurrence-geometry.md`.
    Uranus's ring, its two polar hoods and every Uranus constant are untouched;
    they are corrected in the next run of this pass, not this one.

    **Filament tally, unchanged by this correction.** Thirteen spools. Earth,
    Jupiter and Saturn four; Mercury, Mars, Venus and Neptune three; Uranus
    two. Neptune's three are `blue`, `white` and `dark_gray`, exactly as
    before: the reversal moved white material about, it did not add or remove a
    spool.

25. **Uranus's two polar hoods are gone and its ring is `white`, and both are
    owner decisions on appearance taken against measured arguments that are
    still in this document.** Item 23 is those arguments. Neither was wrong.
    The owner has looked at the finished pieces, does not like the two pale
    discs, and has taken them out; the appearance of his own toy is his to
    decide, and an argument from a reference photograph does not outrank him.
    Item 23 stays where it is, in full, as the case that was heard and lost;
    this item records who overruled it and on what grounds, which are taste
    rather than measurement.

    **What went, and what replaced it.** `("hood_north", ...)` and
    `("hood_south", ...)` were removed from `MARKINGS["uranus"]` entirely.
    Nothing replaced them: no cap, no band, no spot, no quieter tone. Uranus is
    now **the one world in the set with no surface marking of any kind**, and
    that outcome is one item 23's own brief named in advance and called
    legitimate: "Uranus being the one unmarked world in a set of eight is a
    defensible design statement rather than an omission." It was offered there
    as the fallback if no filament measured usable against `cyan`; the
    measurement came back usable at 29.0 luma levels, so the hoods were drawn.
    The owner has taken the fallback anyway.

    **Why a bare world is the right answer on this one.** `ref/uranus-sol.png` [observed]
    is an almost featureless sphere, and the identity of the piece is carried
    by the ring, by the size the ladder gives it and by the `cyan`. It is worth
    naming the condition that keeps that true: bare separates Uranus from its
    neighbours only while it is the only bare world in the set.

    **The ring turns `white`.** `RINGED_WORLDS["uranus"]["colour"]` went from
    `"cyan"` to `"white"`, which is the value `RING_COLOUR` holds as this set's
    default and the spool Saturn's ring already prints from. **After this
    revision there is no exception: both ringed worlds print their ring in
    `white`, and the set's "rings are white" rule holds without a footnote for
    the first time.** The comment under `RING_COLOUR` that recorded the
    exception is corrected.

    **Nothing moved.** Neither change touches a surface. Removing a flush inlay
    stops partitioning the globe; repainting the ring moves one existing body
    from one spool to another. So **both Uranus printed STEPs come out
    byte-identical to the published set's** -- `7eccfab310b21fef` and [observed]
    `d993913622975638` -- and that is the check this run turns on rather than a
    formality: if either hash had moved, something had moved the ring or the
    globe. 20 of the 24 printed geometries are byte-identical; the four board
    panels differ in exactly one line each, a
    `NEXT_ASSEMBLY_USAGE_OCCURRENCE` exporter counter carrying no geometry,
    diffed line by line in this run rather than asserted.
    `measure/revision-part-hashes.md`.

    **Measured on the solids.** The assembly's occurrence count goes 224 -> 220, [observed]
    which is exactly the four hoods and nothing else. Each globe gains exactly
    the hoods it lost: 5323.412 + 109.5887 + 109.5887 = 5542.588 mm³, residue
    -0.0014 mm³ on both armies. The ring's volume is identical to nine decimal
    places at 54.830480 mm³ (Sol) and 54.830494 mm³ (Anti-Sol), in the same
    bounding box, and the 45° gate still measures 44.3° with 0.0000 mm² over
    the gate on both armies. Saturn's two ring occurrences come out at
    574.192167 and 574.192096 mm³, zero delta. `measure/uranus-bare.md`,
    `measure/uranus-ring.md`, `measure/uranus-mirror.md`,
    `measure/saturn-ring-unchanged.md`, `measure/occurrence-geometry.md`.

    **What the piece now has to carry on its own**, checked rather than
    assumed, in `measure/uranus-neptune-separation.md`,
    `measure/uranus-saturn-separation.md` and
    `measure/uranus-earth-separation.md`. Against Neptune, its neighbour in
    rank and in colour family, size cannot help -- Ø22.02 against Ø21.89, less
    than one nozzle apart -- so the separation is surface and silhouette: a
    bare ball with a hoop against a banded ball with a spot. Against Saturn,
    the other ringed world, **the colour of the ring no longer helps at all**,
    since both are now `white`; what is left is orientation and size, a flat
    plate lying almost level at Ø30.00 against an upright hoop at Ø24.02, and
    one piece wider than it is tall against one taller than it is wide.
    Against Earth the two globes are four ranks and two spools apart.

    **The filament count falls.** Uranus's piece loads **three** spools where [observed]
    it loaded **four**: disc, numeral, globe and ring, against disc, numeral,
    globe, hoods and ring. By the tally this document keeps -- the globe and
    what stands on it, disc and numeral excluded -- Uranus is still two, and
    the two are different ones: `cyan` plus `beige` has become `cyan` plus
    `white`. This is the first correction in the chain to make a world simpler
    to print.

    **The `cyan` limitation stands, and this revision makes it MORE visible.**
    `cyan` #00FFFF is a saturated neon; `ref/uranus-sol.png` is a pale [observed]
    desaturated ice blue, its ball measuring 161, 200, 206 against the
    filament's 0, 255, 255. There is no pale blue anywhere in the thirteen-
    colour palette; the only other blue is a dark navy, further away. With the
    hoods gone there is now nothing else on the globe to look at, so the gap is
    more exposed than it was. That is an honest cost of the decision rather
    than an argument against it. `measure/uranus-reference.md`.

    **The reading the owner is overruling, tested rather than assumed.** The
    reason the ring went `cyan` was a blind reviewer who, shown the board cold,
    named both Uranus pieces as tennis balls, twice, and gave the mechanism in
    his own words: "a bold white curved line arcing down one side of a
    saturated-colour ball, and a large pale panel on the opposite side." That
    mechanism has TWO halves and this revision removes one of them -- after the
    hoods came off there is no pale panel anywhere on the piece. Whether a
    white hoop alone on a bare `cyan` ball still reads as a seam is an open
    question, and it is put to this build's blind review as its own question,
    unprimed, at board distance on `iso.png` and close up on the piece, rather
    than assumed in either direction. The answer comes back in the reviewer's
    own words in `snap/SIGNATURE-REVIEW.json` and is reported beside the
    measured separation, which `measure/uranus-ring-tone.md` puts at 38.7 to
    39.3 of 255 luma levels across the three canonical frames. **The ring's
    filament is not changed back whatever the answer is, and nothing is added,
    tinted or softened to compensate.** If the answer is still "tennis ball",
    that is reported plainly with the number beside it and a recommendation for
    the owner to decide.

    **One frame was added to the review set, and it is a lesson about evidence
    rather than about this toy.** The first attempt at this correction built
    the object correctly and could not seal, because the critic was shown
    sixteen frames of which twelve were Uranus detail views and not one let the
    eight globes be compared at a single scale -- and this set's whole
    ownership claim is that a planet's size on the board is the fifth root of
    its real diameter, so rank is something you can SEE. `snap/rank-ladder-sol.png`
    is that frame: all eight worlds of one army at one orthographic camera and
    one framing box, in rank order. `world_views.py` photographs the ladder and
    does not touch it; `LADDER_CONSTANT`, `LADDER_EXPONENT` and every `globe_d`
    are read and never written.

    **Evidence that no longer measures anything is retired rather than dropped
    or kept quietly.** `measure/uranus-facing.md`, `measure/uranus-tone-
    separation.md` and the two hood evidence renders measured the hoods.
    `measure/retired-hood-evidence.md` names each one, says what it measured,
    and says whether it was carried forward under a heading or removed and why.
    The per-piece polar and south-polar renders stay: a bare globe photographed
    down its own pole is still the right way to show there is nothing there.

26. **Mercury's and Venus's two armies were the same piece twice, and the fix
    is a mirror in the map rather than a lean that does not exist.** This is a
    DEFECT found by the owner, not a reversal of anything: his words were that
    looking from one side, the Mercury and the Venus of both armies are on the
    same side, and that these two planets should be flipped.

    The cause is arithmetic rather than anyone's mistake. §3 makes the mirror
    out of the lean: `planet_frame` turns the Sol globe by +tilt and the
    Anti-Sol globe by −tilt. At Mars's 25.19° or Earth's 23.44° the two pieces
    stand 50.38° and 46.88° apart and the difference is obvious across a table.
    Mercury's obliquity is **0.03°**, so its two pieces differ by 0.06°.
    Venus's is **177.36°**, and +177.36 against −177.36 is not 354.72° apart —
    it is the same turn measured each way round, so the angle between them is
    360 − 2 × 177.36 = **5.28°**. Both are nothing.
    `measure/pair-separation.md` reports that angle for all eight worlds.

    **The obliquities are observed facts and do not move.** `params.PLANETS` is
    untouched, `params.lean_sign` is untouched, `features.planet_frame` is
    untouched. Inventing a lean would be correcting the planet rather than the
    piece.

    **So the mirror is taken from the longitudes**, which item 10 records were
    never observations on these two worlds: `mercury_atlas.CALORIS_LON = −50`
    and `venus_atlas.LONGITUDE_OFFSET = +90` are camera decisions, solved by
    earlier runs so that the features face the lens. That is exactly what makes
    them available to mirror, and exactly what makes the obvious flips
    dangerous. Measured on Caloris at the hero frame: negating longitude sends
    it from −50 to +50 and it reads **−0.021**, the limb precisely. Reflecting
    through the lean's own mirror plane, L → 180 − L, sends it to +230 and it
    reads **+0.395** — 80° off the camera meridian, a glancing three-quarter
    view of the one feature this globe is recognised by. Both obey the
    instruction and both ruin the piece.

    **The transform that does both jobs is a reflection about the piece's own
    FACING MERIDIAN.** Carry the camera direction back into that globe's planet
    frame — `planet_frame` inverted — and take its longitude, C. Map every
    marking longitude L to **2C − L**. Facing is the dot product of a marking's
    direction with the view axis, and in the planet frame that is
    cos(lat)·cos(lat_C)·cos(L − C) + sin(lat)·sin(lat_C): longitude enters only
    through cos(L − C), and cos((2C − L) − C) = cos(L − C). So the reflection
    preserves the facing of every point **exactly**, at any obliquity, while
    swapping left and right as the camera sees it. Confirmed numerically rather
    than taken on trust — swept over a 33 × 72 grid of latitudes and longitudes
    at both frames on both worlds, the largest change in the dot product is
    6.66 × 10⁻¹⁶.

    **There are two photographed frames, so there are two values of C**, about
    ten degrees apart, and one reflection has to serve both. Mercury takes the
    plain circular mean of the two, **−49.99°**, and every Mercury feature that
    clears the +0.30 facing floor on the Sol piece still clears it on the
    mirrored piece, by 0.052 at the worst. Venus's mean does not clear:
    Atalanta Planitia reads +0.367 on the Sol piece at the hero frame and falls
    to +0.266 on the mirrored one. Rather than accept that, the meridian was
    swept at a hundredth of a degree and moved **+5.00°** to **−123.85°** —
    which is the whole number beside the sweep's own optimum at +4.98, and
    which amounts to solving Venus's reflection about the hero camera's own
    meridian rather than the mean, because the hero frame is the one Atalanta
    is tight at. `measure/mirror-meridian.md` carries the sweep, both traps and
    every ring's facing at both frames on both pieces.

    **Where the transform lives.** `MARKINGS` in `parts/markings.py` was keyed
    by planet alone and read in five places in `parts/world.py` — the raw
    union, the region builder twice, the body assembly and the absent-key
    check. All five now call **`markings_for(planet, side)`**, a single
    function that returns the same structure `MARKINGS` returns and applies the
    reflection only when the planet is one of the two named and the side is
    `anti`. One place owns the transform and every consumer is unchanged in
    shape. For the six untouched worlds on both sides, and for the two
    corrected worlds' Sol pieces, it returns the table's own list — the
    identical object, not a copy — and `measure/markings-refactor.md` checks
    all sixteen cases. Uranus's entry is empty since item 25 and survives
    unchanged; there is no branch that names it.

    **What it costs, stated plainly.** A reflected map is a MIRROR-IMAGE map.
    The Anti-Sol Mercury's Caloris rim is handed the other way from the real
    basin's, and so are the Anti-Sol Venus's provinces. Latitude, size, shape
    and count are untouched, and so is every dimension of both pieces —
    `part_world_mercury_anti.step` and `part_world_venus_anti.step` come out
    byte-identical to the published set's, because a flush inlay partitions the
    globe without moving its surface. The mitigation is real and is most of the
    answer: on these two worlds longitude was never a map fact, so what is
    mirrored is a placement this project chose rather than an observation it
    made. **Which worlds are drawn at real longitudes and which at solved
    ones**, from this project's own records: Earth's coastlines and Mars's
    albedo map are drawn at their real longitudes, and so are Saturn's and
    Neptune's bands and caps, which are latitude features with no longitude to
    get wrong. Jupiter's Great Red Spot was carried 110° for the camera (item
    10). Venus's whole map carries +90° for the camera. Mercury's Caloris was
    placed at −50° for the camera, and its seven plains keep the centres the
    round-patch build used. Uranus carries nothing.

    **Jupiter has the same condition and is deliberately not in scope.** Its
    obliquity is 3.13°, so its two pieces stand 6.26° apart — third-worst in
    the set, and in the same family as Mercury's 0.06 and Venus's 5.28.
    Measured on the built bodies at the two photographed frames, its markings
    move 1.24 mm between the two pieces on the frame that separates them least, [observed]
    which is **9% of its globe radius**. The four marked worlds whose lean is
    not degenerate move 43% to 73% of their own radius — Earth 43, Mars 53,
    Neptune 55, Saturn 73 — and the two this run corrects now move 36%
    (Mercury) and 56% (Venus) — where before the correction they moved 0.004 mm [observed]
    and 0.528 mm, which is 0% and 6%. The same measurement run with [observed]
    `markings.MAP_MIRRORED_WORLDS` emptied is
    `measure/pair-separation-before.md`, and the other six worlds read
    identically in both, which is the control. Jupiter is the one world left in
    the set that reads as one object photographed twice. The owner named Mercury and Venus and did not
    name Jupiter, so it was measured and left alone. The recommendation is in
    `README.md`. Mars at 25.19°, Earth at 23.44°, Saturn at 26.73°, Neptune at
    28.32° and Uranus at 97.77° are all far from degenerate — 50.38°, 46.88°,
    53.46°, 56.64° and 164.46° between their two pieces — which is the negative
    half of the same check and is why the recommendation is scoped to Jupiter
    alone.

27. **The trap tiles lose their two raised tongues, so the star's flames are
    the only raised flames on the board.** This is an owner decision on
    appearance and is recorded as one. It reverses nothing that was measured:
    the tongues were never argued for at length, they were simply part of the
    corona cell from the first draft.

    Dou Shou Qi puts a den at each end and three traps around it. Here the den
    is the star and the traps are the corona wells. §6 gave the star two flames
    standing 18.00 mm above the field and gave **every** corona tile two more [assumed]
    at 4.00 mm, at the two corners of the edge furthest from the star: three [assumed]
    traps per side, two tongues each, two sides — **twelve small horns around
    the two stars' four**. The owner wants the trap tiles flat.

    **The two raised bodies are removed and nothing replaces them.** The
    sixteen tongues cut 0.40 mm INTO the tile's top face stay exactly as they [assumed]
    are — count, inner radius, eye and depth — because they are not horns: they
    are the star's light on the floor of the well, they are the reason a trap
    reads as a trap with a world standing in it, and they are engraved
    precisely so a seated disc cannot rock on them. The result is a tile whose
    only feature is a sunken sixteen-rayed star.

    **What the tile becomes**, measured in `measure/corona-flat.md`: one solid
    where it was one fused body with two flames on it; **3.00 mm tall where it [assumed]
    was 10.00**; a plain rounded-square extrusion with an engraving in its top
    face. `part_corona_cell.step` is the one printed geometry in this revision
    whose bytes had to move, and byte-identical would have meant the tongues
    were still on it.

    **Four constants are retired.** `CORONA_TONGUE_BASE_D`, `CORONA_TONGUE_H`,
    `CORONA_TONGUE_TIP_R` and `CORONA_TONGUE_DIAGONAL` have no remaining
    consumer and are removed from `params.py` rather than left behind as dead
    numbers; the whole project was searched for each of them first, source,
    measurement scripts and report generators alike, and `parts/corona.py` was
    the only reader. The retired values are recorded in
    `measure/corona-flat.md`.

    **The placement rotation goes with them.** `assemblies/product.py` had a
    function `_away_from_den` whose whole job was to turn each corona tile so
    its tongues pointed away from the star. With no tongues, a rounded square
    carrying a sixteen-fold engraving — whose tongues alternate two lengths, so
    it repeats every 45° — is the same tile at any quarter turn. The rotation
    is dropped rather than kept as a turn through nothing, and that the placed
    occurrences did not move is measured rather than argued: the symmetric
    difference between the tile and the tile turned 90°, 180° and 270° is zero
    to the kernel's own noise, so the assembly's interference and
    occurrence-geometry checks keep exactly the meaning they had.

    **The storage trays do not move.** `assemblies/product.py` parks them well
    clear of the board, and the reason recorded there was that at the fixed
    product viewpoint a tray near the far edge cuts through a corona tongue in
    projection. That reason is spent. `TRAY_Y` is a composition decision every
    whole-set render is framed around, so the distance is kept deliberately and
    the comment now says what it actually buys rather than what it used to.

    **What the removal buys, measured rather than asserted**, in
    `measure/corona-flat.md` and `measure/overhang-corona_cell.md`: the
    overhang gate, the clearances, the packing and the print. The tightest
    thing on the tile was the 0.70 mm the tongues kept from a seated disc at a [inferred]
    20.20 mm diagonal; that constraint is gone with the feature, and what is [inferred]
    left is a plane — the tile's highest surface is now the floor a trapped
    world stands on, so no part of any world, including Saturn's Ø30.00 ring
    and Uranus's hoop, can reach anything on a trap tile.
    `measure/seated-piece-clearance.md` measures that on all sixteen pieces of
    both armies. The well's own 3.00 mm drop and its 0.40 mm of slip per side [assumed]
    are unchanged and are derived there from the board's and the tile's own
    constants rather than quoted.


28. **Jupiter's two armies were the same object photographed twice, and the
    fix is the one Mercury and Venus got — but almost nothing on this globe
    carries a longitude, so it needed a meridian solved for VISIBILITY.**
    This changes exactly one printed part, `part_world_jupiter_anti`, and
    `part_world_jupiter_sol` does not change. It supersedes item 26's closing
    paragraph, which measured this defect and left it out of scope.

    **The defect was measured, not guessed.** Item 26's run handed its eight
    pairs to an independent critic one pair at a time, cold, with the base
    colours excluded, and asked which were two different objects. It answered
    eight of twelve comparisons as different and named this pair as the
    exception: *"Left ball: red oval at dx = +3. Right ball: dx = +7... I
    cannot tell these apart and I would not notice if you swapped them."* And
    of the set: *"Seven of eight are genuine mirror pairs. Jupiter is the one
    that is not."* That quotation is recorded history from the source archive
    and is not this run's evidence for anything; this run's own blind review is
    `snap/SIGNATURE-REVIEW.json` and `measure/signature-review-protocol.md`.

    **The cause is arithmetic and the obliquity does not move.** Jupiter's
    tilt is 3.13°, so `planet_frame(tilt, +1)` and `planet_frame(tilt, -1)`
    leave the two pieces 6.26° apart — third-smallest in the set, in the same
    family as Mercury's 0.06 and Venus's 5.28. `params.PLANETS` is untouched,
    `params.lean_sign` is untouched and `features.planet_frame` is untouched.
    The defect is CAUSED by that tilt, so inventing a lean would be correcting
    the planet rather than the piece.

    **The machinery already existed and no second mechanism was written.**
    `markings.MAP_MIRRORED_WORLDS` gains `"jupiter"` and
    `markings.MERIDIAN_ADJUSTMENT` gains one number. `markings_for` and
    `reflect_longitude` are unchanged.
    `measure/markings-refactor.md` re-checks all sixteen cases.

    **And here is what is not like Mercury and Venus.** Most of this globe is
    INVARIANT under a longitude reflection. Its six belts and five zones are
    circles of latitude, and a circle of latitude has the same longitude
    everywhere, so a reflection does not move it at all — `_mirror_spec`
    returns a `band` and a `shell` spec as the identical object rather than
    rebuilding it. Measured in `measure/jupiter-mirror.md`: **9 of this
    globe's 13 region specs are returned unchanged and 4 are reflected.** The
    four are the Great Red Spot, its collar and the two wavy belts, which are
    built as longitude sectors. The whole mirror read falls on one oval whose
    length is 3.06 mm -- 13 degrees of arc at 0.2354 mm each. [inferred]

    **And the spot was in the worst possible place for it.** Its longitude is
    −48.00 and this world's mean facing meridian on the Anti-Sol piece is
    **−48.7675** — 0.77° away, because at a 3.13° tilt the two cameras carry [observed]
    back into the planet frame almost unchanged. Reflecting a feature at L
    about a meridian C lands it at 2C − L, so the swing is twice the distance
    from the feature to the meridian: at the plain mean the spot would move
    **1.54° of longitude, 1.42° of great-circle arc, 0.33 mm** — and westward, [inferred]
    the wrong way for a spot already west of the meridian. That is not a
    mirror, it is a rounding error, and it would have produced a piece whose
    hash changed and whose appearance did not.

    One degree of great-circle arc on this Ø26.97 globe is π × 26.97 / 360 =
    **0.2354 mm** — a 360th of the circumference, not π × d / 180. [inferred]

    **So the meridian was solved instead, and scored on two things at once.**
    `MERIDIAN_ADJUSTMENT["jupiter"] = +15.00`, giving a meridian of −33.7675.
    The sweep is in `measure/mirror-meridian.md`, at a hundredth of a degree
    over ±40°, and it reports two scores per world: the ring-centroid margin,
    which is the gate this chain has used since Mercury, and the stricter
    every-vertex margin the Jove brief asked for. On the stricter score every
    vertex of the spot and its collar clears the +0.30 facing floor at both
    photographed frames on both pieces for any adjustment in **−15.55 to
    +21.57**, and the margin peaks at +3.01 with 0.1768. The rule taken was to [observed]
    take the LARGEST whole degree that still keeps at least half that peak:
    +16 keeps 0.0865 and falls short, +15 keeps **0.0995** and is what is
    taken. It is a value inside the clearing range with margin, not at its
    edge.

    **What it buys, in the units a reader has.** The spot lands at −19.54: a
    swing of **28.46° of longitude, 26.35° of great-circle arc, 6.20 mm** on a [inferred]
    ball 26.97 mm across — two spot-lengths. [inferred] At the world's own
    `spot` frame the spot sits 0.21 mm left of the ball's centre line on the [observed]
    Sol piece and **6.15 mm right of it** on the Anti-Sol piece. Measured on [observed]
    the built
    bodies at the two photographed frames, Jupiter's markings now move **4.661
    mm between its two pieces on the frame that separates them least, 35% of [observed]
    its globe radius**, against 0.78 mm and 6% in item 26's own measurement [observed]
    of the same thing. `measure/pair-separation.md` is that table for all eight
    worlds, and every marked world in the set now reads as two different
    objects.

    **The twelve belt sectors are not twelve features and are not gated as
    such.** Each wavy belt is drawn as six 60° longitude sectors that seam
    together into one band closed right round the globe, so asking whether
    sector 6 still faces the camera asks the wrong question — the belt has
    material at every longitude on both pieces, and the reflection changes
    which sector is in front of the lens, not where the belt is. That closure
    is MEASURED rather than asserted in `measure/mirror-meridian.md`: the
    sectors are sorted by their western edge, each one's eastern edge is the
    next one's western edge to 0.0e+00 degrees, and the spans total exactly
    360.0000 on both pieces. The floor is then applied to the belt whole, and
    the best facing of each belt CHANGES BY at most +0.042 between the two
    pieces.

    **The belt's hollow follows the spot with no special case.** The South
    Equatorial Belt's southern boundary bends 7.0° north over the spot, and
    that bend is drawn into the sector rings, so the reflection carries it
    along. Measured on the built rings in `measure/jupiter-mirror.md`: the
    boundary's northernmost point is at longitude −48.00 on the Sol piece and
    **−19.54 on the Anti-Sol piece — the reflected spot's own meridian,** at [observed]
    latitude −13.00 against its unbent −20.0 on both.

    **No latitude moved anywhere.** A longitude reflection maps (lon, lat) to
    (2C − lon, lat) and latitude is not in the transform. Checked vertex by
    vertex against the Sol ring each vertex came from: the largest latitude
    change across all 14 rings and 308 vertices is **0.00e+00**. The spot sits [observed]
    at latitude −22.00 on both pieces, and the six belt latitudes are the ones
    `jupiter_atlas.BELTS` declares — widths 7, 10, 13, 7, 5, 6, no two of them
    a mirror of another.

    **What it costs, stated plainly.** Two things, and both are in
    `product.json`'s limitations as well as here. **The Anti-Sol Jupiter's Red
    Spot sits at a longitude that is not the real one** — −19.54 against the
    Sol piece's −48.00. **And the wave phase of its two widest belts is handed
    the other way**; each boundary carries two harmonics of longitude, so
    reflecting longitude reflects the pattern. A reader cannot tell a handed
    wave from an unhanded one without the other piece beside it, which is the
    comparison this correction exists to win, and the amplitude is 2.5° either
    way on both pieces.

    **The mitigation is real and is most of the answer.** Longitude on this
    globe was never a map fact. Item 10 records `SPOT_LON` as chosen to put the
    spot in front of the cameras — the same decision `mercury_atlas.CALORIS_LON`
    and `venus_atlas.LONGITUDE_OFFSET` are — and Jupiter turns in ten hours
    with no fixed meridian anywhere in this set. Latitude, size, shape and
    count are untouched, and those are the four things a reader could check
    against a photograph.

    **The printed solid did not move.** `part_world_jupiter_anti.step` is
    byte-identical to the published set's, because a flush colour inlay
    partitions the globe without moving its surface. The change lands in the
    per-colour bodies, and `measure/occurrence-geometry.md` names exactly which
    of the 220 moved: `jupiter_anti_spot_red`, `jupiter_anti_collar_cocoa_brown`,
    the two wavy `jupiter_anti_bands*` bodies and the three
    `jupiter_anti_zones*` those belts trim. **Nothing outside
    `jupiter_anti_*` gained, lost or moved a solid.**

    **After this run, three of eight worlds carry a mirrored map and five carry
    one map at two leans.** The rule is that a world joins the mirrored set
    when the angle between its two pieces' leans is too small to show the
    mirror, and the set is nowhere near the boundary: the three sit at 0.06,
    5.28 and 6.26° and the five at 46.88 (Earth), 50.38 (Mars), 53.46
    (Saturn), 56.64 (Neptune) and 164.46 (Uranus). The gap between the groups
    is 40.62° wide. `measure/mirror-set-consistency.md` is that table, and it
    also records why Venus is mirrored despite a 177.36° obliquity and why
    Uranus is not mirrored despite a pair a reader finds hard to read.


## 12. What this run does not prove

No part of this run demonstrates physical printing, dimensional accuracy on a
real bed, material durability, tactile comfort, colour accuracy against real
filament, or human play. Earth's coastlines are a stylised silhouette atlas and
not a survey coastline: Central America is one broad land bridge, the Indonesian
arc is left to the sea, and the atlas carries no Antarctica and no southern ice,
so neither is present — stated here rather than left to be noticed. Mars's
albedo rings are the same kind of thing at the accuracy an eyepiece sketch has,
not spacecraft mapping: they are the classical albedo map, they carry no relief
and no crater, and the features listed in `parts/mars_atlas.py`'s `NOT_DRAWN`
are absent on purpose and for stated reasons. Mars is also the world whose
southern hemisphere the disc eats: the globe is sunk 2.00 mm and cut at the disc [assumed]
top, which on a Ø14.72 ball removes about 14% of the sphere and with it the
south polar cap almost entirely, so the southern cap is barely visible on either
army and the southern belt is cut where it runs low. Mercury's rings are
weaker evidence again, and deliberately so: they are generated from a formula
rather than carried from any map, because the planet's albedo boundaries are
soft and unnamed and there is no silhouette to be faithful to. What they claim
is that Mercury's surface is smooth plains of unequal shape with one large
ringed basin in it, not that any particular plain is anywhere in particular.
Caloris's latitude and size are real; its longitude is a camera decision and is
said so. Mercury's `cocoa_brown` plains are also a warm brown rather than a
neutral grey, so at a glance they sit in the same family of colour as Mars's
albedo and Saturn's and Jupiter's bands; that is the price of the separation
measured in item 18 and it was paid deliberately, the neutral alternative being
the tone this revision exists to replace. Venus's rings are a fourth kind of evidence again, and the one with the most
between the picture and the plastic. They are a province map traced from a
radar mosaic, and the mosaic's own subject is the surface read *through* an
opaque atmosphere rather than seen. What they claim is that Venus has a long
equatorial highland with a handful of smaller highlands and three broad lowland
plains around it; they do not claim any boundary is where Magellan put it.
Aphrodite Terra's sweep is the one silhouette on the globe a reader can match
against the image, and everything else on it is a shape the reader has to take
on trust. **None of the reference's texture survives** — one degree of arc is
0.1443 mm here and the nozzle is 2.77 degrees of it, so the tesserae, lava [inferred]
channels and fracture belts that make the mosaic look like beaten gold are each
about a fifth of one nozzle width — and none of it is faked with stippling or
ribs. The piece is a simplified map of the reference, not the reference, and it
will not be mistaken for it. One whole province, Ishtar Terra, is drawn and
cannot be seen at all, because at 177.36° of obliquity the planet's north pole
is inside the collar the globe stands in; 36% of Atalanta Planitia goes the
same way. Ishtar is not absent from the plastic — 3.04 mm³ of `beige` survives [observed]
above the disc's cut and prints inside the collar where nothing can see it — so
a reader counting colour bodies finds one with no picture. And Venus's `beige` highlands separate only 20.2 of 255 luma levels [observed]
from the amber globe as the canonical renders show them, the thinnest marking
separation in the set — it reads because Aphrodite is 117° of longitude wide
rather than because the tones are far apart, and a smaller feature in that pair
of filaments would not.

The two sealed Earth reference
images, `ref/earth-sol.png` and `ref/earth-anti.png`, show the round-patch
surface an earlier revision replaced and are no longer the authority on Earth's
markings; the two Mars images, `ref/mars-sol.png` and `ref/mars-anti.png`, are
the authority the Mars revision was corrected against, the two Mercury
images, `ref/mercury-sol.png` and `ref/mercury-anti.png`, are the authority
Mercury was corrected against — except for their crater field, which is
deliberately not drawn for the reason and at the number item 18 gives; and the
two Venus images, `ref/venus-sol.png` and `ref/venus-anti.png`, show the pale
cream cloud tops and are **superseded for the globe surface and the globe
colour of those two parts only**. Everything else those two show — the disc,
the numeral, the proportions, the seat collar, the lean and the disc filaments
— still holds and is still authoritative, so the pale cream globe in them is
not evidence that this correction failed. Everything else all eight show — the
disc, the numeral, the proportions, the lean and the filaments — still holds,
and every other image in `ref/` remains fully authoritative.

**The reference set is not wholly AI-generated any more.** The twenty sealed
images under `ref/` are AI-generated and their notes state that no web imagery
was used. `ref/venus-radar-surface.png` is the twenty-first and is different in
kind: a supplied photographic dataset image, the Magellan global radar mosaic
at 224x224, **supplied by the owner** rather than generated, and the authority
for Venus's globe surface and globe colour. It is recorded that way here so no
later reader describes the set's references as one thing. The renders are flat-shaded with no ground
plane and no shadows, which costs the reader real information: a `black` disc
comes out as a featureless silhouette with no visible top face or rim, the two
storage trays read as floating because nothing under them is drawn, and the
seven-segment numerals sit on the disc wall facing the two seated players, so
at the product's own oblique frame they are turned nearly side-on and cannot be
read. All three are properties of this renderer, not of the solids; the
numerals read correctly in the per-world frames under `snap/worlds/`.
Jupiter's belt system is a fifth kind of evidence again. Its six latitudes are
the real ones and its Great Red Spot's latitude and proportions are the real
ones, but the wave on its two widest belt boundaries is not Jovian data: it is
two harmonics of longitude summing to 2.5° of arc, chosen to take the lathe [assumed]
look off an exact circle of latitude, and it corresponds to no feature on the
planet. What the piece claims is that Jupiter's belts are unequal, unevenly
spaced and not symmetric about its equator, that bright zones alternate with
them, and that one oval storm sits in the southern tropics with the widest belt
bending round it. It does not claim any boundary is where a particular image
put it. **None of the reference's fine detail survives** — the white ovals, the
polar hoods, the festoons, the plumes and the filamentary turbulence along
every belt edge are each one to two nozzle widths across or less at 0.2354 mm [inferred]
per degree of arc — and none of it is faked with stippling or ribs. The
collar's southern arc and the South Temperate Belt are one continuous region of
the same filament over 11.7° of longitude, for the reason item 20 gives.
Neptune's cloud bands are a seventh kind of evidence, and the one where the
piece departs furthest from its own reference — further, now, than it did
before this revision. **What the piece claims about Neptune's clouds is only
that they are white, that there are three of them, that they are unequal in
width and unevenly spaced, and that the widest is in the southern
mid-latitudes.** It does NOT claim that they are the shape the reference shows.
`ref/neptune-sol.png` shows clouds that are SHORT: each starts and stops inside
a few tens of degrees of longitude, they sit at slightly different angles to
the parallel, they are scattered across the face rather than ringing it, and
not one of them circles the planet. These three bands each circle the planet.
That is a deliberate reversal, taken by the owner on appearance against a
measured argument that is still in this document at item 22, and item 24
records it. It is not softened here and it is not defended by the reference,
because the reference does not support it.

Two smaller departures ride on it. The reference shows a **bright companion
cloud** beside the dark spot; the build this revision corrects drew one and
this build does not, because the companion lived in the white cloud marking
that went back to bands. And the bands are drawn at 3 to 5° of arc where the
reference's own wisps scale to 0.13 – 0.26 mm here, under one nozzle width, so [inferred]
no drawing of those clouds at their own width is printable at all. What the
piece CAN claim without qualification is the dark spot: one oval twice as wide
as it is tall at latitude −22, which is in the reference, which is measured,
and which this revision did not touch.

Saturn's band system is a sixth kind of evidence, and the one where the gap
between the picture and the plastic is a property of the process rather than of
the data. Its five latitudes are a reading of `ref/saturn-sol.png` rather than
Saturnian data, and the 2.5° wave on its two widest boundaries corresponds to [assumed]
no feature on the planet; what the piece claims is that Saturn's bands are wide,
unequal, unevenly spaced, not symmetric about its equator, low in contrast, and
that its northern third is lighter than its southern. **What it cannot claim is
a soft edge.** The reference's bands fade into one another and a flush colour
inlay cannot: every boundary on this globe is a colour change at a line, and
lowering the contrast is the substitute rather than the cure. The band
separation itself is the smallest this project has committed to — 9.4 of 255 [observed]
luma levels against the globe — and it is reported as such rather than called
clear. Nothing else the reference or the planet shows is on this globe: no
hexagon, no vortex, no storm, no ring spoke, no ring division and no ring
shadow, each rejected on the arithmetic in item 21 rather than on taste. And
Saturn shares `sunflower_yellow` with Venus's whole globe from this run onward,
so the two pieces rest on size and silhouette rather than on surface; that is
measured in `measure/venus-saturn-separation.md` and stated there without being
rounded up.

**Uranus's globe claims nothing at all, and that is the seventh kind of
evidence in this set.** Since item 25 it carries no marking, so there is no
reading of `ref/uranus-sol.png` on it to defend and no soft edge to fail to
reproduce. What the bare piece claims is the weakest claim any world here makes
and the easiest to check: that this planet is quiet. The image supports it —
a pale, almost uniform sphere with one faint, soft-edged, off-centre lighter
region and no stripe. It stops short of the image in one direction, which is
worth stating rather than glossing: the reference's one faint lighter region is
not drawn, because the owner removed the feature that drew it. The measured
case for drawing it is kept whole at item 23 and the hoods' own separation
figures are carried forward, under a heading saying the feature is gone, in
`measure/uranus-tone-separation.md` and `measure/retired-hood-evidence.md`.

**And the globe's own colour is wrong and cannot be
made right here**: `cyan` #00FFFF is a saturated neon against a pale [observed]
desaturated ice blue, there is no pale blue in the thirteen filaments this set
stocks, and no marking on a neon globe makes the globe paler. **This revision
makes that gap more visible rather than less**, because with the hoods gone
there is nothing else on the ball to look at. That is an honest cost of the
owner's decision, not an argument against it.

The ring is the eighth kind, different in kind from every other, and is the one
feature in this set that is not evidence of anything the reference shows. **`ref/uranus-sol.png` does not show
a ring.** It is an owner instruction that overruled an earlier version of its
own brief, recorded as exactly that here, in `product.json` and in
`measure/uranus-ring.md` rather than dressed up as an observation. It is
defensible on its own terms — Uranus has thirteen narrow rings and they are too
faint for this image to carry — and none of them is drawn: at 0.1922 mm [inferred]
per degree of arc the real ring system would be grit, so what the piece
carries is one solid hoop standing in the planet's true equatorial plane. Motion
verification is switched off for this run and
is recorded as unverified, never as passed. The clearances, wall thicknesses
and overhang margins above are geometric measurements on the exact CAD solids
and predictions for the printer named in `README.md`.
