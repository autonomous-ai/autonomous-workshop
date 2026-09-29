---
title: Heat-set threaded inserts
tags: [insert, heat-set, threaded-insert, boss, brass, pull-out, torque-out, jack-out]
aliases: [heat staking insert, ultrasonic insert, brass insert, threaded bushing, knurled insert, ruthex, cnc kitchen insert]
sources:
  - https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts (temperatures, installation, depth, straight holes)
  - https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong (M3 hole size tests, 4.6 mm knurl, 1400 N, hole shrinkage)
  - https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive (insert quality pull-out and torque tests)
  - https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment (insert vs screw vs nut)
  - PennEngineering SI® Threaded Inserts for Plastics datasheet, pp. SI-6, SI-25, SI-26 (https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/sidata.pdf)
  - https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m2-m3-m4-m5-sortimentskasten-70-100-50-50-stuck (Ruthex insert lengths)
  - https://www.ruthex.de/en/products/ruthex-hss-bohrer-set-5-tlg-fur-gewindeeinsatze-m2-m2-5-m3-m4-m5-m6-din-338-bohrer-3-2-4-0-5-6-6-4-8-0-mm-fur-kunststoff-stahl-alu-kupfer-messing-uvm (Ruthex drill sizes)
  - https://tools.creative3dp.com/blog/heat-set-insert-hole-size-chart/ (community hole and wall table)
  - https://insertguide.com/guides/heat-set-insert-hole-size/ (community hole table, depth rule)
related: [screws-into-plastic, nut-traps-and-captive-nuts, fastener-torque-and-stripping, metric-screw-clearance-holes, wall-thickness-and-hollowing, printed-threads-and-bosses, resin-printing-design]
updated: 2026-09-23
---

# Heat-set threaded inserts

A brass insert melted into a printed hole gives a metal thread that survives
repeated assembly. It is the default for any printed joint opened more than a
few times ([[fastener-torque-and-stripping#choosing-a-threaded-joint]]).

Resin parts are too brittle for heat-set inserts: [[resin-printing-design]].

## The hole is sized from the insert, not the thread

There is no universal "M3 insert hole": the hole depends on the insert's pilot
and knurl diameter. Use the vendor's number for the insert actually bought.

| insert | Ruthex / CNC Kitchen hole | community CAD pocket (PLA) | PEM IUT hole (moulded) | PEM min hole depth (short / long) |
|---|---|---|---|---|
| M2 | 3.2 | 3.1–3.43 | 3.23 | 3.94 / 4.76 |
| M2.5 | 3.6 | 3.8–3.84 | 4.01 | 6.5 |
| M3 | 4.0 | 4.2–4.24 | 4.01 | 4.19 / 6.5 |
| M4 | 5.6 | 5.6–5.83 | 5.67 | 5.46 / 8.91 |
| M5 | 6.4 | 6.63–6.8 | 6.43 | 6.48 / 10.28 |
| M6 | 8.0 | 8.2–8.23 | 8.03 | 8.38 / 13.46 |
| M8 | 10.0 | 10.23 | 9.6 | 13.46 |

The vendor column is the Ruthex / CNC Kitchen hole as tabulated by
Creative3DP; it matches Ruthex's insert drill set (3.2, 4.0, 5.6, 6.4 and
8.0 mm for M2 to M6). Ruthex sells inserts M2 × 4, M3 × 5.7, M4 × 8.1 and
M5 × 9.5 mm. CNC Kitchen's M3 inserts
(3.0 mm short and 5.7 mm standard) both take a 4.0 mm hole; the M3 knurl is
4.6 mm across. PEM holes are for moulded or drilled plastic; PEM's minimum
hole depth is the insert length plus 0.76 mm.

**A printed hole is not the nominal hole.** CNC Kitchen measured printed M3
holes about 0.25 mm smaller than modelled and recommends adding 0.2–0.3 mm in
CAD: model 4.2 mm for a 4.0 mm datasheet hole. At a printed 4.2 mm the M3
insert kept about 90 % of its pull-out strength, around 1400 N. The community
tables above already include that allowance; the vendor column does not.

## Depth, shape and walls

- **Depth:** a blind hole about 1 mm deeper than the insert (CNC Kitchen);
  PEM: insert length + 0.76 mm; InsertGuide: insert length + two thread
  pitches. The extra room takes the plastic the knurl displaces.
- **Shape:** straight rather than tapered for printed parts, normally with no
  chamfer at the edge (CNC Kitchen). Some community guides call a 1 × 45°
  entry chamfer mandatory; the sources disagree, so test both on the insert
  used.
- **Boss:** PEM's hole preparation guideline is a boss diameter of 2 × the
  insert diameter; thinner bosses work but lower performance. Community
  minimum walls around the pocket: 1.5 mm (M3), 2.0 mm (M4), 2.5 mm (M5 and
  up), and pockets at least 2 × pocket diameter apart centre to centre.

```python
assert boss_od >= 2 * insert_od, "PEM: boss ≥ 2 × insert diameter"
assert hole_depth >= insert_len + 0.76, "no room for displaced plastic"
```

## Installing

- Soldering iron about 10–20 °C above the print temperature: PLA about
  225 °C, PETG 245 °C, ABS 265 °C.
- Melt the insert in only about 90 % of the way with the iron. Push the rest
  flush with a flat tool and hold it a few seconds until the plastic sets.
- Seat it flush or no more than 0.13 mm proud. Below the surface it jacks
  out; above it, it underperforms (PEM).
- Resin (SLA) prints don't melt: glue the insert into a stepped hole with thick
  CA or two-part epoxy.

## The mating part carries the load

The clearance hole in the part being clamped must be larger than the screw but
smaller than the insert's face diameter. Then the insert, not the host plastic,
takes the clamp load. If the clearance hole must be oversized for alignment,
use a flanged insert. Otherwise the screw pulls the insert out through the
mating part ("jack-out", PEM).

## What the tests show

M3, PETG, 4 perimeters, 100 % infill (CNC Kitchen):

| method | pull-out | torque-out |
|---|---|---|
| heat-set insert | 119 kg | 3 Nm (insert turned in the plastic) |
| screw directly into plastic | 118 kg | 1 Nm (plastic thread sheared) |
| helicoil | 120 kg | 1 Nm |
| nut in side pocket | 86 kg | 2 Nm |
| nut in bottom pocket | 166 kg | 2 Nm |

A separate M3 comparison of insert quality gave 181 kg pull-out for Ruthex
(4.0 mm hole), 157 kg for eBay inserts (4.1 mm hole), 39 kg for cheap inserts
made for injection moulding (4.5 mm hole), and 142 kg for a screw straight into
a 2.7 mm hole. All three inserts held 3–4 Nm before the screw head sheared;
the direct screw failed at about 1 Nm. The insert's advantage is torque and
reuse, not pull-out.
