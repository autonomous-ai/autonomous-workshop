# Build spec — Planet Shear matter rank-4 piece

**Source images:** `ref/hero.png` · **Distinct viewpoints:** 1 `[observed]` · **Image kind:** studio render

**Reference labels for the likeness gate**

```
hero=ref/hero.png
```

**Project directory:** `cad/` inside the product root. Every path below
(`ref/`, `measure/`, `snap/`, `part_piece.step.py`) is relative to it.

---

## 1. Overall read

A single play-scale game piece: a stylised Earth standing on a flat cylindrical
disc. It is the rank-4 matter-faction piece of Planet Shear, a Dou Shou Qi
(Jungle Chess) set reskinned as matter and antimatter celestial bodies, so the
disc footprint is what sits in a board square and the numeral on its wall is
what a player reads across the table.

- **Construction family (base solid):** revolve (disc and globe) plus radial
  relief patches trimmed out of a concentric shell — the continents are raised
  ground, not a printed texture `[observed]`
- **Symmetry:** the disc is rotational about Z; the globe is not `[observed]`
- **View coverage:** one three-quarter front view observed; top, side and rear
  are reconstructed from the fact that the disc is a body of revolution and the
  globe a sphere
- **Finish / material read:** matte printed plastic in five flat colours —
  ocean blue, disc blue, olive land, tan dryland, ice white `[observed]`

> **Reconstruction note:** only one viewpoint is supplied. The Pacific face of
> the globe and the rear of the disc wall are reconstructed, not observed, and
> are called out again in section 7.

---

## 2. Top view — plan, looking down −Z

`[inferred]` — the disc is a body of revolution, so its plan follows from the
front view.

- **Outline:** circle, with the globe circle concentric inside it
- **Bounding footprint:** 34.0 × 34.45 mm `[observed]` (the 0.45 mm is the
  numeral standing off one side of the wall)
- **Corner radius:** n/a — circular
- **Symmetry axes:** the disc has every axis; the numeral fixes the front
- **Features visible only in plan:** the polar ice field, whose rim is lobed
  rather than a clean circle
- **Hidden in this view:** the numeral, the ice seat, the disc wall

---

## 3. Front view — elevation, looking along +Y

`[observed]`

- **Silhouette:** a flat disc, then a sphere that meets it through a short
  conical seat
- **Overall:** 34.0 × 25.08 mm `[observed]` width, `[inferred]` height
- **Height bands:**

| Band | From → to (mm) | Width (mm) | Note |
|---|---|---|---|
| disc | 0 → 5.0 `[observed]` | 34.0 `[observed]` | wall carries the rank numeral; top edge rounded 0.6 `[observed]` |
| ocean seat | 5.0 → 6.49 `[inferred]` | 16.30 → 15.67 `[inferred]` | cone, 12° from vertical, spreading outward to the disc face; ocean blue |
| globe | 6.49 → 24.08 `[observed]` | 21.08 max `[observed]` | sphere, centre at Z 13.54 |
| relief | to 25.08 `[observed]` | — | land and ice stand 1.0 mm proud of the ocean |

- **Lean / draft angle:** none on the disc; 25° from vertical on the ice seat
  `[inferred]`
- **Ground contact:** the full 34.0 mm disc face `[observed]`
- **Features visible only in front:** the seven-segment numeral 4

---

## 4a. Side view — elevation, looking along +X

`[inferred]` — identical to the front except that the numeral is edge-on.

- **Silhouette:** as section 3
- **Overall:** 34.45 × 25.08 mm `[inferred]`
- **Depth at each height band:** equal to the widths in section 3; every band is
  a body of revolution
- **Overhangs steeper than 45° from vertical:** none. The ice seat covers the
  globe below latitude 42 S, relief stops at latitude 38 S, and every relief
  side wall is leaned toward the nearer pole where its outline faces south
- **Features visible only in side:** none

---

## 4b. Component descriptions

**Disc base.** A plain cylinder, 34.0 mm across and 5.0 mm tall `[observed]`,
with its top edge rounded 0.6 mm `[observed]` and its bottom edge left sharp so
the piece sits flat. Its wall carries the rank numeral. It meets the globe
through the ice seat, which is one solid with it. What breaks if it is wrong:
the diameter is the board-square fit and the height is the grip, so both are
fixed by the Wish and neither is free. `[observed]`

**Ocean seat.** A short cone from the globe at latitude 42 S `[inferred]` down to
the disc face, spreading slightly outward as it goes: 15.67 mm across where it
meets the globe, 16.30 mm where it lands `[inferred]`. It is the printable
transition -- a sphere resting tangentially on a flat disc leaves an unsupported
cap of 189 mm2 `[observed]` underneath it -- and it spreads rather than tucks so
the silhouette reads as a ball seated on the disc rather than a ball pinched
above it. The globe itself is a full 21.08 mm sphere: the seat is material added
around its foot, never a cut taken out of it. Finished in the ocean's blue so
nothing changes colour where the two meet.

