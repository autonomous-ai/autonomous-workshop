---
title: Food-contact and toy safety basics
tags: [safety, food-safe, toy, small-parts, choking, regulation]
aliases: [food safe, food contact, small parts cylinder, choking hazard, child safety, 16 cfr 1501, en 71, astm f963, iso 8124]
sources:
  - https://formlabs.com/blog/guide-to-food-safe-3d-printing/
  - 16 CFR 1501.4 Size requirements and test procedure, https://www.law.cornell.edu/cfr/text/16/1501.4
  - https://www.avenotester.com/toy-safety-small-part-cylinder-atb01_p94.html (31.7 mm inner diameter; EN 71-1 8.2, ASTM F963 4.6, 16 CFR 1501, ISO 8124-1 5.2)
  - http://en.tomy.org.cn/product/showproduct.php?lang=cn&id=179 (depths 25.4 and 57.1 mm, via search listing)
related: [heat-resistance-of-printed-parts, printed-part-count, creep-and-stress-relaxation, filament-properties, sealing-and-ingress-protection, moulds-and-casting-from-prints]
updated: 2026-09-23
---

# Food-contact and toy safety basics

This page is a design checklist, not compliance advice. A product that is sold
has to be tested to the regulation that applies to it.

Sealing a printed wall with a coating: [[sealing-and-ingress-protection]].

## Food contact

Regulations: in the US, the FDA's food-contact rules (21 CFR); in the EU,
Regulation 10/2011 on plastic food-contact materials (Formlabs). A filament
marketed as food-safe covers only the raw material. The printed part can
still be unsafe:

- **Layer lines** leave narrow crevices where bacteria (E. coli, salmonella)
  and moulds grow and cleaning cannot reach.
- **Brass nozzles can contain lead**; food-contact parts need a stainless
  steel nozzle, and a printer that ran other materials may leave residue.
- **Additives, colourants and thermal degradation:** approval covers the
  polymer with its additives, and printing can oxidise and degrade it. Dyes
  leach; avoid dyeing.
- **Heat:** PLA, PET and nylon soften around 60–70 °C, so they are unsuitable
  for the dishwasher. Hot liquids need co-polyester, high-temperature PLA or
  PEI ([[heat-resistance-of-printed-parts]]).

Mitigations named by Formlabs: smooth the surface (chemically, or by printing
at the lowest feasible layer height), and seal it with a food-safe epoxy or
polyurethane coating, noting that "coatings don't guarantee food safety".
Short contact with dry food is lower risk than long contact with wet or fatty
food.

**Design rule:** a printed part meant to touch food is marked single-use or
sealed, with the nozzle, material and coating recorded in the spec.

Casting a food-safe silicone from a printed master:
[[moulds-and-casting-from-prints]].

## Small parts and choking (children under 3)

US 16 CFR 1501: no toy or children's article intended for children under 3
may fit entirely, without compression and in any orientation, into the small
parts test cylinder. This applies after the "use and abuse" tests
(16 CFR 1500.51/1500.52, excluding bite tests); every piece that comes off
(other than paper, fabric, yarn, fuzz, elastic and string) is tested again.

The cylinder (also used by EN 71-1 §8.2, ASTM F963 §4.6 and ISO 8124-1 §5.2):
inner diameter **31.7 mm (1.25 in)**, depth **25.4 mm (1.00 in)** at the
shallow side and **57.1 mm (2.25 in)** at the deep side.

Consequences for a printed toy:

- **Every part a child can separate** (a wheel, a pin, a snap cap) is a
  candidate small part. Check each one's size against the cylinder.
- **Print-in-place and captured parts help**: a part that cannot come off
  under abuse is not tested alone ([[printed-part-count#print-in-place-before-splitting]]).
- **Retention is a safety property**, not just a mechanism property. A
  friction fit that loosens ([[creep-and-stress-relaxation]]) can release a
  small part later.
- A part that breaks under the abuse tests is tested in pieces, so brittle
  thin features can create small parts; PLA's notched impact is among the
  lowest of common filaments ([[filament-properties]]).

```python
SMALL_PARTS_D, SMALL_PARTS_DEPTH_SHALLOW = 31.7, 25.4   # mm, 16 CFR 1501 / ISO 8124-1 cylinder
# a separable part is a choking hazard for under-3s if it fits in the cylinder in any orientation
```

## Open items

Compliance testing (use-and-abuse, chemical migration, labelling for ages
3–6) is outside anything this repository can verify. Record the intended age
group and food-contact status in the spec.
