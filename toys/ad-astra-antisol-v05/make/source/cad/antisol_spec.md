# Antisol Hesper — design contract

Dou Shou Qi, unchanged, played with the eight planets ranked by their real
measured diameters. Matter faces antimatter, and you win by walking one of your
worlds into the rival sun.

*Hesper* is the evening star, the name Venus carries when it is the brightest
thing in the west, and this revision is Venus's: the world that used to wear
its clouds now wears the ground underneath them. Section 11, item 19 is the
correction; nothing else in the set changed.

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
  in the planet's own frame in angles rather than millimetres, then rotated by
  that planet's true obliquity. Describing them as angles is what lets one
  minimum outline width hold from Mercury to Jupiter. **Four of the eight
  worlds are described by latitude, longitude and angular size** — Neptune,
  Uranus, Saturn and Jupiter — because a union of round patches or a belt of
  latitude is what a cloud pattern, a band system or a storm actually is.
  **Earth, Mars, Mercury and Venus are the four exceptions and are described
  by outline**: a closed ring of longitude/latitude vertices per feature,
  taken from a stylised outline atlas (`parts/atlas.py` for Earth,
  `parts/mars_atlas.py` for Mars, `parts/mercury_atlas.py` for Mercury,
  `parts/venus_atlas.py` for Venus), swept into the globe as the radial cone
  through the ring and trimmed to the same 1.20 mm depth. [assumed]

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
  is the one thing it does not read as. The remaining four keep their round
  patches and their bands, and for those a circle is not a compromise but the
  honest shape: a storm in an atmosphere really is a round patch, and
  Jupiter's Great Red Spot and Neptune's dark spot stay round for that reason.

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
| `white` | Sol disc, Anti-Sol numeral, Mercury Caloris floor, Mars caps, Earth ice, Uranus band, Neptune streaks, Saturn ring |
| `sunflower_yellow` | Sol den plug, Venus globe |
| `black` | Anti-Sol disc, Anti-Sol den plug, Sol numeral |
| `yellow` | Saturn globe |
| `orange` | Sol flames and corona, Jupiter globe |
| `cyan` | Anti-Sol flames and corona, Uranus globe |
| `dark_gray` | board panels, Neptune dark spot |
| `cocoa_brown` | belt tiles, Mercury plains and Caloris rim, Mars albedo, Venus lowlands, Saturn bands, Jupiter bands |
| `gray` | Mercury globe, trays |
| `red` | Mars globe, Jupiter Great Red Spot |
| `beige` | Earth dryland, Venus highlands |
| `blue` | Earth globe, Neptune globe |
| `green` | Earth land |

**Two colour collisions, stated rather than hidden.** Earth and Neptune share
`blue`. They are 5.19 mm apart in globe diameter, Earth carries `green` land [assumed]
and Neptune does not, and they carry different numerals.

Venus's globe and the Sol den plug now share `sunflower_yellow`. That is [assumed]
stated rather than accidental: the amber was chosen for Venus because it is
the closest thing the shop stocks to the Magellan mosaic's colour, and it was
preferred to a new spool precisely because the set already carried it. The two
are never confused — the den is a 36.00 mm square flange lying flat on [assumed]
the board with two 18.00 mm flames rising off it, and Venus is a Ø16.53 [assumed]
ball on a Ø34.00 disc — and the den plug never moves while Venus does.

One near-collision is worth the same sentence. Venus's globe is `sunflower_yellow` [assumed]
#FFB549 and Saturn's is `yellow` #FFD834, which are now neighbours in hue.
They are 9.47 mm apart in globe diameter, Saturn carries a Ø30.00 ring and [observed]
Venus carries nothing of the kind, and they read 3 and 7 on the disc; the
silhouette carries it before the colour is looked at.
`measure/venus-saturn-separation.md` is that check rather than an assumption.

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
    south" and named no meridian for it — Jupiter turns in ten hours and this
    set fixes no prime meridian on any world. Built on the meridian the first
    draft happened to use, the spot sat on the hidden hemisphere of both
    armies in every rendered view: measured against the view axis it scored
    −0.49 and −0.45, and a blind reader given only the renders reported
    Jupiter as "banded belts" with no spot. It was carried 110° around its own
    axis, which is free: after the shift it measures +0.44 / +0.62 against the
    two frames the product is photographed from, on both armies.

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

14. **Earth's surface is drawn from coastline outlines; the worlds that
    carry no recognisable outline stay round patches.** A blob union is honest
    for Neptune's dark spot and for a band system, because that is what those
    features are. It is not honest for Earth: at a glance a union of green and
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
    All thirteen spools are the ones the set already loaded.

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
Motion verification is switched off for this run and
is recorded as unverified, never as passed. The clearances, wall thicknesses
and overhang margins above are geometric measurements on the exact CAD solids
and predictions for the printer named in `README.md`.
