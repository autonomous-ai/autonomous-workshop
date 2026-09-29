---
title: Thermal design for enclosures
tags: [thermal, heat, enclosure, ventilation, heatsink, junction-temperature, fan, regulator]
aliases: [heat budget, power dissipation, theta ja, rθja, thermal resistance, vent sizing, chimney effect, stack effect, cooling fan cfm, thermal pad, gap pad, box temperature rise, overheating]
sources:
  - https://www.ti.com/lit/ds/symlink/lm1117.pdf (LM1117 datasheet SNOS412Q, §7.4 thermal information, §9 PD equation and Table 9-2 RθJA vs copper area)
  - https://www.ti.com/lit/ds/symlink/drv8833.pdf (DRV8833 datasheet SLVSAR1E, §6.4 thermal information, §10.4 power dissipation)
  - https://library.automationdirect.com/selecting-enclosure-fan-air-conditioner/ (surface-area heat transfer 1.25 metal / 0.62 plastic BTU/h·ft²·°F; CFM = 3.17 P / ΔT°F)
  - https://en.wikipedia.org/wiki/TO-220 (TO-220 junction-to-air 50–70 °C/W, junction 2–5 °C above a heatsinked tab at 1 W)
  - https://www.modusadvanced.com/resources/blog/thermal-gap-pad-compression-optimizing-performance-through-proper-selection-and-application (gap pad 1–8 W/m·K silicone, 20–40 % compression)
  - https://batteryuniversity.com/article/bu-410-charging-at-high-and-low-temperatures (Li-ion charge 0–45 °C, discharge −20–60 °C)
  - https://www.electronics-cooling.com/1997/09/a-practical-formula-for-air-cooled-boards-in-ventilated-enclosures/ (lower-vent inlet, upper-vent outlet; chimney height between vent centrelines)
  - ASHRAE Handbook — Fundamentals, ch. 16 Ventilation and Infiltration (stack-driven flow through openings, discharge coefficient)
related: [electronics-enclosure-design, heat-resistance-of-printed-parts, lipo-cells-and-housing, motor-drivers-and-flyback, led-sizing, power-path-design, stepper-motors, noise-and-vibration]
updated: 2026-09-23
---

# Thermal design for enclosures

