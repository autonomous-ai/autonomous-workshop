# Uranus carries no marking, measured on the solids

The owner has removed both polar hoods. Nothing replaces them: no
cap, no band, no spot, no quieter tone. This is the evidence that
nothing at all is drawn on either globe, taken three ways, because a
marking that silently fails to cut leaves a piece that still measures
as sound and correctly sized -- which is a fault this exact world has
had before.

## 1. The marking table is empty

`parts/markings.py` lists 0 regions for `"uranus"`.
The argument that built the hoods is kept above it, headed with
what happened to it. The list itself has nothing in it, so there
is nothing for `world_bodies` to cut the globe with.

## 2. The pieces have no marking body

`parts.world.world_bodies` is the one place the colour split is
decided; every STEP, occurrence and render downstream is built from
what it returns.

| piece | role | filament | solids | volume mm3 |
|---|---|---|---|---|
| sol | `disc` | `white` | 1 | 4388.653338 |
| sol | `globe` | `cyan` | 1 | 5542.588301 |
| sol | `numeral` | `black` | 2 | 8.467313 |
| sol | `ring` | `white` | 1 | 54.830480 |
| anti | `disc` | `black` | 1 | 4392.643479 |
| anti | `globe` | `cyan` | 1 | 5542.588301 |
| anti | `numeral` | `white` | 2 | 8.467231 |
| anti | `ring` | `white` | 1 | 54.830494 |

Four roles per piece and no fifth: the disc it stands on, the numeral
cut into that disc, the globe, and the ring. The ring is geometry, not
a marking -- a solid hoop in the equatorial plane rather than a colour
inlay in the globe's own sphere -- so **the globe is one undivided
`cyan` solid and there is no surface marking on this world at all.**

## 3. The arithmetic closes

A marking here is a flush inlay: it partitions the globe rather than
carving it. So taking the two hoods out must hand the globe back
exactly the volume they held, and move no surface.

**The baseline this run is compared against carries no hoods.**
They were removed by the Antisol Caelus revision, which is the
edition this one corrects, so there is no removal left to do and
no volume left to hand back. The statement this run has to make
about Uranus is the opposite one: that it did not touch it.

| piece | published globe mm3 | this run mm3 | residue |
|---|---:|---:|---:|
| sol | 5542.588301 | 5542.588301 | +0.000000 |
| anti | 5542.588301 | 5542.588301 | +0.000000 |

Both globes come out at exactly the volume the published set
carries, and neither hood occurrence exists in either assembly.
This revision changes `part_world_mercury_anti`,
`part_world_venus_anti` and `part_corona_cell`, and nothing else;
`measure/revision-part-hashes.md` carries Uranus's two printed
STEPs as byte-identical and `measure/occurrence-geometry.md`
compares every occurrence in the set.

## Verdict

**Nothing is drawn on either Uranus globe.** The marking table is
empty and neither piece carries a marking body.
The globe's volume is exactly the published set's, because this
revision does not touch this world: the hoods were removed by the
edition it corrects, and nothing has been put back.
