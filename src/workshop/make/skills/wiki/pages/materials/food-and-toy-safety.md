---
title: Food-contact safety of printed parts
tags: [safety, food-safe, food-contact, regulation]
aliases: [food safe, food contact, food grade, dishwasher safe, 21 cfr, regulation 10/2011]
sources:
  - https://formlabs.com/blog/guide-to-food-safe-3d-printing/
related: [heat-resistance-of-printed-parts, filament-properties, sealing-and-ingress-protection, moulds-and-casting-from-prints, toy-safety-constraints]
updated: 2026-10-10
---

# Food-contact safety of printed parts

This page is a design checklist, not compliance advice. A product that is sold
has to be tested to the regulation that applies to it. Toy rules (small parts,
use-and-abuse, edges, entrapment, magnets) are [[toy-safety-constraints]].

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

## Open items

Chemical-migration testing is outside anything this repository can verify;
the spec states the part's food-contact status.
