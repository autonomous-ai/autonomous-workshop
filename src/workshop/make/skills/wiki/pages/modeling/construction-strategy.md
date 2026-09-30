---
title: Construction strategy and operation order
tags: [construction, strategy, boolean-order, fillet, operation-order, part-vs-assembly, revolve]
aliases: [modeling strategy, feature order, build order, boolean order, feature tree order]
sources:
  - skills/cad/references/build123d-modeling.md (design strategy, before the move)
  - skills/image-to-cad/references/build123d-operations.md (boolean order and finishing, before the move)
  - "experience: parts that compiled and validated with the hole in the wrong face or refilled by a later union"
related: [operation-families, feature-recipes, boolean-pitfalls, fillet-chamfer-pitfalls, build123d-selectors]
updated: 2026-09-23
---

# Construction strategy and operation order

Decide how a part is constructed before writing geometry code. The
construction family is chosen once and every later edit inherits it: a form
authored in the wrong family cannot be rescued by parameter edits, only by
re-authoring. Pick the family per form with [[operation-families]].

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
  clearances, fits and per-part mesh export.
- **Pick the origin and orientation from the functional datum before
  sculpting.** Model on the mating interface, mounting plane, or symmetry axis.
- **Order operations so fragile steps come last and failures localize.** Base
  solid → major additions → subtractive features → shell → through-wall holes
  → fillets and chamfers last. Fillets are the most failure-prone operation and
  every boolean invalidates selectors, so postpone them. Structure the source
  so each feature is a named step — a per-feature function or a distinct
  intermediate variable — so a failed operation points at exactly one feature
  and a parameter change touches one obvious place.
- **Overshoot boolean tools.** Extend cutting tools past the faces they enter
  and exit; for through-cuts, go roughly 1 mm beyond both faces. Coincident or
  coplanar tool/target faces are a classic kernel failure. Cut repeated or
  patterned features in one combined operation ([[boolean-pitfalls]]).
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
- **Mixed objects decompose naturally**: a lofted outer skin carrying the
  appearance, with extruded/booleaned interior carrying the engineering.

## Boolean order

```text
base solid → additive (union) → shell → interior additive → subtractive (cut) → fillet
```

- **Union before cut**, unless the cut is what makes the shape possible. A hole
  cut before a union is silently refilled — no error, wrong part.
- **Shell before interior bosses**, or the shell hollows them.
- **Cut through-features after all unions**, then re-verify with
  `scripts/inspect refs --facts`: a later boolean can refill, shift, or enlarge
  an opening silently.
- **Fillet last.**
- **Gate the result, do not trust it** ([[kernel-validity]]).

State the order as integers in the build spec's feature table. That ordering
**is** the body of `gen_step()`.

## Finishing

```python
body = fillet(body.edges().filter_by(Axis.Z), p.corner_r)       # vertical edges
body = chamfer(body.faces().sort_by(Axis.Z)[0].edges(), 0.6)    # bed-contact edge
```

- **Fillets last**, after every boolean.
- A **unified corner radius** on the vertical edges is what makes a printed
  part read as designed rather than as a CAD default. State one radius in the
  spec and apply it everywhere eligible.
- Always chamfer the bed-contact edge (~0.6 mm) — it lifts off cleaner and
  hides elephant's foot. This is an engineering default; never ask about it.
- If `fillet()` fails on a solid, move the radius into the sketch profile as a
  2D fillet, or into the lofted section. Do **not** silently reduce a radius
  the user specified — a retry ladder converts a hard failure into an invisible
  cosmetic regression ([[fillet-chamfer-pitfalls]]).

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
