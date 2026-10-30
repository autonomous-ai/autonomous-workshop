---
title: Construction strategy and operation order
tags: [construction, strategy, boolean-order, fillet, operation-order, part-vs-assembly, revolve, base-solid, feature-tree, pattern, decomposition]
aliases: [modeling strategy, feature order, build order, boolean order, feature tree order, operation order, build sequence, base feature, base solid, modeling order, repeated features, feature tree and build order]
sources:
  - skills/cad/references/build123d-modeling.md (design strategy, before the move)
  - skills/image-to-cad/references/build123d-operations.md (boolean order and finishing, before the move)
  - skills/image-to-cad/references/decomposition.md
  - "experience: parts that compiled and validated with the hole in the wrong face or refilled by a later union"
  - "experience: feature orders that refilled holes, hollowed bosses or consumed fillets without an error"
related: [operation-families, feature-recipes, boolean-pitfalls, fillet-chamfer-pitfalls, build123d-selectors, printed-part-count, wall-thickness-and-hollowing, parametric-design-intent]
updated: 2026-10-10
---

# Construction strategy and operation order

Decide how a part is constructed before writing geometry code. The
construction family is chosen once and every later edit inherits it: a form
authored in the wrong family cannot be rescued by parameter edits, only by
re-authoring. Pick the family per form with [[operation-families]].

## Find the base solid first

The base solid is the one primitive or profile that carries the object's mass
and identity; everything else is added to it or cut from it. In a photo it is
the largest continuous volume, the thing that would stay recognisable with
every detail removed, and usually what a silhouette measurement measures.
Pick it wrong and every later feature fights the geometry. Two tests:

- **The squint test.** Blur the object mentally until details vanish. The
  shape that is left is the base solid.
- **The removal test.** Delete the feature: if the object is still the same
  object, it was a feature; if not, it is the base solid.

For a lofted or revolved body the base solid is the **outer skin**, and the
functional interior is cut from it afterwards: the skin carries the image,
the extruded and booleaned interior carries the engineering.

## Design strategy

- **Choose the construction that makes the spec's dimensions direct
  parameters.** Profile-driven shapes get one closed sketch plus
  `extrude`/`revolve`/`sweep`/`loft`; block-and-feature parts get a base solid
  plus subtractive features. Prefer whichever construction lets the user's
  controlling dimensions appear as named parameters instead of derived values.
- **Decide part vs assembly before modeling.** Bodies that are separately
  manufactured, purchased, or movable belong in a labeled assembly; monolithic
  manufacturing intent gets a single fused solid. Avoid unlabeled compounds of
  solids — multi-body output without occurrence labels loses traceability in
  inspection and viewer review. Fusing separately printed parts loses
  clearances and fits.
- **Pick the origin and orientation from the functional datum before
  sculpting.** Model on the mating interface, mounting plane, or symmetry axis.
- **Order operations so fragile steps come last and failures localize.** Base
  solid → major additions → subtractive features → shell → through-wall holes
  → fillets and chamfers last. Fillets are the most failure-prone operation and
  every boolean invalidates selectors, so postpone them. Structure the source
  so each feature is a named step — a per-feature function or a distinct
  intermediate variable — so a failed operation points at exactly one feature
  and a parameter change touches one obvious place.