**Ocean globe.** A 21.08 mm sphere `[observed]`, centred 13.54 mm above the disc
face, sunk 2.0 mm into the disc so the seat is short `[inferred]`. Everything
else on the globe is relief standing on this surface.

**Nothing white at the foot.** The reference shows a band of ice where the globe
meets the disc, and two independent reviews rejected every attempt to build it:
white there faces downward, shades to mid grey, and reads as bare unpainted
material rather than as ice. The seat is therefore finished in the ocean's own
blue, the globe runs blue into the disc, and the piece carries no southern ice.
This is a deliberate departure from the reference, recorded rather than hidden.

**Continental relief.** Land stands 1.0 mm proud of the ocean `[observed]`.
Outlines are stylised: on a 21.08 mm globe one degree of arc is 0.184 mm, and a
south-facing relief edge has to ramp about seven degrees of arc to print without
support, so no landmass is drawn narrower than about fourteen degrees. Central
America is therefore one broad land bridge and the Indonesian arc is left to the
sea. What breaks if it is wrong: the continents are the whole subject, and a
thread-width peninsula would come off the bed as a smear. `[observed]` outlines,
`[inferred]` minimum width.

**Dryland relief.** Tan ground cut out of the continents at the same 1.0 mm
height — Sahara and Arabia, the Kalahari, inner Asia, the American southwest,
the Australian outback `[observed]`. A colour boundary only; it is never its own
wall.

**Polar ice.** White relief at the same 1.0 mm height covering the cap above
latitude 72 N, Greenland, and four lobes that carry the ice down onto the
northern coasts `[observed]`. There are six lobes, enough that the ice reaches a
different latitude at nearly every longitude: the bare cap ends on an exact
circle of latitude, which in a front elevation is a straight line across the top
of the globe and reads as a lid laid on it. Two other ways of breaking that rim
were tried and taken back out -- notches bitten into it made the cap read as a
cog, and leaning the cap cone off the polar axis left slivers where it grazed a
lobe and the printed body came out with five open edges.

**Rank numeral.** A seven-segment 4, 2.8 mm wide and 3.6 mm tall, strokes 1.0 mm,
standing 0.45 mm off the disc wall and centred on the front `[observed]`. Every
stroke is drafted: the underside rises 1.2 mm per mm of relief so it is not a
ceiling over open air, and the sides and top draft 0.5 mm per mm so each face
catches the light at its own angle instead of lying flush with the wall.

**Component ledger** — every entry above appears here, and every row is one
production body the shop can address by name.

| Component | Described in 4b | Becomes part(s) | Landmark check |
|---|---|---|---|
| Disc base and rank numeral | yes | `parts/disc_base.step` | disc diameter, height, top round; numeral proud of the wall and reading as four bars |
| Ocean seat | yes | `parts/ocean_seat.step` | seat radii at both ends and its top height |
| Ocean globe | yes | `parts/ocean_globe.step` | sphere diameter and centre height |
| Continental relief | yes | `parts/land_americas.step`, `parts/land_africa.step`, `parts/land_eurasia.step`, `parts/land_australia.step` | relief outer radius, four named bodies each one solid, land coverage |
| Dryland relief | yes | `parts/dryland_sahara.step`, `parts/dryland_kalahari.step`, `parts/dryland_inner_asia.step`, `parts/dryland_american_southwest.step`, `parts/dryland_outback.step` | five named bodies each one solid |
| Polar ice | yes | `parts/polar_ice.step` | ice present above latitude 72 N and its rim not a single parallel |

The bodies are named for the landmass they are, not numbered, because the name
travels to the shop as the part name. They are split out of the fused relief by
which outline group each body sits over, so naming never moves a vertex.

---

## 5. Size

**Scale anchor:** the Wish states the piece dimensions directly and forbids
re-deriving them from the image — `[observed]`

| Dimension | Value (mm) | Confidence | Source |
|---|---|---|---|
| Overall L × W × H | 34.0 × 34.45 × 25.08 | `[observed]` | Wish, plus numeral relief and land relief |
| Disc diameter | 34.0 | `[observed]` | Wish |
| Disc height | 5.0 | `[observed]` | Wish |
| Globe diameter | 21.08 | `[observed]` | Wish |
| Relief height | 1.0 | `[observed]` | Wish |
| Numeral relief | 0.45 | `[observed]` | reference image |
| Minimum stroke / feature | 1.0 | `[inferred]` | 2.5 × 0.4 mm nozzle |
| Globe sink into the disc | 2.0 | `[inferred]` | shortest seat that still prints |

**Source parameter ledger** — every value below is the literal in
`planet_shear_lib.py`, and `measure/check_spec.py` fails if one drifts.

The Wish's four hard dimensions are `BASE_DIAMETER = 34.0`,
`BASE_HEIGHT = 5.0`, `GLOBE_DIAMETER = 21.08` and `RELIEF = 1.0`, with
`RANK_DIGIT = 4`. The printability choices are `GLOBE_SINK = 2.0`,
`SEAT_LAT = -42.0`, `SEAT_ANGLE = -12.0` and `RELIEF_FLOOR_LAT = -38.0`; the
numeral is `GLYPH_HEIGHT = 3.6` by `GLYPH_WIDTH = 2.8` with
`GLYPH_STROKE = 1.0` standing `GLYPH_RELIEF = 0.45` off the wall.

