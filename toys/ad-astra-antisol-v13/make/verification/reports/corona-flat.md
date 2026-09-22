# The trap tile, before and after its tongues came off

## Where the before figures come from

`make/models/cad/part_corona_cell.step` in the source archive, sha256
`484a16ba92e26ad451b5dabd2b87e514b788a796242d4babc8f1ecdd1837d906`.

The published set's own `cad/part_corona_cell.step` is
`484a16ba92e26ad451b5dabd2b87e514b788a796242d4babc8f1ecdd1837d906`,
read from `make/made.json`'s product manifest in the same archive.
They are **the same file**.

## The tile

| | before | after | change |
|---|---:|---:|---:|
| separate solids | 1 | 1 | +0 |
| printed height mm | 10.000 | 3.000 | -7.000 |
| footprint mm | 33.597 x 33.548 | 33.500 x 33.500 | -- |
| volume mm3 | 3414.678 | 3292.462 | -122.216 |
| surface area mm2 | 2855.890 | 2748.946 | -106.945 |

The tile is 3.00 mm tall and was 10.00: the two tongues stood
7.00 mm above its top face, which is `CORONA_TONGUE_H` 4.00 above
the field plus `CORONA_WELL_DROP` 3.00 of well. The tile's own
height, `CORONA_TILE_H`, is untouched at 3.00 mm and so is the well
it leaves.

## What the six tiles save

| | per tile | across the 6 trap tiles |
|---|---:|---:|
| volume removed mm3 | 122.216 | 733.295 |
| filament at 1.24 g/cm3 | 0.152 g | 0.909 g |
| tapered flames removed | 2 | 12 |

A fraction of a gram. The print this buys is not the filament -- it
is that six parts lost their tallest feature, so the six tallest
unsupported regions on the board's terrain are gone with it. The
overhang gate below is where that shows.

## The engraving is untouched

| | value |
|---|---:|
| `CORONA_ENGRAVE_COUNT` | 16 |
| `CORONA_ENGRAVE_INNER` mm | 6.50 |
| `CORONA_ENGRAVE_EYE_D` mm | 9.00 |
| `CORONA_ENGRAVE_D` mm | 0.40 |

Measured on the solid rather than read off the constants: the bare
tile is 3364.175 mm3 and the engraved tile is 3292.462 mm3, so the engraving
takes 71.713 mm3 out of the top face and the tile is otherwise whole.
Its deepest point is 0.40 mm below the top face.

## Nothing stands above the tile any more

The claim is that the corona cell is now a plain rounded-square
extrusion with an engraving cut into its top face -- one solid, no
feature above `CORONA_TILE_H`. Asked of the built body:

- separate solids: **1** 
- highest point: **3.000000 mm**, and `CORONA_TILE_H` is 3.00 
- lowest point: **0.000000 mm**, the bed

## The overhang gate

The published tile carried two trace regions of unsupported surface,
both at the tongue bases at Z 3.00 -- the one place on the part where
a leaning flame left the tile's own top face. With the tongues gone
there is nothing on the part that leans at all.

| | figures |
|---|---|
| before, published | part_corona_cell.step.py: 28.6 cm2 of surface, grid 0.400 mm, 10 unsupported samples over 2 region(s) |
| after, this run | part_corona_cell.step.py: 27.5 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s) |

The published report's own table of those regions:

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.0 | (-15.5, 15.5, 3.0) | 2.7 | 4.0 |
| 2 | trace | 0.0 | (16.8, 14.4, 3.0) | 0.0 | 4.0 |

**The corona cell now has zero unsupported regions.**
Both reports are measurements on the tessellated solid in the pose
it prints in, at a 0.4 mm nozzle and the 45 degree gate, and both
say `prints unsupported`. What changed is that the earlier one said
it with two trace regions in its table and this one says it with an
empty table.

## The tile at a quarter turn

`assemblies/product.py` used to turn each trap tile so its tongues
pointed away from the star, through one of 0, 90, -90 and 180
degrees. With no tongues that rotation has been dropped, and the
claim it rests on is that a quarter turn maps the tile exactly onto
itself -- the rounded square repeats every 90 degrees, and the
sixteen engraved tongues alternate two lengths so the engraving
repeats every 45. That is measured here rather than argued: the
symmetric difference between the tile and the tile turned, which is
the volume that is in one and not the other.

| turn | volume in one and not the other mm3 |
|---|---:|
| 90 degrees | 0.000000 |
| 180 degrees | 0.000000 |
| 270 degrees | 0.000000 |

Zero to the kernel's own noise. Every placed trap tile is the
same solid in the same place it was when the rotation turned it,
so the assembly's interference and occurrence-geometry checks
keep exactly the meaning they had.

## The four retired constants

| constant | value | what it was |
|---|---:|---|
| `CORONA_TONGUE_BASE_D` | 5.00 | mm, the tongue's base diameter |
| `CORONA_TONGUE_H` | 4.00 | mm above field datum |
| `CORONA_TONGUE_TIP_R` | 0.60 | mm tip radius |
| `CORONA_TONGUE_DIAGONAL` | 20.20 | mm between the two tongues, which left 0.70 mm of clearance to a seated disc and was the tightest thing on the tile |

All four are removed from `params.py`. Nothing reads them: they were
searched for across the whole project -- source, measurement scripts
and report generators -- before they were taken out, and
`parts/corona.py` was their only consumer.

## Verdict

The trap tile is one solid 3.00 mm tall: a rounded square with a
sixteen-rayed star sunk 0.40 mm into its top face, and nothing
above that face at all.

Measured by `measure/corona_flat.py`.
