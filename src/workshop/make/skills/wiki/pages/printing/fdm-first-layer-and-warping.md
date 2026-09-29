---
title: First layer, elephant's foot and warping
tags: [first-layer, elephant-foot, warping, curling, brim, mouse-ears, bed-adhesion, shrinkage, chamfer, enclosure]
aliases: [elephant foot, elephants foot, corner lifting, curling corners, brim ears, anti-warp tabs, bed adhesion, raft]
sources:
  - https://help.prusa3d.com/article/elephant-foot-compensation_114487
  - https://help.prusa3d.com/article/layers-and-perimeters_1748
  - https://www.hydraresearch3d.com/design-rules
  - https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
  - https://www.simplify3d.com/resources/print-quality-troubleshooting/warping/
  - https://www.xometry.com/resources/3d-printing/3d-print-warping-pla-petg-abs/
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
related: [overhangs-and-print-orientation, fdm-design-rule-tables, wall-thickness-and-hollowing, print-in-place-mechanisms]
updated: 2026-09-23
---

# First layer, elephant's foot and warping

The bed face is the one face of every print that the process deforms on
purpose: it is squashed for adhesion, and it is where cooling stress pulls
hardest. Design the bottom edge for both.

## Elephant's foot

The first layer is pressed into the bed to stick, so it spreads wider than
the model. That lip is elephant's foot (Prusa). Slicers compensate by
shrinking the first layer; Prusa's "values around 0.2 mm usually work well
for the default 0.4 mm nozzle", and it is on by default in their profiles.
The first layer itself is 0.20 mm in every Original Prusa profile.

Design-side fix: chamfer the bottom edge so the lip has somewhere to go.
Hydra Research sizes the base chamfer at **~0.3 mm (first layer height + one
layer height)**; the Hubs FDM article recommends a 45° chamfer or radius on
edges that touch the build plate. Use a chamfer, not a fillet, on the bed
side: a fillet's lower edge is an overhang ([[joints#rules-that-are-easy-to-break]]).

```python
BASE_CHAMFER = FIRST_LAYER_H + LAYER_H   # ~0.3 mm at 0.2 + 0.1…0.2
```

A bottom edge that must mate or seal: model the chamfer, or measure the part
with the lip and say so.

A gap between two moving bodies near the bed closes the same way:
[[print-in-place-mechanisms]].

## Why parts warp

Plastic shrinks as it cools. Simplify3D: an ABS part printed at 230 °C and
cooled to room temperature "will shrink by almost 1.5 %", which is several
millimetres on a large part. The upper layers shrink onto the lower ones,
and the stress lifts corners off the bed. Xometry orders the common
materials: PLA lowest shrinkage (corner lift on large flat parts), PETG in
between, ABS highest ("shrinks so fast") and needing sustained temperature
control.

## Design against warping

| lever | rule | source |
|---|---|---|
| round the base corners | R > 4 mm on corners that touch the bed | Hydra Research |
| thin tall walls | add ribs, as in injection moulding | Stratasys Direct |
| brim | spreads shrinkage stress over more bed; only a few layers tall, so it holds edges down | Simplify3D, Xometry |
| mouse ears / brim ears | discs at high-risk corners only: grip where it is needed, easier removal | Xometry |
| raft | for high-shrink materials such as ABS | Xometry |

Process levers belong in the print notes, not the model: an ABS bed at
100–120 °C, part cooling off for warp-prone materials, and a heated enclosure
for tall parts (Simplify3D).

## Checks

- Every bed-contact edge is chamfered, not filleted, by at least
  `FIRST_LAYER_H + LAYER_H`.
- Large flat bases in ABS/ASA get rounded corners (≥ 4 mm) and a note calling
  for a brim or ears.
- The model's bottom face is at Z = 0 and flat: warping lifts corners, it
  does not straighten a base designed with a crown.
