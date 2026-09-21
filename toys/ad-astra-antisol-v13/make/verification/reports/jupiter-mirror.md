# The Jove mirror: what moved on Jupiter, and what did not

The correction adds `"jupiter"` to `parts/markings.MAP_MIRRORED_WORLDS`
and gives it a `MERIDIAN_ADJUSTMENT` of +15.00 degrees. That is the
whole of the source change to the geometry. Everything below is a
consequence of it, measured rather than argued, because the brief
this correction answers is mostly a list of things that must stay
where they are.

## 1. The Sol piece is untouched

`markings_for` returns the identical object `MARKINGS` holds for any
Sol piece -- not a copy, not a rebuild -- so the Sol world cannot
have been changed by a transform that is never applied to it. That is
an identity check rather than an equality check, and it is the
strongest form the claim has:

- `markings_for("jupiter", "sol") is MARKINGS["jupiter"]`: **yes**
- `markings_for("jupiter", "anti") is MARKINGS["jupiter"]`: **no**, which is the correction

The printed solid says the same thing in bytes:
`measure/revision-part-hashes.md` carries `part_world_jupiter_sol.step`
and `part_world_jupiter_anti.step` against the published set, and
`measure/occurrence-geometry.md` carries every one of the 220 colour
bodies.

## 2. No latitude moved, anywhere

A longitude reflection maps (lon, lat) to (2C - lon, lat). Latitude
is not in the transform at all, so no belt boundary, no zone
boundary and no feature can have changed latitude. Checked vertex by
vertex against the Sol ring it came from, at 0.0001 degrees.

| marking | rings | vertices | largest latitude change |
|---|---:|---:|---:|
| `bands` | 12 | 264 | 0.00e+00 |
| `spot` | 1 | 13 | 0.00e+00 |
| `collar` | 1 | 18 | 0.00e+00 |

The Great Red Spot sits at latitude -22.00 on both pieces, which is
where the real one sits, and the six belts keep the latitudes
`jupiter_atlas.BELTS` gives them:

| belt | south | north | width |
|---|---:|---:|---:|
| North North Temperate Belt (`nntb`, band) | +38.0 | +43.0 | 5.0 |
| North Temperate Belt (`ntb`, band) | +24.0 | +31.0 | 7.0 |
| North Equatorial Belt (`neb`, outline) | +7.0 | +17.0 | 10.0 |
| South Equatorial Belt (`seb`, outline) | -20.0 | -7.0 | 13.0 |
| South Temperate Belt (`stb`, band) | -34.0 | -27.0 | 7.0 |
| South South Temperate Belt (`sstb`, band) | -46.0 | -40.0 | 6.0 |

Read the widths rather than the names: 7, 10, 13, 7, 5, 6. No two of
the pairs are mirror images and no two gaps between them are equal.
That is the set's own asymmetry and this correction does not touch
it -- a reflection about a meridian cannot, because a band has the
same longitude everywhere.

## 3. What a longitude reflection leaves exactly alone

Most of this globe is invariant under the transform, and it is worth
saying how much. `_mirror_spec` returns a `band`, a `shell` and a
`cap` spec unchanged -- the same object, not a rebuilt one -- because
they are sets of latitudes and the transform is the identity on them.

| marking | spec | kind | carries a longitude | identical object |
|---|---:|---|---|---|
| `bands` | 1 | `band` | no | yes |
| `bands` | 2 | `band` | no | yes |
| `bands` | 3 | `outline` | **yes** | no |
| `bands` | 4 | `outline` | **yes** | no |
| `bands` | 5 | `band` | no | yes |
| `bands` | 6 | `band` | no | yes |
| `spot` | 1 | `outline` | **yes** | no |
| `collar` | 1 | `outline` | **yes** | no |
| `zones` | 1 | `shell` | no | yes |
| `zones` | 2 | `shell` | no | yes |
| `zones` | 3 | `shell` | no | yes |
| `zones` | 4 | `shell` | no | yes |
| `zones` | 5 | `shell` | no | yes |

