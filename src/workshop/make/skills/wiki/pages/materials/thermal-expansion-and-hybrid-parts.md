---
title: Thermal expansion and plastic-metal hybrid parts
tags: [thermal-expansion, cte, hybrid, press-fit, slotted-hole, adhesive, metal-insert, temperature]
aliases: [coefficient of thermal expansion, clte, linear expansion, expansion mismatch, plastic on aluminium, plastic on metal, differential expansion, expansion slot, floating mount, bondline thickness]
sources:
  - https://www.engineeringtoolbox.com/linear-expansion-coefficients-d_95.html (bulk plastics and metals, 10⁻⁶/°C near 25 °C)
  - Covestro, Engineering Polymers Joining Techniques design guide (https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1557217197.pdf), pp. 12–15 and 22 (σ = (αp − αm)·Ep·ΔT, slotted holes, do not clamp tight, CLTE table, moulded-in inserts)
  - Stratasys ASA material data sheet (https://www.stratasys.com/siteassets/materials/materials-catalog/fdm-materials/asa/mds_fdm_asa_0921a.pdf), CTE 88 flow / 83 xflow µm/(m·°C), ASTM E831; via search excerpt
  - Kousiatza et al., Characterization of Thermal Expansion Coefficient of 3D Printing Polymeric Materials Using Fiber Bragg Grating Sensors, Materials 2024, 17(18) 4668 (PMC11433601), Table 2 (printed PLA, ABS, PA, CF-PA, PEBA)
  - Effects of Fiber Orientation on the CTE of Fiber-Filled Polymer Systems in Large Format Polymer Extrusion-Based AM, Polymers 2022 (PMC9031978), Tables 6–8 (neat ABS, PC, PETG at 30 °C; CTE jump above Tg)
  - Effects of CTE and Moisture Absorption on the Dimensional Accuracy of Carbon-Reinforced 3D Printed Parts, Polymers 2021 (PMC8587952), Table 2 (Onyx and unfilled nylon, flow vs cross-flow vs Z)
  - https://permabond.com/tech-tips-bonding-dissimilar-materials-industrial-adhesives/ (glue line 0.25–0.3 mm, toughened/flexible adhesive, cure at service temperature)
related: [creep-and-stress-relaxation, dowel-pins-and-press-fits, heat-set-inserts, adhesives-and-solvent-welding, heat-resistance-of-printed-parts, filament-properties, moisture-and-drying, annealing-printed-parts, fit-derivation]
updated: 2026-09-23
---

# Thermal expansion and plastic-metal hybrid parts

Printed plastics expand 3–10 times more per kelvin than steel or aluminium.
A plastic part held to a metal one at two points, or a metal pin pressed into
a plastic bore, is strained by every temperature change. Read this page when a
printed part meets metal (rail, frame, pin, shaft, insert, glued plate) over
a span or a temperature range that is not trivial. A fit derived at room
temperature ([[fit-derivation]]) is only valid at room temperature.

## Coefficients

Linear CTE α in µm/(m·K) = 10⁻⁶/K, below the glass transition. Printed
values differ from bulk ones and depend on raster direction; use the range.

| material | α, µm/(m·K) | source / note |
|---|---|---|
| PLA, printed | 96–102 | FBG study, 25–50 °C, both rasters, plus its cited TMA values |
| PETG | 59–65 | neat printed PETG 65 at 30 °C (LFAM study); bulk PET 59.4 (Engineering ToolBox) |
| ABS | 72–115 | printed 86–89 (FBG), cited 90–115; neat 82 (LFAM); bulk 72–108 |
| ASA | 83–88 | Stratasys: 88 along the road, 83 across |
| PC | 62–70 | neat printed 62 (LFAM); bulk 65–70; Makrolon 70 (Covestro) |
| nylon, unfilled, printed | 114–175 | FBG PA 118–119; Markforged unfilled nylon 114–175 by orientation; bulk nylon 50–90 |
| nylon + chopped carbon | 14–22 along the road, 86–95 across, up to ~250 in Z | FBG CF-PA; Markforged Onyx |
| POM / PP / PTFE (bulk) | 85–110 / 72–90 / 112–135 | Engineering ToolBox |
| epoxy, unfilled | 45–65 | Engineering ToolBox |
| carbon steel | 11–14 | Engineering ToolBox 10.8–12.5; Covestro 14 |
| stainless 304 | 17.3 | Engineering ToolBox |
| aluminium | 23 | Engineering ToolBox, Covestro |
| brass | 17–19 | Engineering ToolBox 18–19; Covestro 17 |
| copper | 16–16.7 | Engineering ToolBox |
| glass | 9 | Engineering ToolBox |

- Fibre-filled filaments are strongly anisotropic: low along the road,
  near-neat across it and highest in Z. Do not use the flow-direction number
  for a dimension that runs across roads or up the layers
  ([[layer-anisotropy]]).
- **Near and above Tg the linear model fails.** The LFAM study measured
  neat ABS, PC and PETG jumping to hundreds of µm/(m·K) (and changing sign)
  approaching Tg, as frozen-in print strain releases. Printed parts also
  shrink irreversibly on their first heating; the FBG study discarded the
  first thermal cycle as unreliable. A part heated near its Tg once is a
  different size: [[annealing-printed-parts#dimensions-change-and-not-uniformly]].
- Nylon also swells with absorbed water, often by more than a service
  temperature change moves it ([[moisture-and-drying#nylon-is-a-different-material-wet]]).

## The mismatch formula

```text
free length change     ΔL = α · L · ΔT
relative change        ΔL_rel = (α_p − α_m) · L · ΔT     plastic vs metal over span L
diametral change       Δc = (α_p − α_m) · d · ΔT          clearance/interference of a metal pin in a plastic bore
restrained stress      σ ≈ (α_p − α_m) · E_p · ΔT          plastic held rigidly to metal (Covestro)
```

ΔT is measured from the **assembly temperature**, in both directions. Take the
service range (cold car, hot car, sun, motor) and check both ends. `E_p` is the
plastic's modulus at that temperature; it falls as the part warms
([[filament-properties]]).

## Worked example: steel pin in a PLA bore, 20 → 50 °C

Ø5 steel pin, PLA bore, α_PLA ≈ 96, α_steel ≈ 12:

```text
Δc = (96 − 12)e-6 · 5 mm · 30 K = 0.013 mm   bore grows more than the pin
```

- A **running fit** gains 0.013 mm. That is far below FDM hole scatter
  (0.1–0.3 mm undersize, [[dowel-pins-and-press-fits#the-fdm-fit-ladder]]),
  so thermal expansion is not what decides a small printed clearance.
- A **press fit** of −0.10 mm loses about 13 % of its interference at 50 °C.
  At 50 °C PLA is within a few kelvin of its HDT
  ([[heat-resistance-of-printed-parts#temperatures-per-material]]), so the
  bore also creeps open under the remaining hoop stress. When it cools, the
  relaxed bore is bigger than it was. **Heat plus creep, not expansion
  alone, is what loosens small press fits.**
- Cold goes the other way: from 20 to −20 °C the interference grows by
  0.017 mm on Ø5. The hoop strain at the bore is roughly `interference / d`, so
  the cold adds about 0.34 % to a bore already strained 2 % by a −0.10 mm fit.
  That is the cracking case for brittle PLA and PETG.

## Worked example: long printed part on an aluminium rail

300 mm between the end screws, service 0 → 40 °C, assembled at 20 °C
(ΔT = ±20 K, range 40 K):

```text
PETG on aluminium   (65 − 23)e-6 · 300 · 40 = 0.50 mm total relative movement
PLA on aluminium    (96 − 23)e-6 · 300 · 40 = 0.88 mm
PLA on steel, restrained, ΔT = 40 K:
                    σ ≈ (96 − 12)e-6 · 3427 MPa · 40 = 11.5 MPa
```

11.5 MPa is sustained stress in the plastic. 10 MPa ruptured PLA at 60 °C in
3 hours ([[creep-and-stress-relaxation#design-rules]]). Restrained, the part
either creeps, bows or cracks at a screw hole. Hot, it buckles; cold, it pulls
in tension (Covestro).

## Let long parts float

- **One fixed point, the rest slotted.** Fix one hole (the datum) and slot
  every other hole along the line to it. Slot length for hole i at distance
  `L_i` from the fixed hole:
  `slot_i = d_clear + |α_p − α_m| · L_i · ΔT_range` (plus the printed
  hole's own tolerance).
- Put the fixed hole where position matters most, usually mid-span so the
  movement splits both ways.
- The slot can be in either part, as long as relative movement is allowed
  (Covestro).
- **Do not clamp the slot.** "If the fasteners are too tight, the effect of
  the slotted holes will be negated" (Covestro). Use a shoulder screw or a
  metal spacer sleeve that the screw bottoms on, with a washer over the slot,
  so the head sets the gap and not friction. The sleeve also stops preload loss
  in the plastic ([[creep-and-stress-relaxation#design-rules]]).
- Sliding fits along a rail need the same allowance: a printed carriage on a
  metal rod changes its bore clearance by Δc above
  ([[linear-guides-and-slides#clearance-and-preload-in-printed-slides]]).
- Tabs and hooks that engage metal at both ends need the relative movement in
  their engagement length.

## Metal pressed into plastic

- Heating loosens a metal part pressed into plastic; cooling tightens it and
  raises hoop stress. Each hot excursion relaxes the interference by creep,
  so the fit loses grip cycle by cycle. For a joint that must stay tight,
  add a mechanical lock (flat, key, pin, screw) rather than friction alone
  ([[creep-and-stress-relaxation#design-rules]]).
- Covestro calls moulded-in metal inserts a high-residual-stress joint that
  can craze and crack some plastics (it names PC and PC blends), and prefers
  inserts installed by heat or ultrasound, which lack the high stresses of
  press fits. Printed parts: [[heat-set-inserts]].
- Glass- or carbon-filled plastics have CTEs closer to metal, so inserts
  suffer less (Covestro). This holds only along the fibres of a print.
- Keep boss walls thick enough for the cold-end hoop strain, not only the
  assembly strain. Check `(interference + Δc_cold) / d` against the
  material's permissible strain ([[snap-fit-design#permissible-strain]]).

## Gluing plastic to metal

- A rigid, thin bondline takes the whole mismatch as shear. A simple
  estimate (derived, not sourced) of the adhesive shear strain at the end of
  a bond of length L and thickness h:
  `γ ≈ |α_p − α_m| · ΔT · (L/2) / h`. PLA on aluminium, L = 100 mm,
  h = 0.3 mm, ΔT = 40 K gives γ ≈ 0.49: far beyond a rigid epoxy.
- Permabond: use a glue line of 0.25–0.3 mm (wire or glass-bead spacers hold
  it), a toughened or flexible adhesive, and cure at the temperature the
  assembly runs at so the joint is stress-free there. Model the gap into the
  joint: a bonded seat is a clearance of 2 × bondline on diameter, not a
  press fit.
- Long bonds between plastic and metal: bond short patches, or bond one end
  and let the rest float in a slot. Bond chemistry per material is in
  [[adhesives-and-solvent-welding]].

## Checks

```python
alpha = {"PLA": 96e-6, "PETG": 65e-6, "ABS": 90e-6, "ASA": 88e-6, "PC": 66e-6,
         "steel": 12e-6, "aluminium": 23e-6, "brass": 18e-6}
T_assembly, T_min, T_max = 20.0, 0.0, 40.0

# long plastic part on metal: the slot must absorb the relative movement
L_i, d_clear, slot_len = 150.0, 3.4, 4.2           # mm, hole i from the fixed hole
dL = abs(alpha["PETG"] - alpha["aluminium"]) * L_i * (T_max - T_min)
assert slot_len - d_clear >= dL, f"slot too short: needs {dL:.2f} mm of travel"

# restrained plastic stays below a sustained-stress limit (see creep page)
E_p, sigma_sustained_max = 3427.0, 5.0              # MPa; PLA modulus, chosen limit
restrained = False                                  # True only if no hole is slotted
sigma = abs(alpha["PLA"] - alpha["steel"]) * E_p * max(T_max - T_assembly, T_assembly - T_min)
assert not restrained or sigma <= sigma_sustained_max, f"restrained part at {sigma:.1f} MPa: slot it"

# metal pin pressed into plastic: cold end must not exceed permissible strain
d, interference, eps_allow = 5.0, 0.10, 0.03
dc_cold = (alpha["PLA"] - alpha["steel"]) * d * (T_assembly - T_min)
assert (interference + dc_cold) / d <= eps_allow, "bore cracks at the cold end"

# bonded plastic-metal joint: bondline modelled as a gap, in the recommended band
bondline = 0.3
assert 0.25 <= bondline <= 0.3
```
