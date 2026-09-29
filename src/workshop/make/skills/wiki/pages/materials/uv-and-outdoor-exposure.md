---
title: UV and outdoor exposure
tags: [uv, outdoor, weathering, aging, asa, petg, pla, abs]
aliases: [sunlight, weather resistance, uv resistance, outdoor parts, aging, weathering]
sources:
  - Accelerated Aging Effect on Mechanical Properties of Common 3D-Printing Polymers, Polymers 2021, https://pmc.ncbi.nlm.nih.gov/articles/PMC8659210/
  - Analysis of the Mechanical Properties of 3D-Printed Plastic Samples Subjected to Selected Degradation Effects, Materials 2023, 16(8) 3268, https://pmc.ncbi.nlm.nih.gov/articles/PMC10146359/
related: [moisture-and-drying, heat-resistance-of-printed-parts, creep-and-stress-relaxation, filament-properties, sealing-and-ingress-protection]
updated: 2026-09-23
---

# UV and outdoor exposure

Outdoors a part gets UV, heat, water and temperature cycles together. The
published printed-part data is short-term and disagrees on PETG, so this page
gives what was measured and a conservative choice.

## Two studies, different answers for PETG

**Accelerated UV-B (Polymers 2021).** PLA and PETG printed at 100 % infill;
UV-B at 310 nm, 0.43 W m⁻² nm⁻¹ for 24 h in cycles of 8 h dry at 50 °C and
4 h condensation at 23 °C. The authors equate this to several months
outdoors.

| property change | PLA | PETG |
|---|---|---|
| tensile strength | −5.3 % | −36 % |
| compressive strength | −6.3 % | −38.3 % |
| Young's modulus | not significant | not significant |
| elongation at break | 1.68 → 1.43 % | 3.06 → 1.36 % |

Stiffness did not change; strength and ductility did, and creep worsened in
proportion to the strength loss.

**Mixed degradation (Materials 2023).** PLA, PETG, ABS and ASA from three
makers each: 20 h and 100 h under a 125 W mercury lamp, 100 h condensation at
55 °C and 100 % humidity, 130 freeze cycles from −18 to 21 °C, 100 h at 60 °C,
and 98 days outdoors.

- PETG showed **no decrease** in ultimate tensile strength for any factor.
- ASA had the most stable properties of all, at lower absolute strength
  (reference about 45 MPa).
- ABS had the lowest values and decreased under every factor.
- PLA degraded most in humid conditions (about −28 % after the condensation
  chamber).
- Overall the authors found no fundamental effect on short-term mechanical
  properties at these exposures.

The PETG results differ by source, dose and filament, and the first study's
authors themselves recommend in-house testing before outdoor functional use.

## Choosing a material for outdoor parts

- **ASA** was the most stable in the multi-factor study, and is the usual
  outdoor choice; its HDT (about 100 °C) also covers sun heating
  ([[heat-resistance-of-printed-parts]]).
- **PETG** may lose a third of its strength under strong UV. Size it with
  that loss or keep it shaded.
- **PLA** loses strength in warm humid conditions and softens around 55–60 °C;
  avoid it for loaded outdoor parts.
- **ABS** weakened under every factor tested.
- Dark colours in sun run hotter; stiffness is the property least affected,
  strength and elongation the most.

```python
OUTDOOR_STRENGTH_KNOCKDOWN = {"PETG": 0.64, "PLA": 0.72}  # worst measured retention above
```

Keeping water out, and letting it drain: [[sealing-and-ingress-protection]].

## Open items

UV dose, pigment, wall thickness (UV damage is a surface effect) and years of
exposure are not covered by these short tests. Record outdoor service as an
open item with the material and the expected exposure.