**9 of the 13 region specs on this globe are returned unchanged and
4 are reflected.** The 4 are the Great Red Spot, its collar and the
two wavy belts; everything else is a circle of latitude. That is why
this world needed a meridian adjustment and Mercury and Venus did
not: on those two the reflection moves most of the map, and here it
moves one oval and the phase of two waves.

## 4. The hollow follows the spot

The South Equatorial Belt's southern boundary bends 7.0 degrees
north over the spot, so the belt looks like it belongs to the weather
rather than like a sticker. That bend is drawn into the belt's own
sector rings, so the reflection carries it with them -- but that is a
prediction, and this is the measurement. The belt's SOUTHERN boundary
-- the first half of every sector ring, which is the half the hollow
is cut into -- is walked on each piece at the 6 degree vertex
spacing the build gives it, and its northernmost point found. Its
unhollowed latitude is -20.0, so the peak is the hollow.

| piece | spot longitude | belt's northernmost point | its latitude | offset from the spot |
|---|---:|---:|---:|---:|
| Sol | -48.00 | -48.00 | -13.00 | +0.00 |
| Anti-Sol | -19.54 | -19.54 | -13.00 | +0.00 |

The bend is within one 6 degree vertex step of the spot's own
meridian on both pieces, and the boundary reaches latitude -13.00
there against its unbent -20.0 -- a rise of 7.00 degrees against the
7.0 the hollow is drawn at. The belt bends around the spot on the
Anti-Sol piece exactly as it does on the Sol one, at the new
longitude, with no second mechanism and no special case: the hollow
is part of the ring, so reflecting the ring reflects the hollow.

## 5. What it costs, measured

Two things about the Anti-Sol Jupiter are now not the real planet,
and both are recorded in the product's limitations as well as here.

**The Red Spot sits at a longitude that is not the real one.** It is
at -48.00 on the Sol piece and -19.54 on the Anti-Sol one.
What that costs is nothing a map could check, because longitude on
this globe was never a map fact: `SPOT_LON = -48.0` was chosen to put
the spot in front of the cameras -- the same decision
`mercury_atlas.CALORIS_LON` and `venus_atlas.LONGITUDE_OFFSET` are --
and Jupiter turns in ten hours with no fixed meridian anywhere in
this set. Latitude, size, shape and count are untouched, and those
are the four things a reader could check against a photograph.

**The wave phase of the two widest belts is handed the other way.**
Each wavy boundary carries two harmonics of longitude, so reflecting
longitude reflects the pattern:

| boundary | harmonics (n, amplitude, phase) |
|---|---|
| `neb` south | (3, 1.5, 0); (4, 1.0, 110) |
| `neb` north | (2, 1.4, 250); (5, 1.1, 40) |
| `seb` north | (3, 1.6, 200); (4, 0.9, 20) |
| `seb` south | (2, 1.5, 70); (3, 1.0, 310) |

A reader cannot tell a handed wave from an unhanded one without the
other piece beside it -- which is the point, since the two pieces
standing side by side is exactly the comparison this correction
exists to win. The amplitude is 2.5 degrees either way on both
pieces, which is 0.59 mm on this globe, so the belts stay the same
belts.

## 6. The set, after the correction

Three of eight worlds carry a mirrored map and five carry one map at
two leans. `measure/mirror-set-consistency.md` is that table, the
rule that decides it, and every world's tilt and inter-piece angle.
`markings.MAP_MIRRORED_WORLDS` is now ('mercury', 'venus', 'jupiter').

## Verdict

Every negative the brief names holds in the built tables: the Sol
piece takes the identity path, no latitude moved anywhere by more
than 0.0001 degrees, the six belt latitudes and five zone latitudes
are the ones `jupiter_atlas` declares, and the belt hollow
follows the spot to the new longitude by itself. What moved is
the spot, its collar, the two wavy belts' phase, and the three
zones those belts trim.

Measured by `measure/jupiter_mirror.py` on the exact specs
`parts.markings.markings_for` returns for each piece.
