---
title: Bridging, supports and sacrificial layers
tags: [bridge, support, sacrificial-layer, counterbore, nut-trap, interface, overhang, support-free]
aliases: [bridging, max bridge length, support interface, support z distance, sequential bridging, sacrificial bridge, floating hole, counterbore hole]
sources:
  - https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
  - https://mit.ek.dk/media/s4sf4t3k/3d_printing_design_rules-ultimaker.pdf (3D Hubs poster)
  - https://www.hydraresearch3d.com/design-rules
  - https://qidi3d.com/blogs/news/3d-printing-bridging-techniques-guide
  - https://www.orcaslicer.com/wiki/print_settings/quality/quality_settings_bridging
  - https://hackaday.com/2017/10/17/sacrificial-bridge-avoids-3d-printed-supports/
  - https://hackaday.com/2023/05/28/3d-printing-bores-without-support/
  - https://help.prusa3d.com/article/support-material_1698
related: [overhangs-and-print-orientation, fdm-design-rule-tables, fdm-hole-accuracy, printed-threads-and-bosses, print-in-place-mechanisms]
updated: 2026-09-23
---

# Bridging, supports and sacrificial layers

A bridge is a strand stretched between two supported points. It sags in
proportion to its span and to how slowly it cools. This page is about spans
and features that would otherwise float; the overhang angle rules are in
[[overhangs-and-print-orientation]].

## How far a bridge can go

| span | result | who |
|---|---|---|
| < 5 mm | no visible sag or support marks | Hubs FDM article |
| ≤ 10 mm | printable without support | 3D Hubs poster; Hydra Research "< 10 mm" |
| < 20 mm | clean on default settings | QIDI bridging guide |
| 20–50 mm | slight sag that disappears after 2 solid layers | QIDI |
| 50–80 mm | visible sag, compromised finish | QIDI |
| > 80 mm | unreliable without mid-span support | QIDI |

The design takeaway: keep a *visible* bridge under 5 mm, keep any bridge
under 10 mm if you cannot tune the printer, and treat 20–80 mm as a tuned
printer's ability, not a design allowance.

Slicer settings that make a bridge (QIDI; OrcaSlicer): bridge speed
20–30 mm/s; bridge flow 0.80–0.90 so the strand is lighter; part fan 100 %
for PLA/PETG (ABS/ASA start at 0 %); nozzle at the low end of the material
range. OrcaSlicer's "thick bridges" prints the bridge at a line height equal
to the nozzle diameter: stronger over long spans, rougher, and suited to
internal bridges over sparse infill.

The ceiling of every print-in-place gap is such a bridge:
[[print-in-place-mechanisms]].

## Design out the bridge

In order of preference (QIDI, Hackaday):

1. **Shorten it**: a mid-span pillar turns one long span into two short ones.
2. **Rotate the part**: 45° often turns a bridge into a self-supporting
   overhang.
3. **Replace a flat roof** over a hole with a 45° chamfer or teardrop
   ([[fdm-hole-accuracy#horizontal-holes-teardrops-and-horiholes]]).
4. **Give a floating feature something to stand on** (next two sections).

## Floating holes: sacrificial bridge

A hole that starts in mid-air, such as a counterbore's through-hole or a nut
trap under a bridge, makes the printer "draw circles in mid-air". The
sacrificial bridge closes the hole with a thin solid layer at that height. The
printer bridges it flat, prints the round hole on top, and afterwards you
drill through the membrane (Hackaday, 2017). That is far easier than digging
support out of a captive pocket.

Slicers now do this without CAD changes. OrcaSlicer's "counterbore hole
bridging" has modes None / Partially Bridged / Sacrificial Layer, and the
sacrificial layer must be broken through after printing. If the model is
handed to an unknown slicer, model the membrane (one or two layers thick at
the project layer height) and record the drilling step.

## Floating holes: sequential bridging

For a bore that must come out clean with no drilling, bridge in stages
(Hackaday, 2023): 2–3 bridging layers make a rectangle as wide as the bore,
then a second set at 90° turns it into a square. Large holes may need three
sets at 60° offsets. Every stage gives the next layer edges to stand on. It
has to be modelled in CAD, as stepped pockets one or two layers tall each.

## When support is unavoidable

Prusa's settings that decide how a supported face looks:

- **Top contact Z distance**: 50–75 % of layer height works well. 0 means no
  gap, which welds the support to the part and disables bridge flow.
- **Interface layers**: a much denser pattern than the support body, so the
  supported face is flat.
- **XY separation**: can be a percentage of the external perimeter width,
  for example 150 %.
- **Pattern spacing**: wider spacing is easier to remove, but interface layers
  then sag between lines.
- **Organic supports**: easy to remove, do not scar the surface.

A supported face is always rougher than a bed or top face. If a face must be
smooth, orient it away from supports rather than tuning them.