| Parameter | Value | Confidence |
|---|---|---|
| `BASE_DIAMETER` | `34.0` | `[observed]` |
| `BASE_HEIGHT` | `5.0` | `[observed]` |
| `GLOBE_DIAMETER` | `21.08` | `[observed]` |
| `RELIEF` | `1.0` | `[observed]` |
| `RANK_DIGIT` | `4` | `[observed]` |
| `BASE_TOP_ROUND` | `0.6` | `[observed]` |
| `GLYPH_HEIGHT` | `3.6` | `[observed]` |
| `GLYPH_WIDTH` | `2.8` | `[observed]` |
| `GLYPH_STROKE` | `1.0` | `[inferred]` |
| `GLYPH_RELIEF` | `0.45` | `[observed]` |
| `GLYPH_BOTTOM` | `0.4` | `[inferred]` |
| `GLYPH_RAMP` | `1.2` | `[inferred]` |
| `GLYPH_DRAFT` | `0.5` | `[inferred]` |
| `GLOBE_SINK` | `2.0` | `[inferred]` |
| `SEAT_LAT` | `-42.0` | `[inferred]` |
| `SEAT_ANGLE` | `-12.0` | `[inferred]` |
| `RELIEF_FLOOR_LAT` | `-38.0` | `[inferred]` |
| `LON_OFFSET` | `-65.0` | `[observed]` |
| `NOZZLE` | `0.4` | `[assumed]` |

**Print sanity:**

- Bed fit: fits 220 × 220 × 220 mm `[assumed]`
- Minimum wall at this scale: 1.0 mm `[inferred]` — ok at a 0.4 mm nozzle
- Minimum feature: about 14° of arc, 2.6 mm, for a relief outline `[inferred]`
- Overhangs: handled by orientation and by the ice seat; no supports
- Print orientation: disc face on the bed, globe up — the only orientation in
  which the disc prints as a flat first layer

---

## 6. Decomposition

### 6a. Printed parts

| # | Part | Purpose | Envelope (mm) | Joins to | Joint type | Shared mating dimension | Clearance/side |
|---|---|---|---|---|---|---|---|
| 1 | `part_piece` | the whole game piece | 34.0 × 34.45 × 25.08 `[observed]` | — | none | — | — |

One printed part. The split test fails on every count: nothing opens, nothing
moves, one orientation prints all of it, and it fits the bed many times over.
The six colour groups in `planet_shear_earth.step.py` -- disc base, ocean seat,
ocean, land, dryland and polar ice -- are regions of this one body,
not separate prints; their volumes sum to it exactly, which
`measure/check_landmarks.py` asserts against the written STEP.

**Assembly order:** none — single part.

**Seams seen in the image that are NOT splits:** the line where the globe meets
the disc is a colour change and a change of surface, not a joint.

### 6b. Feature tree — part `part_piece`

| # | Tier | Feature | Rooted in / cut from |
|---|---|---|---|
| 1 | base | disc cylinder | — |
| 2 | finishing | 0.6 mm `[observed]` round on the disc top edge | disc |
| 3 | additive | ice seat cone | disc top face |
| 4 | additive | ocean sphere | ice seat |
| 5 | additive | seven-segment numeral 4 | disc wall |
| 6 | additive | continental, dryland and polar relief | ocean sphere |
| 7 | finishing | colour split into six occurrences | the whole body |

### 6c. Off-the-shelf components — catalog search log

N/A — the piece has no bought components, no fasteners and no standard elements.

### 6d. Analogous design references

| Query | Status | Source authority/type | Stable URL + revision/commit | Relevant feature | Specification/constraint taken | Construction lesson used | License/use |
|---|---|---|---|---|---|---|---|
| tiled-board piece layer | used | Mara Masque inventor skill, `references/tiled-board-baseline.md` | local skill file, materialised for this run | disc footprint and piece height | none — its piece-layer millimetres are overridden by the Wish | rising transition under every projecting feature; no thin freestanding elements; prefer faceted to circular detail at nozzle scale | internal |

The baseline's piece layer is display scale: 26–32 mm `[observed]` base
circumdiameters and 40–86 mm `[observed]` role heights. This set is play scale
and the Wish fixes a 34.0 mm `[observed]` disc, 5.0 mm `[observed]` tall, under a
21.08 mm `[observed]` sphere, so the departure is deliberate and is recorded here
rather than silently taken.

### 6e. Mount declarations

N/A — nothing is mounted.

---

## 7. What is not verified

- The Pacific face of the globe and the rear of the disc wall are not in the
  reference image. They are reconstructed and unverified against it.
- Motion is unverified: this run's `MAKE-OPTIONS.json` has `check_motion` false,
  and the piece has no mechanism in any case.
- Nothing here has been printed. Wall, overhang and mesh gates are geometric.
