# Neptune's companion cloud, and what did not move

Baseline: the build this correction starts from, rebuilt from the
source in `revision-source.zip`. Current: this tree. Globe Ø21.89 mm, one degree of arc
= 0.1910 mm, nozzle 0.40 mm = 2.09 degrees.

Declared: centre lat -33.50, lon -75.20; 10 x 5 degrees of arc; spot centre
lat -22.00, lon -65.20, so the companion is 11.50 degrees south of it and 10
degrees west. The owner asked for about 8 south at the same longitude: 8
would overlap the spot's rim, and the spot's own meridian puts 41% of a
printable companion under the Sol piece's seat (see `parts/neptune_atlas.py`
and the seat table below).

## sol

| check | result | value |
|---|---|---|
| companion is one solid | PASS | 1 |
| companion filament is white | PASS | white |
| companion not proud of the globe (max r - R) | PASS | +0.00000 mm |
| east-west extent, deg of arc (want ~10) | PASS | 9.99 deg = 1.908 mm |
| north-south extent, deg of arc (want ~5) | PASS | 5.00 deg = 0.955 mm |
| narrowest neck (minor axis) >= nozzle | PASS | 0.955 mm = 2.39 nozzle widths |
| centre latitude | PASS | -33.50 |
| centre longitude (declared spot -10) | PASS | -75.20 (spot -65.20) |
| centre lies within the spot's east-west span | PASS | -75.20 in -80.25..-50.15 |
| companion south of spot (its north rim below spot's south rim) | PASS | -31.00 < -29.00 |
| bare gap to spot >= nozzle | PASS | 0.526 mm = 1.31 nozzle widths |
| bare gap to bands >= nozzle | PASS | 0.954 mm |
| bands unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, white |
| disc unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, white |
| numeral unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, black |
| spot unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, dark_gray |
| globe lost exactly the companion's volume | PASS | 1.5194 vs 1.5195 mm3 |

## anti

| check | result | value |
|---|---|---|
| companion is one solid | PASS | 1 |
| companion filament is white | PASS | white |
| companion not proud of the globe (max r - R) | PASS | +0.00000 mm |
| east-west extent, deg of arc (want ~10) | PASS | 9.99 deg = 1.908 mm |
| north-south extent, deg of arc (want ~5) | PASS | 5.00 deg = 0.955 mm |
| narrowest neck (minor axis) >= nozzle | PASS | 0.955 mm = 2.39 nozzle widths |
| centre latitude | PASS | -33.50 |
| centre longitude (declared spot -10) | PASS | -75.20 (spot -65.20) |
| centre lies within the spot's east-west span | PASS | -75.20 in -80.25..-50.15 |
| companion south of spot (its north rim below spot's south rim) | PASS | -31.00 < -29.00 |
| bare gap to spot >= nozzle | PASS | 0.526 mm = 1.31 nozzle widths |
| bare gap to bands >= nozzle | PASS | 0.954 mm |
| bands unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, white |
| disc unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, black |
| numeral unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, white |
| spot unchanged (volume, bbox, filament) | PASS | dV +0.00e+00 mm3, dbbox 0.0e+00 mm, dark_gray |
| globe lost exactly the companion's volume | PASS | 1.5195 vs 1.5195 mm3 |

## How much of the companion the seat cone covers

The seat cone springs from the sphere at piece latitude -42.0
(about the piece's own vertical). Area-weighted over the oval:

| army | piece-latitude span of the oval | outer face above the seat | covered by the seat |
|---|---|---:|---:|
| sol | -39.5 to -32.5 | 100% | 0% |
| anti | -26.0 to -19.4 | 100% | 0% |

At the spot's own meridian (the first build of this correction,
centre -34.5) the Sol figure was 59% above / 41% covered; the
10-degree westward offset exists to make it 100%.

**Overall: PASS**

