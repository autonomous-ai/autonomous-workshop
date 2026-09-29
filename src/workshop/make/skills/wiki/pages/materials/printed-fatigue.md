---
title: Fatigue of printed plastics
tags: [fatigue, s-n-curve, endurance, cyclic-load, pla, nylon, asa, pc]
aliases: [fatigue limit, endurance limit, cyclic loading, wohler curve, sn curve, repeated load]
sources:
  - Ezeh, O.H. and Susmel, L. (2019) Fatigue strength of additively manufactured polylactide (PLA) - effect of raster angle and non-zero mean stresses. International Journal of Fatigue 126, 319-326, https://eprints.whiterose.ac.uk/id/eprint/146276/
  - Mechanical, Fatigue, and Thermal Characterization of ASA, Nylon 12, PC, and PC-ABS Manufactured by Fused Filament Fabrication (FFF), https://pmc.ncbi.nlm.nih.gov/articles/PMC12845617/
related: [layer-anisotropy, creep-and-stress-relaxation, flexure-materials-and-snap-strain, filament-properties, gears]
updated: 2026-09-23
---

# Fatigue of printed plastics

A part that flexes, clicks, or carries a load that comes and goes fails far
below its static strength. For printed plastics the cracks start at filament
boundaries and layer welds.

## A design curve for printed PLA

Ezeh & Susmel (2019) re-analysed their own and published fatigue data for PLA
printed flat on the bed and proposed a unifying design curve for a probability
of survival of at least 90 %:

```text
negative inverse slope        k = 5.5
endurance limit at N = 2·10^6 cycles:  σ_max = 0.1 · σ_UTS
σ_max(N) = 0.1 · σ_UTS · (2e6 / N)^(1/5.5)
```

Their conclusions, for PLA printed flat:

- Cracking follows three mechanisms: cracking of the filaments, debonding
  between adjacent filaments, and debonding between adjacent layers.
- **Raster angle can be neglected** with little loss of accuracy: for fatigue
  design a flat PLA print can be treated as homogeneous and isotropic.
- **A static mean stress is handled by using the maximum stress of the cycle**
  (σ_max), not the amplitude.

```python
UTS = 52.3                     # MPa, X-Y, from the filament datasheet
def pla_fatigue_max_stress(n_cycles):
    return 0.1 * UTS * (2e6 / n_cycles) ** (1 / 5.5)
assert sigma_max_in_cycle <= pla_fatigue_max_stress(N_DESIGN)
```

At 2·10⁶ cycles that is about 5 MPa for a 52 MPa PLA. Every clip, flexure
and spring made of PLA that must survive millions of cycles has to stay
below this. At 10⁴ cycles the curve allows about 2.6 × more.

The curve is for unnotched specimens. The authors list notch effects and
infill level as open questions, so a sharp corner in a real part sits below
the curve.

## Other materials, one test

FFF specimens, load controlled, R = 0.05, 10 Hz, staircase method, run-out at
10⁶ cycles:

| material | UTS MPa | fatigue limit (stress range at 10⁶) MPa |
|---|---|---|
| ASA | 31.7 | 8.0 |
| PC | 57.1 | 3.6 |
| Nylon 12 | 37.0 | 7.4 |
| PC-ABS | 31.4 | 4.7 |

- **Nylon 12 was the most fatigue-resistant**; ranking by endurance was
  Nylon 12 > ASA ≈ PC-ABS >> PC.
- **PC has the highest static strength but the lowest fatigue limit here**,
  under 10 % of its UTS. A strong datasheet number says nothing about cyclic
  life.
- Micro-CT porosity: ASA 8.2 %, PC 11.2 %, Nylon 12 4.2 %, PC-ABS 8.0 %.
  Porosity is where fatigue cracks start, so print settings that close voids
  matter more for cyclic parts than for static ones.

## Design rules

- **Cyclic stress limit:** without material-specific data, take about 10 %
  of the X-Y UTS as the long-life maximum stress for PLA; for other materials
  use the measured table or test a coupon.
- **Choose nylon for parts that flex millions of times** (hinges, clips,
  springs); avoid PLA there, and do not choose PC for its static strength.
- **Remove notches:** fillet the root of every beam, boss and tooth; a notch
  is where the three crack mechanisms start.
- **Keep cyclic stress in the layer plane** ([[layer-anisotropy]]); layer
  debonding is one of the failure mechanisms.
- **Record the cycle count** a moving part must survive; no gate here checks
  fatigue.
