# Belt tile landing pad: coplanarity with its rubble crests

> Provenance: this measurement was taken on the source archive's build of
> `part_belt_cell`. This run does not repeat it, and does not need to: the
> belt tile's printed STEP is byte-identical to the archive copy in this
> run, which `measure/revision-part-hashes.md` shows against the archive's
> own sealed hash. The numbers below therefore describe this run's solid
> exactly. Nothing in this revision touches the belt.

Wish §6 requires the belt tile to carry "one smooth flat Ø26.00 mm disc at the
exact centre of the tile, level with the field and with every crest around it".
Wish §16 makes it the belt's one hard requirement: "**every crest the disc can
touch is coplanar with the pad, to within one layer.** If that cannot be held,
raise the pad to Ø34.40 and shrink the rubble to a border rather than accepting
a piece that wobbles."

Measured on the exact solid returned by `parts.belt.build_belt_cell()`, not on
a render.

| quantity | measured |
|---|---|
| tile top datum | z = 6.0000 mm |
| terrain pocket depth | 6.00 mm, so the tile top is flush with the field |
| planar faces lying exactly at the datum | 5 |
| their total area | 532.9 mm² |
| the pad alone | 530.93 mm² (= π·13.00², the full Ø26.00) |
| the crests at the datum | 2.0 mm², four faces of 0.50 mm² each |
| **faces anywhere above the datum** | **0** |
| seated disc footprint (widest disc, Ø33.87) | 901.0 mm² |

Two things follow, and together they are stronger than the requirement.

1. **Nothing stands proud of the pad.** The tile's bounding box tops out at
   z = 6.0000 and no face exceeds it. There is no crest that can lift a disc
   off the pad, so the failure §16 forbids cannot occur by height.
2. **Every crest the disc can touch is already in the pad's plane, exactly.**
   The four crest faces at the datum are not within one layer of the pad; they
   are in the same plane as it, to the kernel's own tolerance. Every other rock
   falls away below it.

A seated disc therefore rests on 532.9 mm² of coplanar contact — a Ø26.00
central pad plus four coplanar crests — and cannot rock. The tonal break
visible around the pad rim in the product renders is the step down to the
rubble *below* the datum; it is not material above it.

## Why there are four crests and not sixteen

The rubble field was rewritten to repair a measured `inspect validate` failure
(`invalidTopology` on all twelve belt tiles in the assembly package, see
`../features/rubble.py`). The rocks are now disjoint and flat-topped instead of
a dense overlapping mat, so fewer of them reach the trim plane. The tile's face
count fell from 906 to 248, its worst face from 0.00034 mm² to 0.00090 mm², and
its worst edge from 0.0012 mm to 0.0125 mm.

The requirement is unaffected and is in fact easier to hold: with a Ø26.00 pad
under a Ø33.87 disc, the pad alone is a 530.93 mm² flat seat, and the four
crests that do reach the datum are in its plane rather than above it.
