---
title: Sealing and ingress protection
tags: [seal, o-ring, gasket, ip-rating, waterproof, gland, vent, cable-gland]
aliases: [ip code, ip67, ip68, ipx7, iec 60529, ingress protection, waterproof enclosure, watertight print, o-ring groove, gland design, face seal, radial seal, squeeze, gland fill, gasket compression, compression stop, pressure equalisation, breather vent, eptfe membrane, drain hole, labyrinth seal, lip seal]
sources:
  - https://en.wikipedia.org/wiki/IP_code (IEC 60529 digit tables and test conditions)
  - https://raw.githubusercontent.com/gumyr/bd_warehouse/main/src/bd_warehouse/o_rings.py (ORing, static_gland_profile, dynamic_gland_profile, gland_width_for)
  - skills/cad/references/standard-elements.md
  - https://www.globaloring.com/o-ring-groove-design/ (squeeze by series, 60–85 % fill, 5–30 % at tolerance extremes, face-seal ID/OD interference)
  - https://www.marcorubber.com/o-ring-groove-design-considerations.htm/ (squeeze by application, 0–5 % stretch, cross-section loss ≈ half the stretch, finish 16–32 µin static)
  - Parker O-Ring Handbook ORD 5700, ch. 4 static seals, Design Chart 4-2 (22–32 % squeeze for -0XX static, 32 µin finish, 16 µin for gas face seals; via search excerpt)
  - https://www.nedc.com/compression-rates-in-rubber-gaskets/ (solid 10–30 %, sponge 30–50 %)
  - https://blog.prusa3d.com/watertight-3d-printing-pt1-vases-cups-and-other-open-models_48949/ (perimeters by material, layer height, flow, vase mode)
  - https://hackaday.com/2026/05/30/testing-various-ways-to-waterproof-fdm-printed-parts/ (internal epoxy and PU coatings best at ~1 bar)
  - https://www.gremco.de/en/magazin/eptfe-membranes-in-battery-vents/ (ePTFE pores < 1 µm, +50 °C ≈ 180 mbar sealed)
  - https://verchilconnect.com/cable-gland-size-chart/ (cable OD near the middle of the clamping range, one cable per seal)
related: [electronics-enclosure-design, layer-anisotropy, perimeters-infill-and-strength, creep-and-stress-relaxation, fdm-surface-finish, adhesives-and-solvent-welding, food-and-toy-safety, uv-and-outdoor-exposure, fit-derivation, element-libraries, post-processing-and-finishing, fluid-fittings-and-pneumatics]
updated: 2026-09-23
---

# Sealing and ingress protection

A seal is designed from the rating it must meet backwards: pick the IP code,
then the seal type, then derive the groove or clamp from the seal, then check
that the printed walls themselves do not leak. Read this before drawing a lid,
a groove, a cable entry or a "waterproof" claim.

## What the IP code promises

`IP` + solids digit + water digit (IEC 60529). `X` means "not tested", not
"zero". The water digits are **not cumulative**: an IPX7 part has not
necessarily passed IPX5/6 jets, so a product that must survive both is marked
`IPX5/IPX7`.

| digit | solids | digit | water (test) |
|---|---|---|---|
| 1 | > 50 mm (back of hand) | 1 | vertical drips, 10 min |
| 2 | > 12.5 mm (finger) | 2 | drips at 15° tilt |
| 3 | > 2.5 mm (tool) | 3 | spray up to 60°, 10 L/min |
| 4 | > 1 mm (wire) | 4 | splash from any direction |
| 5 | dust-protected (some entry, harmless) | 5 | 6.3 mm jet, 12.5 L/min, 3 m, ≥ 3 min |
| 6 | dust-tight (vacuum test) | 6 | 12.5 mm jet, 100 L/min, ≥ 3 min |
| | | 7 | immersion to 1 m, 30 min |
| | | 8 | beyond 1 m, conditions set by the maker |
| | | 9K | hot high-pressure jets (ISO 20653) |

The solids digit is a geometry check you can make in CAD: an opening that
admits a 12.5 mm sphere fails IP2X, 1 mm fails IP4X. Digits 5 and up, and
every water digit, are tests on a built product; a model can only be
*designed for* them. Record the target as a claim with its open test.

