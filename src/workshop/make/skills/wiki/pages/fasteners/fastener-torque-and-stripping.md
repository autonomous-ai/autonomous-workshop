---
title: Fastener torque, stripping and choosing a threaded joint
tags: [torque, stripping, pretension, clamp-load, creep, thread-engagement, joining-method]
aliases: [tightening torque plastic, strip torque, torque out, bolt preload, which fastener, how to join printed parts]
sources:
  - https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment (torque-out and pull-out by method; 1 Nm on M3 > 1500 N pretension)
  - https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive (inserts 3–4 Nm, direct screw about 1 Nm)
  - EJOT PT® Screw brochure 02.11, pp. 8–9 (torque window, tightening torque formula, drive speed)
  - https://kingroon.com/blogs/3d-print-101/how-to-screw-into-3d-printed-parts (engagement 2–2.5 × d; via search excerpt)
  - https://hackaday.com/2024/12/03/torque-testing-3d-printed-screws/ (printed screws by orientation)
  - PennEngineering SI® datasheet p. SI-3 (compression limiters for plastic assemblies)
related: [heat-set-inserts, screws-into-plastic, nut-traps-and-captive-nuts, printed-threads, creep-and-stress-relaxation]
updated: 2026-09-23
---

# Fastener torque, stripping and choosing a threaded joint

A printed joint almost always fails at the plastic, not the steel screw; only
with a metal insert did the M3 screw head shear first. The torque a joint can
take is set by whichever interface gives first.

## How much torque a printed joint takes

M3, PETG, 4 perimeters, 100 % infill (CNC Kitchen):

| joint | torque-out | failure |
|---|---|---|
| screw directly into plastic | ≈ 1 Nm | plastic threads sheared |
| helicoil | ≈ 1 Nm | plastic threads sheared |
| nut in a pocket (side or bottom) | ≈ 2 Nm | PETG crushed |
| heat-set insert | 3 Nm (3–4 Nm in a second test) | insert turned, or screw head sheared |

**1 Nm on an M3 screw already makes more than 1500 N of pretension.** That is
plenty for most printed assemblies, so tighten gently; a torque-limited driver
removes the guesswork. For thread-forming screws, set the torque inside the
installation-to-stripping window with EJOT's rule:
`Tt = 0.5 × (0.5 × Ts,min + 1.5 × Ti,max)` ([[screws-into-plastic#torque-window]]).

## Engagement

Engage a screw in plastic 2–2.5 × its major diameter (7.5 mm for an M3 where
the joint must be tight). EJOT's installation depth for its plastic screws is
1.7–2.0 × d depending on the material.

## Clamp load relaxes

Plastic creeps under a steady load, so a tensioned screw in plastic loses
preload over time ([[creep-and-stress-relaxation]]). Where clamp matters, put
the load on metal: an insert with a flange, a nut, or a compression limiter
(PEM makes non-threaded metal limiters for exactly this).

## Choosing a threaded joint

| need | first choice | why |
|---|---|---|
| opened and closed repeatedly | heat-set insert | metal thread; 3–4 Nm vs about 1 Nm for a plastic thread |
| strongest pull-out, access to the back | nut in a pocket loaded against solid plastic | 166 kg, the best pull-out measured |
| assembled once, cheapest | screw directly into a 0.8–0.9 d hole | pull-out close to an insert's (118–142 kg), low torque |
| large, coarse, no hardware (lids, knobs) | printed thread ≥ M6–M8 | [[printed-threads]] |
| resin print | insert glued into a stepped hole | resin does not melt |
| never comes apart | adhesive plus a locating feature | [[adhesives-and-solvent-welding]] |

Avoid helicoils in prints: they add nothing over screwing straight into the
plastic. Avoid a nut in a side slot that cuts the load path: it was the weakest
method measured (86 kg).

A printed screw loaded in torsion breaks between layers if printed standing
up. In one rough test a horizontally printed screw took about twice the
torque of the best vertical one ([[printed-threads#orientation]]).
