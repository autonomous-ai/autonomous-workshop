---
title: Battery cells and packs
tags: [battery, cell, aa, aaa, 9v, cr2032, 18650, lithium, capacity, series, parallel]
aliases: [battery sizes, coin cell, button cell, alkaline, li-ion cell, battery pack, power budget]
sources:
  - https://en.wikipedia.org/wiki/List_of_battery_sizes
  - https://learn.adafruit.com/li-ion-and-lipoly-batteries/voltages
  - https://data.energizer.com/pdfs/e92.pdf (AAA alkaline: 150-300 mOhm fresh, capacity against drain, service curves)
related: [lipo-cells-and-housing, toy-battery-compartments, power-path-design, energy-drive, led-sizing]
updated: 2026-10-07
---

# Battery cells and packs

Choose the cell from the load, then design the compartment around the cell
and its holder. The table gives nominal sizes for planning; a holder's own
STEP (`$step-parts`) is what the cavity is cut from.

## Common cells

Nominal dimensions and typical capacities (Wikipedia list of battery sizes):

| cell | diameter × height (mm) | nominal V | typical capacity |
|---|---|---|---|
| AA | 14.5 × 50.5 | 1.5 | 2,700 mAh alkaline |
| AAA | 10.5 × 44.5 | 1.5 | 1,200 mAh alkaline |
| C | 26.2 × 50 | 1.5 | 8,000 mAh alkaline |
| D | 34.2 × 61.5 | 1.5 | 12,000 mAh alkaline |
| 9 V (PP3) | 17.5 × 26.5 × 48.5 (W × L × H) | 9 | 565 mAh alkaline |
| CR2032 | 20 × 3.2 | 3 | 225 mAh lithium |
| CR2025 | 20 × 2.5 | 3 | 160–165 mAh lithium |
| LR44 | 11.6 × 5.4 | 1.5 | 110–150 mAh alkaline |
| 14500 | 14 × 50 | 3.7 | 700–1,500 mAh Li-ion |
| 18650 | 18 × 65 | 3.6–3.7 | 500–4,050 mAh Li-ion |
| 21700 | 21 × 70 | 3.7 | 2,000–6,500 mAh Li-ion |

A 14500 Li-ion cell is AA-sized but 3.7 V. A device whose AA holder accepts
one will see more than twice the voltage it was designed for. Key or label
the compartment for the chemistry it is designed for.

## Voltage over the discharge

Nominal is not what the load sees:

- alkaline starts about 1.5 V per cell and falls steadily through the
  discharge;
- Li-ion / LiPo is 4.2 V full, 3.7 V nominal, 3.4 V effectively empty, and
  must not go below about 3.0 V ([[lipo-cells-and-housing]]);
- a coin cell (CR2032) sags hard under pulse load; it suits microamp sleep
  current and a small indicator, not a motor.

Design the circuit for the whole range, from full to empty. An LED resistor
sized at the full voltage dims as the cells empty ([[led-sizing]]). A motor
slows. A 3.3 V regulator needs its dropout above the empty voltage.

## Series and parallel

- **Series** adds voltage, capacity stays: 3 × AA = 4.5 V nominal, ~2,700 mAh.
- **Parallel** adds capacity, voltage stays. Parallel only identical cells at
  the same charge. Never parallel primary cells with different charge or age,
  and never parallel Li-ion cells without a pack design (balancing,
  protection).
- A 4 × AA pack (6 V nominal) is the classic hobby servo and TT-motor supply
  ([[hobby-servos]], [[small-dc-motors]]).

## Runtime estimate

```text
hours ≈ capacity_mAh / average_current_mA
```

That is an upper bound. Rated capacities are quoted at gentle discharge
rates, and a cell under motor-type current delivers less; take the derating
from the cell's datasheet discharge curve at the real current. Record the
estimate as an open item: no rigid gate measures runtime
([[power-path-design]]).

## An alkaline cell in a model

To run a motor down rather than quote a capacity, model each cell from its
datasheet:

- **open-circuit voltage against depth of discharge**: read the gentlest
  service curve (the AAA E92's 50 mA curve runs 1.50 → 1.33 V at a fifth,
  1.27 at half, 1.20 at two thirds, 1.0 V at 93 %, 0.8 V at the end) and add
  that curve's own current times the resistance;
- **internal resistance**: 150–300 mΩ fresh for an AAA alkaline, rising
  steeply toward the end (model it growing with the cube of the depth);
- **capacity against drain**: the bar chart of service to 0.8 V at a few
  continuous currents (an AAA alkaline: about 1,150 mAh at 25 mA, 940 at
  100 mA, 670 at 250 mA, 430 at 500 mA); depth is charge drawn over the
  capacity at the load's mean current.

The load then sees `E(depth) − I × R(depth)` per cell, and the run ends where
the load's peak demand meets what the motor can give, which on a friction-heavy
mechanism comes before the cells reach 0.8 V.

## Choosing

| need | first choice |
|---|---|
| a small indicator or sensor sleeping most of the time | CR2032 in a holder that a child cannot open ([[toy-battery-compartments]]) |
| a toy motor or servo, replaceable cells | 3–4 × AA |
| rechargeable, flat, light | a protected LiPo pouch with a charger board ([[lipo-cells-and-housing]]) |
| rechargeable, high capacity | a protected 18650 in a proper holder |