## Pick the seal for the rating

| target | usual seal |
|---|---|
| IPX4 splash | overlapping lip or labyrinth, drain path, no compressed seal |
| IP54–IP65 | flat gasket or cord in a groove, screws or latches along the edge |
| IP67/68 immersion | O-ring in a machined-quality groove, or a potted/bonded joint |
| cable through a wall | a bought cable gland or a potted grommet, never a bare hole |

A **labyrinth** (two or more interleaved lips, a drip edge above every
opening, the joint line facing down) keeps out falling water and dust without
any squeeze. It does nothing against jets aimed into it or immersion.

## O-rings: what the toolchain derives and what it does not

`stdpart` serves ISO 3601 O-rings through `bd_warehouse.o_rings.ORing`, and
the ring also produces its own gland: `static_gland_profile(axial=True)` for a
face seal, `static_gland_profile(axial=False)` for a static radial seal,
`dynamic_gland_profile()` for a moving one, and `gland_width_for(...)`. Take
the groove width, depth and radii from that profile, never from a table typed
into the parameter block ([[element-libraries]],
[[fit-derivation]]). This page holds the *why*, so you can check the profile
against a printed part and choose the ring:

```text
squeeze        s = (CS - H) / CS          CS cross-section, H gland depth
                                           (face: groove depth; radial: groove depth + radial gap)
gland fill     f = (pi/4 CS^2) / (W * H)   W groove width
ID stretch     e = (D_seat - ID) / ID      D_seat groove inner diameter it is stretched onto
```

- **Squeeze**: static face seals about 20–30 %; static radial 18–25 %
  (Parker's static chart runs 22–32 % for the smallest sections, less for large
  ones); reciprocating 10–20 %; rotary 0–10 %. At the tolerance extremes the
  squeeze must stay within about 5–30 %.
- **Fill**: 60–85 % of the groove volume, never 100 %. The ring is
  incompressible; it swells in fluids and expands with heat, and a full groove
  extrudes it or cracks the housing.
- **Stretch**: 0–5 % on the ID. The cross-section thins by about half the
  stretch percentage, which drops squeeze; recompute s with the thinned CS.
- **Face seal and pressure direction**: with pressure from inside, seat the
  ring against the groove's **outer** wall (ring OD up to about 3 % larger than
  the groove OD); with pressure from outside (an immersed housing), against the
  **inner** wall (ring ID up to about 5 % smaller than the groove ID). The
  pressure then pushes the ring onto the wall it already touches instead of
  rolling it across the groove.
- **Surface finish**: static sealing faces about 32 µin Ra (0.8 µm), 16 µin
  (0.4 µm) for gas; dynamic 8–16 µin. No FDM surface is this smooth.

## Printed grooves and faces

FDM misses those finishes by an order of magnitude and its depth tolerance is
a large fraction of a small CS. Consequences:

- Use the **largest cross-section** the part allows (2.62 or 3.53 mm rather
  than 1.78 mm): a 0.15 mm depth error is 8 % squeeze on 1.78 mm and 4 % on
  3.53 mm. Assert the squeeze at both tolerance extremes.
- **Layer lines must run along the seal line, never across it.** A face seal
  on a top (X-Y) face, or a radial seal on a cylinder whose axis is vertical,
  has every layer step parallel to the ring. A radial seal on a horizontal
  bore crosses every layer, and each step is a leak path.
- Seal on a top surface or ironed face ([[fdm-surface-finish]]), not on a
  bed-side face with elephant's foot or a supported face.
- A soft ring hides roughness better: prefer a bought elastomer ring over a
  printed TPU ring. A printed TPU 95A "O-ring" is too hard and
  its own layer seams leak; print TPU as a flat gasket instead.

## Flat gaskets and compression stops

A flat gasket (cut sheet, cord, foam or printed TPU) seals by being squeezed
between two flanges:

- Solid rubber: 10–30 % of its thickness (air about 10–15 %, water 20–30 %).
- Closed-cell sponge: 30–50 % (water about 40–50 %).
- Solid rubber is incompressible, so the groove or flange must leave volume
  for it to bulge into; sponge needs little.
