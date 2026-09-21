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

| piece | published globe | + hood north | + hood south | = expected | measured now | residue |
|---|---|---|---|---|---|---|
| sol | 5323.412 | 109.5887 | 109.5887 | 5542.590 | 5542.588 | -0.0014 |
| anti | 5323.412 | 109.5887 | 109.5887 | 5542.590 | 5542.588 | -0.0014 |

The residue is the whole of what the removal cost the solid: within
0.01 mm3 the globe is exactly its old self plus its two hoods, which
is what a partition undone has to be. Both printed STEPs come out
byte-identical to the published set's for the same reason --
`measure/revision-part-hashes.md` carries those hashes.

## Verdict

**Nothing is drawn on either Uranus globe.** The marking table is
empty, neither piece carries a marking body, and the globe's volume
is its old volume plus both hoods to within 0.01 mm3.
