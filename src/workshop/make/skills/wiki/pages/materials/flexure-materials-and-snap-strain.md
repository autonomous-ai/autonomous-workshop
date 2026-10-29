---
title: Flexure materials and living hinges
tags: [flexure, living-hinge, strain, compliant, tpu, nylon, petg, pp]
aliases: [compliant mechanism, flexible hinge, integral hinge, printed spring, flexure material]
sources:
  - https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/
  - https://www.protolabs.com/resources/blog/how-to-design-3d-printed-living-hinges/
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla (PLA elongation)
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/petg-pet/polylite-tm-petg
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/tpu/polyflex-tm-tpu95
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/nylon/polymide-tm-copa
  - Mechanical, Fatigue, and Thermal Characterization of ASA, Nylon 12, PC, and PC-ABS (FFF), https://pmc.ncbi.nlm.nih.gov/articles/PMC12845617/
related: [joints, flexures-and-living-hinges, snap-fit-design, printed-fatigue, creep-and-stress-relaxation, layer-anisotropy, filament-properties]
updated: 2026-10-10
---

# Flexure materials and living hinges

A part that works by bending is limited by strain, not stress. Every rule
here comes down to keeping the peak strain below what the printed material
survives, in the direction it was printed, for the number of cycles needed.
The strain limits themselves — single snap, repeated use, many cycles, held
deflected — are [[snap-fit-design#permissible-strain]].

## Living hinges

A living hinge is a thin web bent repeatedly. The polymer decides whether it
works at all.

- **FDM:** 0.4–0.6 mm thick with at least two layers. Orient the part so the
  hinge's **width**, not its length, is built layer by layer (often an
  upright part), so the bend runs along the strands. Give the hinge a long
  curved outer surface and a short inner one. One optimised FDM design
  reached only **25 cycles** before failure. Recommended materials are
  nylon 12, or a rigid body with a TPU or other flexible section by dual
  extrusion.
- **SLS:** 0.3–0.8 mm thick and at least 5 mm long in PA12 or PA11, about
  30–50 cycles (one guide). Another (Protolabs) gives 0.020–0.040 in
  (0.5–1.0 mm) measured in the horizontal build direction, avoiding
  0.013 in (0.33 mm); minimum length 0.050 in (1.3 mm) for a 90° bend and
  0.150 in (3.8 mm) for 180°; "hundreds" of cycles; anneal and pre-flex
  before use. Protolabs recommends only SLS for functional living hinges.
- Both guides treat printed living hinges as proof-of-concept parts, less
  durable than moulded ones.

**Rule:** a PLA living hinge is a failure waiting for its first bends
(1.8–6.3 % elongation). If the hinge must last, use a pinned hinge
([[joints#revolute-joints]]), a print-in-place hinge, or a TPU section.

## Flexures and printed springs

- **Nylon** was the most fatigue-resistant of four FFF materials (Nylon 12
  fatigue limit 7.4 MPa stress range at 10⁶ cycles), and it tolerates creep
  without rupture: the default for flexures that cycle.
- **PETG** has more elongation than PLA (8.4 %) and less creep; acceptable for
  flexures with few cycles.
- **PLA** is the stiffest and least ductile common filament; use it only for
  flexures that move a few times.
- **TPU 95A** (E ≈ 34 MPa, over 500 % elongation) is a rubber, not a spring:
  choose it for grips, bumpers and compliant sections. It stores little
  energy per millimetre.
- Size a flexure's thickness from the strain budget
  ([[snap-fit-design#permissible-strain]]; ε = t / (2R) for a strip bent to
  radius R), then check the force it gives.
