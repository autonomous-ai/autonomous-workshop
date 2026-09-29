---
title: Feature tree and build order
tags: [feature-tree, base-solid, boolean, fillet, shell, order, pattern, decomposition]
aliases: [feature order, operation order, build sequence, base feature, modeling order, repeated features]
sources:
  - skills/image-to-cad/references/decomposition.md
  - "experience: feature orders that refilled holes, hollowed bosses or consumed fillets without an error"
related: [printed-part-count, wall-thickness-and-hollowing]
updated: 2026-09-23
---

# Feature tree and build order

Inside each printed part, decompose into an ordered list of features. The order
*is* the implementation — the generator executes it in that order — so a wrong
order is a wrong model, often with no error.

## Find the base solid first

The base solid is the one primitive or profile that carries the object's mass
and identity. Everything else is added to it or cut from it. In a photo it is:

- the largest continuous volume;
- the thing that would remain recognisable if every detail were removed;
- usually the thing a silhouette measurement is measuring.

Pick it wrong and every later feature fights the geometry. Two tests:

- **The squint test.** Blur the object mentally until details vanish. What shape
  is left? That is the base solid.
- **The removal test.** If you deleted this feature, would the object still be
  the same object? If yes, it is a feature. If no, it is the base solid.

For a lofted or revolved body, the base solid is the **outer skin**, and the
functional interior is cut from it afterwards. Skin carries the image, interior
carries the engineering.

## The four tiers, in build order

1. **Base solid** — one operation. Extrude, revolve, loft, or sweep.
2. **Additive** — bosses, ribs, lugs, flanges, handles, fenders, standoffs.
   Each must be **rooted in the base solid**, overlapping it by real material,
   never merely touching. A feature that touches at a tangent produces
   disconnected bodies and a floating part.
3. **Subtractive** — cavities, holes, slots, channels, ports, reliefs, shells.
4. **Finishing** — fillets, chamfers, edge breaks, engraving, texture.

## Ordering rules that prevent build failures

- **Most stable anchor first.** Build the feature everything else is positioned
  from before the features that reference it.
- **Union before cut**, unless the cut is what makes the shape possible. A hole
  cut before a union can be refilled by the union — silently, with no error.
- **Shell before adding interior features**, so the shell does not hollow out
  the bosses you just added ([[wall-thickness-and-hollowing]]).
- **Fillets last.** A fillet applied before a boolean either gets consumed or
  makes the boolean fail. The exception is a 2D fillet on a sketch profile,
  which is part of the profile, not a finishing operation.
- **Tag frames you will need again.** If a feature's position is defined
  relative to a face a later boolean will destroy, record (tag) that frame
  before the destroying operation.

## Group repeated features

Four identical corner bosses are **one** feature with a count and a placement
rule, not four. Name the layout: `GridLocations`, `PolarLocations`, or
`Locations` with a named point list. A repeated feature spelled out N times is
implemented as N hand-placed copies, and the next edit has to touch all of
them. The count of a repeated feature also sets the web between copies
([[wall-thickness-and-hollowing#a-repeated-features-count-is-a-wall]]).

## Pitfalls

- Choosing a detail as the base solid because it is visually prominent.
- Listing repeated features individually instead of as an array.
- Fillets placed before the booleans they must survive.
- Additive features that touch the base at a tangent instead of overlapping it.