Heat is a budget with three stages: each part's watts raise its junction
above the air inside the box, and the box raises that air above the room.
A printed box is an insulator, so the second stage is larger than it looks,
and PLA or PETG walls soften at temperatures a regulator reaches easily.
Read this page when a design has a linear regulator, a motor driver, a power
LED, a charger or a sealed box. The short rules are in
[[electronics-enclosure-design#heat-and-ventilation]].

## The power budget

List every part that turns electrical power into heat, at the worst-case
input voltage and load:

```text
linear regulator   P = (Vin − Vout) · Iload + Vin · Iq        (LM1117 eq. 3; Iq is small)
H-bridge (DC)      P = I_rms² · (R_HS + R_LS)  × 1.1–1.3      (DRV8833 §10.4: switching adds 10–30 %)
LED + resistor     P = Vsupply · I_led                        (count it all as heat: conservative)
resistor           P = I² · R
switching regulator P = Pout · (1/η − 1)                      (η from its datasheet at that load)
```

A linear regulator's loss grows with the voltage it drops, not with what it
delivers: 5 V → 3.3 V at 0.5 A burns 0.85 W, a third of the 2.5 W drawn
from the supply. From a 2S pack (up to 8.4 V) the same load burns
2.55 W. When `(Vin − Vout) · I` passes about a watt, choose a buck
converter ([[power-path-design]]). Motor current is the stall current for as
long as the mechanism can stall ([[motor-drivers-and-flyback]]).
`R_DS(on)` rises with temperature, so the driver's loss grows as it heats.

## Junction temperature from θJA

```text
T_J = T_box + P · RθJA          RθJA in °C/W (= K/W)
P_max = (T_Jmax − T_box) / RθJA
```

`T_box` is the air **inside** the enclosure, not the room (next section).
`T_Jmax` is the recommended operating limit, typically 125 °C; the absolute
150 °C figure is not a design point.

RθJA is not a property of the package alone. The datasheet value is for a
JEDEC test board; on a real board it is set by the copper under the tab.
LM1117 (TI, Table 9-2), top-side 1 oz copper:

| copper under the tab | SOT-223 RθJA | TO-252 RθJA |
|---|---|---|
| 0.0123 in² (8 mm², pad only) | 136 °C/W | 103 °C/W |
| 0.3 in² (194 mm²) | 84 °C/W | 60 °C/W |
| 1 in² (645 mm²) | 66 °C/W | 47 °C/W |

The same datasheet gives 23.8 °C/W for TO-220 on the JEDEC board; a free-air
TO-220 with no board copper or heatsink is about 50–70 °C/W. DRV8833:
40.5 °C/W in the exposed-pad HTSSOP, 103 °C/W in the plain TSSOP. Read the
board you are buying (breakout boards seldom state copper area) as the pad-only
row until a measurement says otherwise.

Worked example: 0.85 W in a SOT-223 on a breakout with little copper,
box air 45 °C → `T_J = 45 + 0.85 · 136 = 161 °C`: thermal shutdown. With
645 mm² of copper → `45 + 0.85 · 66 = 101 °C`: acceptable.

## Box air rise from surface area

A closed box sheds heat from its outer surface by natural convection and
radiation:

```text
ΔT_box = P_total / (h · A_surface)
h ≈ 7.1 W/m²·K  unpainted metal box    (1.25 BTU/h·ft²·°F)
h ≈ 3.5 W/m²·K  plastic box            (0.62 BTU/h·ft²·°F)
A_surface = 2 (L·W + L·H + W·H), minus faces against a wall or table
```

The coefficients are the industrial enclosure constants
(AutomationDirect); for a small printed box treat them as a first estimate
good to perhaps ±50 %. Worked example: a 100 × 60 × 40 mm plastic box has
0.0248 m² of surface, so 1 W raises its air about `1 / (3.5 · 0.0248) ≈ 12 K`.
A sealed pocket-sized printed box holds about 1 W for a 10–15 K rise; beyond
that it needs vents, a fan or a metal path to the outside.

## Vents: inlet low, outlet high

Warm air rises, so a vent pair works as a chimney: inlet near the bottom,
outlet near the top, on the far side from the inlet so the air crosses the
hot parts. Put the hottest part low and near the inlet (the chimney height
above it is what drives the flow). Stack-driven flow (ASHRAE Fundamentals,
ch. 16):

```text
Q = Cd · A_eff · sqrt(2 g h ΔT / T_in)       m³/s, T in kelvin
P_air = ρ cp · Q · ΔT                        ρ cp ≈ 1206 J/m³·K at 20 °C
1/A_eff² = 1/A_in² + 1/A_out²                equal vents: A_eff = A / √2
Cd ≈ 0.6–0.65 for a sharp-edged opening
h  = height between inlet and outlet centrelines
```

Worked example: 5 W to remove by air at `ΔT = 20 K`, `h = 0.05 m`,
`T = 300 K`, `Cd = 0.6` → velocity term 0.256 m/s, `Q = 2.07e-4 m³/s`,
`A_eff ≈ 13.5 cm²`, so each vent needs about 19 cm² of **free** area.
Doubling the chimney height to 0.1 m cuts the area by √2. The lesson for a
small toy or gadget: vents that are a few slots help less than they look,
and a tall internal path helps more than more slots.

- **Free area** is the open area of the slots only, not the grille outline.
  Bars, a finger guard or a mesh cut it sharply.
- Keep inlet and outlet about equal; a small outlet chokes a big inlet.
- Slots sized to keep fingers out of a toy: [[toy-safety-constraints]].
- Vents on the underside need feet that lift the box off the table.

## Fans: airflow from power and ΔT

```text
Q [m³/h] = 2.98 · P [W] / ΔT [K]
Q [CFM]  = 1.76 · P [W] / ΔT [K]     = 3.17 · P / ΔT[°F]  (AutomationDirect)
```

`ΔT` is outlet air minus inlet air. 10 W at a 10 K rise needs about 3 m³/h
(1.8 CFM). A fan's catalogue airflow is at zero back-pressure; slots, filters
and a crowded board cut it, so read the operating point off the fan's
pressure–flow curve or keep a margin of two. Blow in low, exhaust high, in
the same direction as convection, and give the fan an intake gap of at least
its frame depth.

Fan noise against size and speed: [[noise-and-vibration]].

## Heatsinks and thermal pads

```text
RθJA = RθJC + RθCS + RθSA      junction–case, case–sink, sink–ambient
R_pad = t / (k · A)            t thickness (m), k W/m·K, A contact area (m²)
```

- Silicone gap pads run about 1–8 W/m·K and want 20–40 % compression. A
  1 mm pad at k = 3 over 10 × 10 mm is `0.001 / (3 · 1e-4) = 3.3 K/W`. Design
  the gap from the pad's compressed thickness, set by rigid features, never
  by the pad.
- A heatsinked TO-220 at 1 W sits only 2–5 °C below its junction; the tab
  and the sink are as hot as the part.
- A heatsink inside a sealed printed box only moves heat into the box air.
  To leave, the heat needs vents, a fan, or the sink through the wall.
- A printed wall is not a heat spreader: plastics conduct heat orders of
  magnitude worse than aluminium. Do not press a regulator onto the wall to
  cool it.

## Keeping printed parts below softening

The part surface a hot component touches runs near its case temperature.
Apply the HDT margin from [[heat-resistance-of-printed-parts#design-rule]]
to that surface, not to the room:

- PLA (HDT about 55–60 °C) holds its shape only below about 35–40 °C with a
  20 K margin: do not let a regulator tab, a motor can, a power LED or a
  heatsink touch PLA. Leave an air gap of a few millimetres, or use PETG,
  ABS, ASA or PC for the bracket that carries a hot part.
- A standoff under a board with a hot part is loaded (screw preload) and
  warm: it creeps first ([[creep-and-stress-relaxation]]).
- Motors and steppers run hot at their case: [[stepper-motors]].

## Batteries while charging

Li-ion and LiPo charge only between 0 and 45 °C (Battery University; many
chargers stop at 50 °C) and discharge between −20 and 60 °C. The charger IC
and the cell share the box air, and a linear charger dissipates
`(Vin − Vcell) · Icharge` (5 V → 3.7 V at 0.5 A: 0.65 W). Keep the cell away
from the charger, the regulator and the motor driver, and check the box air
rise at full charge current against 45 °C ([[lipo-cells-and-housing]]).

## Checks

```python
T_room_max = 35.0                                   # °C, stated in the spec
A_surf = 2 * (L*W + L*H + W*H)                      # m², faces exposed to air
dT_box = P_total / (3.5 * A_surf)                   # plastic box, sealed
T_box = T_room_max + dT_box
assert (Vin_max - Vout) * I_load * Rtheta_ja + T_box <= 125.0, "regulator junction over 125 °C"
assert T_box <= 45.0 or not charging_inside, "Li-ion charged above 45 °C"
assert T_hot_contact <= HDT_045[MATERIAL] - 20, f"{MATERIAL} bracket softens against a hot part"
assert abs(A_vent_in / A_vent_out - 1) <= 0.25, "unbalanced vent pair"
```
