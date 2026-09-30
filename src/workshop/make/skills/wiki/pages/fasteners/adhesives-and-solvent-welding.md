---
title: Adhesives and solvent welding for printed parts
tags: [adhesive, glue, cyanoacrylate, epoxy, solvent-weld, acetone, bonding]
aliases: [super glue, CA glue, two-part epoxy, ABS juice, acetone weld, plastic welder, gluing prints, bonded joint]
sources:
  - https://blog.prusa3d.com/the-great-guide-to-gluing-and-assembling-3d-prints_44908/ (adhesives per material, tensile results, activator heat, gap filling)
  - https://clevercreations.org/best-glue-for-pla-abs-petg-adhesive/ (gel CA for PLA, ABS acetone slurry; via search excerpt)
  - https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts (inserts in resin prints glued with CA or epoxy)
related: [printed-part-count, dowel-pins-and-press-fits, heat-set-inserts, post-processing-and-finishing, thermal-expansion-and-hybrid-parts]
updated: 2026-09-23
---

# Adhesives and solvent welding for printed parts

Glue is the joint for parts that never come apart, and a split you had to make
([[printed-part-count]]). Every glued joint still needs a locating feature: a
peg, key or dowel. Glue fixes the parts; it does not position them.

## What bonds what

| material | works | does not / caution |
|---|---|---|
| PLA | CA (gel CA gives control and fills small gaps); dichloromethane; plain acetone reported to glue it; two-part epoxy works but isn't the best | acetone does not smooth PLA even where it glues it |
| PETG | CA (13.06 MPa in Prusa's tensile test with Alteco CA); two-part epoxy; methacrylate plastic welders; THF-based PVC cement (user reports) | inert to the solvents a hobbyist has, so no practical solvent weld |
| ABS / ASA | acetone solvent weld, or an acetone slurry of dissolved ABS ("ABS juice"); CA (7.23–9.44 MPa on ASA) | styrene model cements vary: one tested did not react with ASA at all |
| SLA resin | CA bonds almost instantly; UV resin fills gaps and hides seams; epoxy | — |
| TPU / flexible | CA if the mating faces are at least a bit stiff; contact cement | — |
| PC | adhesives marketed for polycarbonate | — |

Prusa's tensile results, for scale: Peckalep Medium CA on PLA 10.20 MPa,
Alteco CA on PETG 13.06 MPa, Tamiya Extra Thin Cement on ASA 6.06 MPa.

Vapour smoothing per material: [[post-processing-and-finishing]].

## Practice

- **Surfaces:** clean and as level as possible; a CA bond is only as good as
  its contact area.
- **Gaps:** CA does not fill gaps. Use two-part epoxy, or CA thickened with
  talcum powder or microballoons.
- **Activator heat:** CA accelerators cure exothermically. The heat can deform
  low-temperature materials like PLA.
- **Inserts in resin prints:** resin does not melt, so heat-set inserts are
  glued into a stepped hole with thick CA or epoxy
  ([[heat-set-inserts#installing]]).

## Design for a bonded joint

- A bonded joint has no gate: no geometry check measures bond strength. Record
  every glued joint in the spec as a limitation. Glue only what never moves,
  and say so ([[automata-patterns#rules-shared-by-every-layout]]).
- Give the joint location (pegs, a key, a dowel) so it assembles one way and
  the glue only holds ([[mechanism-failures]] row 6: parts joined on bare glued
  faces had no location).

Bonding plastic to metal across a temperature range:
[[thermal-expansion-and-hybrid-parts]].
