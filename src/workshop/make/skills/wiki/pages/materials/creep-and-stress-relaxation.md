---
title: Creep and stress relaxation in printed plastics
tags: [creep, stress-relaxation, press-fit, snap-fit, sustained-load, temperature]
aliases: [cold flow, loosening, sustained load, long-term load, creep rupture, relaxation]
sources:
  - Dogan, O., Short-term Creep Behaviour of Different Polymers Used in Additive Manufacturing under Different Thermal and Loading Conditions, Strojniški vestnik - Journal of Mechanical Engineering 68(2022)7-8, 451-460, DOI 10.5545/sv-jme.2022.191
  - Accelerated Aging Effect on Mechanical Properties of Common 3D-Printing Polymers, https://pmc.ncbi.nlm.nih.gov/articles/PMC8659210/
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla
related: [filament-properties, heat-resistance-of-printed-parts, fit-derivation, joints, flexure-materials-and-snap-strain, wall-mounting-and-hanging, thermal-expansion-and-hybrid-parts]
updated: 2026-09-23
---

# Creep and stress relaxation in printed plastics

A plastic part under a constant load keeps deforming (**creep**); a plastic
part held at a constant deformation slowly loses its force (**stress
relaxation**). Both are the same viscoelastic behaviour, both accelerate with
temperature, and neither shows up in a short tensile test or in any geometry
gate. They are why a printed press fit loosens, a snap latch stops clicking,
a bolted printed flange loses preload, and a shelf bracket sags over weeks.

## What one comparison measured

Printed then CNC-milled specimens of six materials, 3-hour tensile creep at
10 and 20 MPa and at 25, 40 and 60 °C (Dogan 2022):

- **Creep rate rises with stress and temperature for every material;** the
  load was the stronger factor. The increase is not linear in stress.
- **No rupture at 25 °C or 40 °C.** At 60 °C every material except PC broke
  after a while.
- **PLA had the worst creep resistance.** It crept far more than ABS under
  the same conditions and broke at 60 °C even at 10 MPa. The author's
  recommendation: PLA parts at room temperature with no load or very low
  static loads.
- **ABS** ruptured in about 3 minutes at 60 °C and 20 MPa.
- **Tough PLA** crept less than PLA but more than ABS; **CPE (a
  co-polyester)** less than ABS, PLA and tough PLA.
- **PC** had the highest creep resistance and was least affected by
  temperature and load; no specimen failed under any tested condition.
- **Nylon** showed the largest creep strain (most flexible) but did not
  break, even at 60 °C and 20 MPa.

Ranking for sustained load, best first: **PC > CPE/PETG-family > ABS > tough
PLA > PLA**, with nylon deforming most but not rupturing.

Put 60 °C next to PLA's heat deflection temperature of 58–60 °C
([[heat-resistance-of-printed-parts]]): a PLA part near its HDT under load is
a part that will fail.

UV aging makes it worse. In one accelerated UV-B test, creep behaviour
degraded in proportion to the strength lost (PETG lost 36 % tensile
strength) ([[uv-and-outdoor-exposure]]).

## Design rules

- **Sustained stress:** keep it a small fraction of short-term strength.
  10 MPa was already enough to rupture PLA at 60 °C in 3 hours. For a
  permanently loaded printed part, design against creep with a large safety
  factor and a material higher in the ranking.
- **Press fits relax.** An interference that grips at assembly loses force
  over time, faster when warm. For a joint that must stay tight, use a
  mechanical lock (key, flat, pin, screw) rather than relying on friction
  ([[joints#keyed-joints]]); treat friction retention as a limitation.
- **Snap fits that stay deflected creep open.** Design latches so the beam
  returns to zero deflection once engaged. A latch held permanently bent
  loses its hold ([[flexure-materials-and-snap-strain#snap-fit-strain]]).
- **Bolted printed parts lose preload.** Clamp through a metal sleeve or put
  a washer or spring washer under the head so the plastic is not the spring.
- **Heat is the multiplier.** A part near a motor, in a car
  ([[heat-resistance-of-printed-parts#hot-environments]]) or in the sun needs
  a material whose HDT is well above the service temperature.
- **Nylon:** creeps most but tolerates it without breaking. Choose it for
  flexing parts, not for holding a dimension under load.

A permanently loaded wall mount is the common creep case:
[[wall-mounting-and-hanging]].

Temperature cycling adds to the relaxation of a metal part pressed into
plastic: [[thermal-expansion-and-hybrid-parts]].

## What no gate here can tell you

Creep strain, relaxation rate and time to rupture depend on stress,
temperature, time, infill and layer bonding. Record every sustained-load
joint as an open item with its material, estimated stress and service
temperature. A rigid sweep or a short-term strength check never closes it.