- **Overshoot boolean tools** past the faces they enter and exit, so no tool
  face is coincident with the target's
  ([[boolean-pitfalls#overshoot-the-tool]]), and cut repeated or patterned
  features in one combined operation
  ([[boolean-pitfalls#multi-tool-booleans]]).
- **Sanity-check proportions before generating.** Compare the expected bounding
  box against the real-world object, wall thickness against overall size, and
  feature positions against edges and neighbouring features. Order-of-magnitude
  and collision errors pass geometric validation but fail visual review.
- **Prefer one revolved profile for axisymmetric soft forms.** A foam arrow
  tip, rubber bumper, knob, pawn, or bottle-like cap built from overlapping
  spheres, cones, and cylinders can mesh watertight while STEP validation
  reports `invalidTopology` or `selfIntersecting`. Put the full radial
  silhouette in one XZ-plane profile and `revolve(..., axis=Axis.Z)`; use
  stations in that profile to retain the bulge/taper without internal boolean
  seams.

## Boolean order

```text
base solid → additive (union) → shell → interior additive → subtractive (cut) → fillet
```

- **Most stable anchor first.** Build the feature everything else is
  positioned from before the features that reference it.
- **Root every addition in the base solid.** A boss, rib, lug, flange or
  standoff overlaps the base by real material (≥ 1 mm), never merely touching:
  a feature that meets it at a tangent comes out as a disconnected, floating
  body.
- **Union before cut**, unless the cut is what makes the shape possible. A hole
  cut before a union is silently refilled — no error, wrong part.
- **Shell before interior bosses**, or the shell hollows them
  ([[wall-thickness-and-hollowing]]).
- **Cut through-features after all unions**, then re-verify with
  `scripts/inspect refs --facts`: a later boolean can refill, shift, or enlarge
  an opening silently.
- **Tag frames you will need again.** If a feature is positioned from a face
  that a later boolean destroys, record that frame before the destroying
  operation.
- **Finishing last**: fillets, chamfers, edge breaks, engraving and texture.
  A fillet applied before a boolean is consumed or makes the boolean fail. A
  2D fillet on a sketch profile is part of the profile, not a finishing
  operation, and is exempt.
- **Gate the result, do not trust it** ([[kernel-validity]]).

State the order as integers in the build spec's feature table. That ordering
**is** the body of `gen_step()`: the generator executes it in that order, so a
wrong order is a wrong model, often with no error.

## Group repeated features

Four identical corner bosses are **one** feature with a count and a placement
rule, not four. Name the layout: `GridLocations`, `PolarLocations`, or
`Locations` with a named point list
([[text-patterns-and-surface-detail#patterns-locations-then-one-boolean]]). A
repeated feature spelled out N times is implemented as N hand-placed copies,
and the next edit has to touch all of them. The count also sets the web between copies
([[wall-thickness-and-hollowing#a-repeated-features-count-is-a-wall]]).

## Finishing

```python
body = fillet(body.edges().filter_by(Axis.Z), p.corner_r)       # vertical edges
bed = body.faces().sort_by(Axis.Z)[0]
body = chamfer(bed.edges(), length=0.3, length2=0.52, reference=bed)  # bed edge: 30° off vertical
```

- **Fillets last**, after every boolean.
- A **unified corner radius** on the vertical edges is what makes a printed
  part read as designed rather than as a CAD default. State one radius in the
  spec and apply it everywhere eligible.
- Break the bed-contact edge by default, never ask: an asymmetric chamfer at
  most 30° off vertical, short leg on the bed face, never a fillet or a 45°
  chamfer, which the overhang gate fails
  ([[rounded-bodies-on-the-print-bed#breaking-the-bed-edge]]).
- If `fillet()` fails on a solid, move the radius into the sketch profile as a
  2D fillet, or into the lofted section. Do **not** silently reduce a radius
  the user specified — a retry ladder converts a hard failure into an invisible
  cosmetic regression ([[fillet-chamfer-pitfalls]]).

## Pitfalls

- Choosing a detail as the base solid because it is visually prominent — run
  the squint and removal tests.
- Listing a repeated feature as N rows instead of one array row.
- Fillets placed before the booleans they must survive.
- Additions that touch the base at a tangent instead of overlapping it.

## Per-feature risks worth naming

The risk each feature row most often carries, and its standard answer:

- *fillet may fail at this radius* → fall back to a 2D sketch or section fillet;
- *boss tangent to the wall* → root it in by ≥ 1 mm;
- *cut may be refilled by the later union* → move after, then verify;
- *loft sections index-mismatched* → sample on rails, same point count
  ([[loft-pitfalls]]);
- *smooth loft may overshoot* → `ruled=True` with dense stations;
- *cutter severs the body* → clip the tool to one side;
- *decoration tool misses the skin* → anchor it on a solved surface point;
- *feature below the FDM minimum* → deepen, thicken, or drop and say so;
- *overhang > 45°* → name the print orientation or add a chamfer.
