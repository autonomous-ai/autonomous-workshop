---
title: LiPo and Li-ion cells in a printed housing
tags: [lipo, li-ion, battery, protection, swelling, charging, safety, pouch]
aliases: [lithium polymer, lipoly, pouch cell, battery swelling, protection circuit, jst ph battery]
sources:
  - https://learn.adafruit.com/li-ion-and-lipoly-batteries/voltages
  - https://learn.adafruit.com/li-ion-and-lipoly-batteries/protection-circuitry
  - https://learn.adafruit.com/li-ion-and-lipoly-batteries/conclusion
  - https://www.adafruit.com/product/1578
  - https://www.hanery.com/blog/decoding-li-po-battery-model-numbers-and-labeling-standards/
  - https://www.ufinebattery.com/blog/lithium-ion-cell-sizes-a-comprehensive-guide/
related: [battery-cells-and-packs, toy-battery-compartments, wire-gauge-and-connectors, electronics-enclosure-design, thermal-design-for-enclosures]
updated: 2026-09-23
---

# LiPo and Li-ion cells in a printed housing

A lithium cell stores enough energy to start a fire. The housing's job is to
give it room, keep it from being crushed or punctured, and let its
protection and charger do theirs.

## Voltages

Most common chemistry (Adafruit):

| state | voltage |
|---|---|
| full | 4.2 V |
| nominal | 3.7 V |
| effectively dead | 3.4 V |
| minimum safe | ~3.0 V (protection cut-off) |

Older 3.6/4.1 V cells and newer 4.35 V cells exist. A charger for the wrong
one damages the cell or starts a fire: match the charger to the cell.

## Protection and charging

- A protection circuit cuts off over-charge (above ~4.2 V), over-discharge
  (below ~3.0 V) and excess current (discharge above about 1–2 C). A
  protected pouch cell carries it as a small board taped at the tab end. A
  cell with no visible board is a raw cell and is **not protected**.
- Charge with a CC/CV lithium charger (constant current, then constant
  voltage) only. NiMH, NiCd or lead-acid chargers damage it.
- Charge current up to about 1 C (Adafruit's 500 mAh cell: 100–500 mA).
  Charge only between about 0 and 50 °C. Above 0.5 C, or outdoors, use a
  charger with temperature sensing.
- Do not strike, crush, puncture, bend or disassemble the cell, and do not
  solder to its terminals. Stop using a cell that smells, heats, discolours
  or deforms.

Cell datasheets differ on the upper charge limit (Battery University gives
0–45 °C); design the box to the lower figure unless the cell's datasheet says
otherwise: [[thermal-design-for-enclosures]].

## The connector trap

Adafruit ships its LiPo cells on a 2-pin JST-PH. Other brands use the same
connector with **reversed polarity**, and plugging one into a board wired
the other way destroys the board or the cell. Check the polarity against the
board before a cell goes in, and note it in the spec
([[wire-gauge-and-connectors]]).

## Reading a pouch size

Pouch cells are commonly named TTWWLL: thickness in tenths of a millimetre,
then width and length in millimetres. For example, 503450 ≈ 5.0 × 34 × 50 mm
and 603048 = 6.0 × 30 × 48 mm. Makers vary the digit count and order: confirm
against the maker's drawing. Example of a real part: Adafruit's 3.7 V
500 mAh cell is 29 × 36 × 4.75 mm, 10.5 g, on a 102 mm JST-PH lead.

## Room to give the cell

From a cell maker's OEM housing guidance (Hanery):

| direction | allowance over nominal |
|---|---|
| width | +1 mm (sealed side folds) |
| length | +2 mm (tab exit) |
| thickness | +10 % (a 5.0 mm cell can reach 5.5 mm after ~500 cycles) |

"A tight fit can lead to mechanical pressure on the cell, causing internal
shorts." Never clamp a pouch. Hold it with a pocket and a light strap or foam,
with no sharp printed edges or screw tips facing it. Route the leads so
closing the lid cannot pinch them.

```python
POCKET_W = CELL_W + 1.0      # sealed side folds
POCKET_L = CELL_L + 2.0      # tab exit
POCKET_T = CELL_T * 1.10     # swelling over the cell's life
```

## Cylindrical Li-ion (18650 and friends)

Treat it as a cell that needs a holder, a protection board (or a protected
cell, which is longer than the bare 65 mm), and a charger. A holder's STEP
gives the cavity. Never seat bare cells in printed plastic with loose wire
contacts.

## In a toy

A rechargeable lithium cell in a children's product brings extra
requirements (battery-compartment access, charging circuit, marking) under
toy safety standards; see [[toy-battery-compartments]].