- **Put a hard stop in the joint**: the lid closes metal-to-metal (or
  plastic-to-plastic) on a land, and the gasket thickness minus the stop
  height *is* the compression. Without a stop, screw torque sets the squeeze,
  the printed flange creeps, and the seal loses force over time
  ([[creep-and-stress-relaxation]]).
- A flexible printed flange bows between widely spaced screws and the
  compression drops midway. Space screws closely, stiffen the flange with a
  rib, or clamp with a continuous lip; record the spacing as an open item
  until a leak test passes.
- A seal line runs **inside** the screw circle, so the screw holes are not
  leak paths, or each screw gets its own washer seal.

## Cable entries

A cable gland is a purchased part (`$step-parts`): an M-thread body, a
compressible insert and a dome nut. Choose it so the cable's jacket OD lands
near the **middle** of the clamping range (ranges overlap and differ by vendor,
e.g. M16 is sold as 4–8 or 5–10 mm), one cable per insert. The panel hole and
the nut's seating face come from the vendor file via `cadmount`, and the face
around the hole must be flat and wide enough for the gland's O-ring or washer.

Tube entries, hose barbs and push-fit ports:
[[fluid-fittings-and-pneumatics]].

## Making the printed wall itself watertight

A perfect seal on a porous wall leaks through the wall. Prusa's test on open
vessels found the **number of perimeters** decides it:

| minimum perimeters to hold water | materials |
|---|---|
| 2 | ABS, ASA, CPE, PC, PP |
| 3 | TPEE |
| 4 | PETG, PLA, PA |
| 5 | HIPS, PVB |

- Lower layer height is better (0.05 mm best, 0.3 mm worst; 0.15 mm "quite
  good"). Flow at 105–110 % helps at the cost of accuracy.
- Solid bottom layers mattered less than perimeters.
- One-perimeter vase mode was watertight in every material tested: the
  **seam**, not the layer bond, is the main leak. Align or hide seams away from
  a wetted face ([[fdm-surface-finish#seams]]).
- Under about 1 bar, **internal** epoxy and PU coatings beat external ones and
  survived impact best. Coat the pressure side.
- Acetone vapour smoothing seals ABS/ASA only; it rounds edges and changes
  dimensions, so never smooth a sealing or mating face after the gland was
  sized ([[adhesives-and-solvent-welding]]).
- For anything touching food or drinking water, see [[food-and-toy-safety]].

Which solvent smooths which material, and what the coating does to fits:
[[post-processing-and-finishing]].

## Vents and drains

A sealed box breathes by temperature. Ideal gas at constant volume:

```text
dp = p0 * dT / T0            101.3 kPa * 50 K / 293 K ≈ 17 kPa (≈ 170 mbar)
```

A 50 °C swing gives about 180 mbar; as the box cools it **sucks** water past
any weak seal. A membrane vent (ePTFE, pores < 1 µm; a purchased part) passes
air and blocks liquid, holding the difference to a few mbar. Its water-entry
pressure is finite (hundreds of mbar), so mount it on a vertical or downward
face out of direct jets.

Where water will get in (IPX4-class products, outdoor housings), give it a way
out: a drain hole at the lowest point of every cavity in every mounted
orientation, and electronics raised above the drain level
([[electronics-enclosure-design]]).

## Checks

```python
import math
s = (CS - H) / CS
fill = (math.pi / 4 * CS**2) / (W * H)
stretch = (D_seat - ID) / ID
cs_eff = CS * (1 - stretch / 2)
s_min = (cs_eff - (H + H_tol)) / cs_eff
s_max = (cs_eff - (H - H_tol)) / cs_eff
assert 0.05 <= s_min and s_max <= 0.30, f"squeeze {s_min:.2f}..{s_max:.2f} outside 5-30 %"
assert fill <= 0.85, f"gland fill {fill:.2f} over 85 %"
assert 0 <= stretch <= 0.05, f"ID stretch {stretch:.3f} outside 0-5 %"
comp = (GASKET_T - STOP_GAP) / GASKET_T          # flat gasket set by a hard stop
assert GASKET_MIN <= comp <= GASKET_MAX, "gasket compression not set by the stop"
```
