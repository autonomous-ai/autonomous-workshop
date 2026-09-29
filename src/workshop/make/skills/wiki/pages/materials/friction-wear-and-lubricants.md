---
title: Friction, wear and lubricants for printed parts
tags: [friction, wear, bushing, lubricant, grease, tribology, sliding]
aliases: [tribology, plain bearing material, wear resistance, grease compatibility, lubrication, sliding contact, iglidur]
sources:
  - https://www.igus.eu/3d-printing/material/test-laboratory
  - https://www.igus.com/plastic-bearings/resources/company-iglide-tribo-filament-test
  - https://www.nyelubricants.com/material-compatibility
  - Maries et al., Determining the tribological properties of different 3D printing filaments, IOP Conf. Ser. Mater. Sci. Eng. 724 012022 (2020), https://iopscience.iop.org/article/10.1088/1757-899X/724/1/012022/pdf
  - Comprehensive Sliding Wear Analysis of 3D-Printed ABS, PLA, and HIPS, https://pmc.ncbi.nlm.nih.gov/articles/PMC12298762/
  - Mechanical, Fatigue, and Thermal Characterization of ASA, Nylon 12, PC, and PC-ABS Manufactured by FFF, https://pmc.ncbi.nlm.nih.gov/articles/PMC12845617/
related: [shafts-and-bearings, gears, joints, filament-properties, linear-guides-and-slides]
updated: 2026-09-23
---

# Friction, wear and lubricants for printed parts

Printed journals, slides and gears wear. How fast depends on the material
pair, the load and the surface, and ordinary filaments are not made for it.

## Ordinary filaments wear fast against steel

A bearing manufacturer's test rig (igus) compared its wear-optimised
("tribo") filaments with standard 3D-printing plastics:

| test | conditions | result |
|---|---|---|
| linear long stroke | 0.11 MPa, 0.34 m/s, 370 mm stroke, aluminium shaft | FDM tribo filament i180: **15 × lower wear than ABS**; SLS iglidur i3: 33 × lower |
| linear short stroke | 1 MPa, 0.3 m/s, 5 mm stroke | printed J260 wore like injection-moulded J260, many times less than ABS |
| pivoting | 20 MPa, 0.01 m/s, 60° | SLS i3 up to 50 × higher abrasion resistance than PA12 |
| rotating | 1 MPa, 0.1 m/s | SLS i3 about 2 × better than PA12 |
| lead-screw nut | 129 N load, 290 rpm, 370 mm stroke | 6–18 × better than conventional printed materials; **standard ABS failed quickly** rotating on a stainless shaft |

These are one manufacturer's tests of its own product, but the direction is
consistent: **ABS and PLA are poor sliding materials.** For a bushing,
nut or slide that runs for hours, use a wear-optimised filament, a bought
bushing, or a ball bearing ([[shafts-and-bearings#bushing-or-ball-bearing]]).

Academic pin-on-disc work agrees on the ordering. One sliding-wear study
found ABS under 0.15 mm³ mean wear volume across all conditions, against
1.5 mm³ for PLA and 3.0 mm³ for HIPS. Another found that PLA's wear rate rose
and its friction coefficient fell as sliding speed increased. Among one
maker's filaments pinned against steel, a PETG and a glass-type copolyester
had the lowest wear.

Nylon 12 had the highest fatigue resistance of four FFF materials in a
separate study ([[printed-fatigue]]), which is one reason nylon is the usual
printed gear and bushing material.

## Design rules for sliding contact

- **Pair unlike materials:** a printed bore on a steel or brass shaft runs
  better than plastic on plastic of the same kind.
- **Keep bearing pressure low:** the test rig pressures above (0.1–1 MPa for
  continuous motion) are the regime where printed plastics were measured;
  pressure = load / (bore × length).
- **Layer ridges are the first wear surface.** Orient a slide so it runs
  along the layers, or ream/sand the bore.
- **Clearance grows as it wears:** derive the running fit from `cadfits`
  ([[fit-derivation]]) and expect it to open.
- **Heat from friction softens PLA** at 55–60 °C ([[heat-resistance-of-printed-parts]]):
  fast or loaded sliding needs a higher-temperature material.

Friction also decides whether a slider binds: [[linear-guides-and-slides]].

## Lubricants: check the base oil against the plastic

A lubricant manufacturer (Nye) groups plastics by sensitivity:

- **Compatible with all base oils:** acetal (POM), polyamide (nylon), PBT,
  PTFE, polyimide, PEI, polyamide-imide, phenolic.
- **Usually attacked only by polar base oils such as esters:** ABS,
  polycarbonate, polyester (PET/PETG), PPO, polysulfone, PVC.
- **Generally safe base oils:** synthetic hydrocarbons (PAO), multiply
  alkylated cyclopentanes, silicone oils, PFPE.

Higher temperatures and lower viscosities raise the risk. The attack shows up
as environmental stress cracking in a loaded part. So for ABS, PC and PETG
parts use a silicone- or PFPE/PTFE-based grease or a PAO grease, never an
ester oil, and test the pair when the part is loaded. Nye's own advice is to
validate with tensile, dimensional and weight-change tests.

## Open items

Wear rate, friction coefficient and running temperature are properties of the
pair, the load and the speed. Record every sliding joint's material pair and
lubricant; no rigid sweep answers them.
