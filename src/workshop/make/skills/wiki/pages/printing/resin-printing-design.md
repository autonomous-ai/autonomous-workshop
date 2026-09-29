---
title: Designing for resin (MSLA/SLA) printing
tags: [resin, sla, msla, drain-hole, hollow, suction, cupping, support, shrinkage, post-cure, clearance, emboss, engrave]
aliases: [stereolithography, vat photopolymerization, lcd printer, dlp, photopolymer, resin printer, drain hole, vent hole, suction cup, cupping blowout, trapped resin, post cure warp, formlabs design specs]
sources:
  - https://formlabs.com/support/Design-specifications-for-3D-models-form-3 (Form 3, Clear Resin at 100 µm)
  - https://formlabs.com/white-papers/form-4-design-guide/
  - https://support.formlabs.com/s/article/Design-Specs (Form 2: drain holes ≥ 3.5 mm; via search excerpt)
  - https://formlabs.com/blog/how-to-hollow-out-3d-models/
  - https://formlabs.com/support/Cupping-Blowout
  - https://formlabs.com/support/Warping-SLA/
  - https://formlabs.com/global/products/clear-resin/ (Clear Resin V5 properties)
  - https://www.hubs.com/knowledge-base/how-design-parts-sla-3d-printing/
  - https://ameralabs.com/blog/3d-design-parts-sla-3d-printing/
related: [wall-thickness-and-hollowing, fdm-minimum-feature-sizes, fdm-design-rule-tables, print-in-place-mechanisms, heat-set-inserts, adhesives-and-solvent-welding, filament-properties, overhangs-and-print-orientation, moulds-and-casting-from-prints]
updated: 2026-09-23
---

# Designing for resin (MSLA/SLA) printing

A resin printer cures liquid photopolymer layer by layer, usually hanging the
part upside down from the build plate and peeling each layer off a film. That
changes which rules bind compared with FDM: detail and thin walls are easy,
while **trapped liquid, trapped air, peel suction, shrinkage and brittleness**
are the failures. Use this page when a part will be printed in resin instead
of filament; the FDM rules live in [[fdm-design-rule-tables]].

## Design numbers, two sources

Values are minimums at which the feature still forms, not what survives use.
Formlabs figures are for Clear Resin at 100 µm layers; they vary by resin and
layer height. The service-bureau figures (Protolabs Network / Hubs) are
generic across machines and more conservative; design to them unless the
printer is known.

| feature | Formlabs Form 3 | Formlabs Form 4 | Hubs (generic SLA) |
|---|---|---|---|
| supported wall (joined on ≥ 2 sides) | 0.2 mm | 0.2 mm | 0.4 mm |
| unsupported wall (joined on < 2 sides) | 0.2 mm | 0.2 mm | 0.6 mm |
| unsupported overhang length | ≤ 5.0 mm | ≤ 5.0 mm | ≤ 1.0 mm |
| unsupported overhang angle | ≥ 10° from level | ≥ 10° from level | ≥ 19° from level |
| horizontal span (5 × 3 mm beam) | 29 mm | 29 mm | — |
| vertical wire, 7 mm tall / 30 mm tall | Ø 0.2 / Ø 1.5 mm | Ø 0.3 / Ø 0.6 mm | — |
| embossed detail height | 0.1 mm | 0.1 mm | 0.1 mm |
| engraved detail width and depth | 0.15 mm | 0.15 mm | 0.4 mm |
| hole diameter | 0.5 mm | 0.5 mm | 0.5 mm |
| clearance between parts | 0.5 mm | 0.4 mm | 0.5 mm moving, 0.2 mm assembly, 0.1 mm snug |
| drain hole | Ø 2.5 mm | Ø 0.75 mm | Ø 3.5 mm |
| hollow shell wall | — | — | ≥ 2 mm |

Formlabs' Form 2 spec gave Ø 3.5 mm drain holes; the smaller Form 3/4 values
depend on those printers' resin handling. For an unknown printer, use
**Ø 3.5 mm**.

These are finer than the FDM minimums
([[fdm-minimum-feature-sizes]]), but "forms" is not "survives": a 0.2 mm wall
is a membrane in a brittle material. Structural walls stay at 1–2 mm
(AmeraLabs) — see shrinkage below.

## Hollowing, drains and vents

