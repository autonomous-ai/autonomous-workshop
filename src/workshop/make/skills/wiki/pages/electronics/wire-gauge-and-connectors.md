---
title: Wire gauge and small connectors
tags: [wire, awg, gauge, ampacity, connector, jst, dupont, pitch, wiring]
aliases: [wire size, cable gauge, jst ph, jst xh, jst sh, qwiic, stemma qt, header pitch, bec connector]
sources:
  - https://en.wikipedia.org/wiki/American_wire_gauge
  - https://en.wikipedia.org/wiki/JST_connector
  - https://www.adafruit.com/product/1578
  - https://www.adafruit.com/product/3777
related: [power-path-design, lipo-cells-and-housing, small-dc-motors, electronics-enclosure-design]
updated: 2026-09-23
---

# Wire gauge and small connectors

Wires and connectors are the part of the power path that gets forgotten
until it gets warm. Size them from the worst-case current (a motor's stall,
a pixel strip at full white), then give them a route in the model
([[power-path-design]]).

## AWG table (copper)

From the Wikipedia AWG table. Ampacity is for enclosed wire at 30 °C ambient,
60 °C-rated insulation, a conservative building-wire figure. Short,
ventilated chassis runs carry more, but these numbers are a safe planning
floor.

| AWG | diameter | area | resistance | ampacity (60 °C) |
|---|---|---|---|---|
| 18 | 1.024 mm | 0.823 mm² | 20.95 mΩ/m | 10 A |
| 20 | 0.812 mm | 0.518 mm² | 33.31 mΩ/m | 5 A |
| 22 | 0.644 mm | 0.326 mm² | 52.96 mΩ/m | 3 A |
| 24 | 0.511 mm | 0.205 mm² | 84.22 mΩ/m | 2.1 A |
| 26 | 0.405 mm | 0.129 mm² | 133.9 mΩ/m | 1.3 A |
| 28 | 0.321 mm | 0.0810 mm² | 212.9 mΩ/m | 0.83 A |
| 30 | 0.255 mm | 0.0509 mm² | 338.6 mΩ/m | 0.52 A |

The voltage drop matters as much as heat at low voltages:

```python
V_DROP = I_MAX * R_PER_M * LENGTH_M * 2      # out and back
assert V_DROP <= 0.05 * V_SUPPLY, "wire drops more than 5 % of the supply"
```

Example: a TT gearmotor ships on 28 AWG leads (Adafruit). At its 1.1–1.5 A
stall, that is beyond the 0.83 A conservative figure. Fine for short
intermittent stalls, but a harness carrying several motors should step up to
22–24 AWG.

## JST connector families

From the Wikipedia JST article:

| series | pitch | rating | typical use |
|---|---|---|---|
| SH | 1.00 mm | 1 A | small sensor boards (compatible with SR/SZ IDC) |
| GH | 1.25 mm | 1 A | often confused with Molex PicoBlade |
| ZH | 1.50 mm | 1 A | small boards (compatible with ZR/ZM) |
| **PH** | 2.00 mm | 2 A | small LiPo cells, many stepper motors |
| **XH** | 2.50 mm | 3 A | R/C battery balance leads, general purpose |
| EH | 2.50 mm | 3 A | general purpose |
| RCY ("BEC") | 2.50 mm | 3 A | small models, toys, small LiPo packs |
| SM | 2.50 mm | 3 A | LED lighting, appliances |
| VH | 3.96 mm | 10 A | higher-current power |

- **JST-PH polarity is not standardised across battery vendors.** Adafruit's
  cells match Adafruit boards, and other brands may be reversed, which
  destroys the battery or the board ([[lipo-cells-and-housing]]).
- "JST" alone does not name a connector. Write the series and pin count
  (for example JST-PH 2-pin) in the spec.
- 2.54 mm (0.1 in) is the pitch of Dupont jumper housings, pin headers and
  breadboards. Dupont jumpers are for prototypes: they work loose under
  vibration. A toy that moves needs latching connectors or soldered joints.

## Giving wires a place in the model

- **Route every wire as a solid** with a bend radius, through a channel or
  clips, never pinched by a lid seam or a moving part
  ([[power-path-design#wires-are-solids]]).
- A wire crossing a moving joint needs a service loop and a path that the
  motion sweep can see.
- Strain-relieve every cable that leaves the housing or can be pulled
  (a printed clamp or a knot behind a wall), so the pull lands on plastic, not
  on a solder joint ([[electronics-enclosure-design#strain-relief]]).
- Leave finger room to mate and unmate a connector, and room for the housing
  behind it: a JST-XH plug is taller than the header it sits on.