A solid resin part costs resin and builds shrinkage stress; hollowing cuts
both, and in resin (unlike FDM) the saved volume really is saved material —
Formlabs' example bust lost 77 % of its resin at a 2 mm shell
([[wall-thickness-and-hollowing#hollowing-is-worth-less-than-the-volume-it-removes]]).

The rules the hollow owes:

- **Shell ≥ 2 mm** (Hubs), more for a large or loaded part. A hollow part has
  no internal scaffolding; the shell carries everything.
- **Every enclosed cavity has at least one drain**, or uncured resin stays
  sealed inside, keeps curing, and cracks the part later
  ([[wall-thickness-and-hollowing#when-not-to-hollow]]).
- **Two holes per cavity is the working rule** (Formlabs): one as close to
  the build plate as possible, and at least one more, so air enters while
  resin leaves and the part can be washed through. A single hole drains
  poorly and traps wash solvent.
- Place drains on a face that will not be seen, and on the face nearest the
  build plate in the chosen orientation — that is the first face printed and
  the one where the cup forms.
- Internal ribs or pillars inside a hollow make separate pockets; each pocket
  needs its own path to a drain.

## Suction cupping

A hollow or concave region that opens **toward the build plate** traps air
(or resin) as each layer peels. The trapped volume expands on the peel, the
pressure inside drops, and the wall buckles or bursts — "cupping blowout":
holes, ragged ruptures, poor surfaces on the cup (Formlabs). Small cups and
thick cup walls may survive; large thin cups do not.

Fixes, in order: reorient so the concave side does not face the plate; add a
vent/drain at the cup's deepest point (the first layers printed); thicken the
cup wall. The mechanism is pressure on an area, so the risk grows with the
cup's projected area, not its depth.

## Orientation and supports

- Print large flat faces **at an angle** to the plate, not parallel to it:
  each layer's peel force scales with the cured area of that layer, and a
  flat part parallel to the plate warps on its supports (Formlabs warping).
- Every local minimum (a downward point, the lowest point of an island) must
  get a support; an unsupported minimum starts in mid-air and the layer is
  lost.
- Support touch-points leave marks; put them on hidden faces by orientation,
  and keep cosmetic and mating faces facing away from the plate.
- Thin walls are best printed perpendicular to the plate (edge first).
- Leave parts on supports during post-cure (Formlabs): the supports hold the
  shape while the resin finishes shrinking.

## Shrinkage and post-cure distortion

Resin shrinks as it cross-links, and again in post-cure under heat and UV.
Distortion comes from **uneven** shrinkage:

- **Uniform walls.** Thick and thin sections shrink by different amounts and
  stop at different times; keep walls in the 1–2 mm band and make every
  change of thickness gradual (AmeraLabs).
- Stiffen with ribs at about 0.6 × wall thickness, not by thickening the
  wall; hollow the junction where ribs cross.
- Inside corner radius ≥ 0.5 × wall, outside radius ≈ 1.5 × wall
  (AmeraLabs) — the molded-plastic rule, which applies because resin is
  brittle and notch-sensitive.
- Undercured or unevenly cured parts warp when one side cures first; long
  washes let solvent swell edges (Formlabs). Thin walls and wires absorb IPA
  fastest (Form 4 guide).
- Tolerance: Formlabs quotes ±0.15 % (min ±0.02 mm) for 1–30 mm features on
  Form 4; a generic printer and resin will not hold that without
  calibration. Design critical fits as tunable parameters and print a
  coupon.

## Clearance for moving and mating parts

Resin needs **more** gap than its resolution suggests: uncured resin
wicked into a narrow gap cures in post-cure and bonds the faces. Use 0.5 mm
between moving parts (0.4 mm on a Form 4), 0.2 mm for assembly, 0.1 mm for
a push/snug fit (Hubs). A print-in-place resin mechanism also needs every
gap to **drain**: open both ends of each gap so wash solvent flows through,
and do not rely on a gap that is blind ([[print-in-place-mechanisms]]).
Resin has no elephant's foot or bridge droop in the FDM sense, but the first
(burn-in) layers on the plate are overexposed and can spread — keep gaps off
the plate or raise the part on supports.

## Material: brittle unless chosen otherwise

Standard resins are stiff and brittle. Clear Resin V5, post-cured: UTS
60 MPa, modulus 2.75 GPa, **elongation 8 %**, notched Izod 29 J/m, HDT
59 °C at 1.8 MPa (Formlabs). That is PLA-like stiffness with little
toughness under a notch ([[filament-properties]]). Consequences:

- Snap-fits, living hinges and press fits that work in PETG or nylon crack
  in standard resin. Use a tough/durable engineering resin and its
  datasheet's elongation for the strain limit ([[snap-fit-design]]).
- No heat-set inserts: resin does not melt. Glue an insert into a stepped
  hole ([[heat-set-inserts]]); bond resin to resin with CA or UV resin
  ([[adhesives-and-solvent-welding]]).
- Uncured resin left in a part keeps curing under ambient UV, which can
  warp or crack it later (AmeraLabs): wash and post-cure fully.

A resin master can stop platinum silicone curing:
[[moulds-and-casting-from-prints]].

## Embossed and engraved detail

Resin keeps text and texture FDM cannot: embossed detail ≥ 0.1 mm high,
engraved ≥ 0.15 mm (Formlabs) or ≥ 0.4 mm (Hubs, generic). Engraved detail
on a face toward the plate fills with support marks; put detail on faces
that point away from the plate. Engraved grooves hold wash solvent and
uncured resin — keep them open-ended where possible.

## Checks

```python
assert wall >= (0.4 if supported else 0.6), "resin wall below generic SLA minimum"
assert not hollow or shell >= 2.0, "hollow resin shell under 2 mm"
for cavity in cavities:
    assert len(cavity.drains) >= 2 and min(d.dia for d in cavity.drains) >= 3.5, \
        f"{cavity.name}: needs >= 2 drains of >= 3.5 mm (one near the plate)"
assert moving_gap >= 0.5, "resin moving parts fuse below 0.5 mm"
assert max(walls) / min(walls) <= WALL_RATIO_MAX, "non-uniform walls warp in post-cure"
```
