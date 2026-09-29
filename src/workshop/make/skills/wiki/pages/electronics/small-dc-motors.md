---
title: Small DC motors and gearmotors
tags: [motor, dc-motor, gearmotor, tt-motor, n20, stall-current, noise, 130-motor]
aliases: [toy motor, hobby motor, micro metal gearmotor, yellow gearmotor, brushed motor, motor noise]
sources:
  - https://www.adafruit.com/product/711
  - https://www.adafruit.com/product/3777
  - https://www.pololu.com/category/60/micro-metal-gearmotors
  - https://www.pololu.com/product/1089
  - https://www.pololu.com/docs/0J15/9
related: [energy-drive, motor-drivers-and-flyback, power-path-design, gears, shafts-and-bearings, noise-and-vibration]
updated: 2026-09-23
---

# Small DC motors and gearmotors

A brushed DC motor spins fast with little torque; every toy use needs a
reduction ([[energy-drive#ratio-budget]], [[gears]]). The number that sizes
the battery, the driver and the wires is the **stall current**, not the
running current: a motor draws it at every start and whenever the mechanism
jams.

## Three common families

Vendor figures; the same name covers many makers with different numbers, so
take the chosen part's own datasheet and its STEP (`$step-parts`) for the
seat.

| family | size | voltage | speed | current | notes |
|---|---|---|---|---|---|
| **130-size motor** (Adafruit 711) | body 27.5 × 20 × 15 mm, shaft 8 mm × Ø2 mm | 6 V rated, 4.5–9 V, starts at 2 V | 9,100 ± 1,800 rpm no load, 4,500 ± 1,500 loaded | 70 mA no load, 250 mA loaded, **500 mA stall** max | 20 g·cm start torque, 10 g·cm rated; 17.5 g |
| **TT gearmotor** (Adafruit 3777) | 70 × 22 × 18 mm, dual output axle | 3–6 V | 90–250 rpm | 150 mA no load, **1.1–1.5 A stall** | 1:48 plastic gearbox, 0.4 kg·cm (3 V) to 0.8 kg·cm (6 V) stall torque; 30.6 g |
| **micro metal gearmotor** (Pololu "N20"-size) | gearbox 10 × 12 mm section, D-shaft Ø3 × 9 mm | 6 V (LP, MP, HP, HPCB), 12 V (HPCB) | ratio 5:1 to 1000:1 | stall 6 V: LP 0.36 A, MP 0.67 A, HP 1.6 A, HPCB 1.5 A; 12 V HPCB 0.75 A | 1000:1 gearbox is 3.5 mm longer; brackets fit the 10 × 12 × 26 mm gearhead class |

## Sizing rules

- **Driver and supply sized to stall**, with margin: a TT motor at 1.1–1.5 A
  stall is beyond a microcontroller pin and at the edge of small drivers
  ([[motor-drivers-and-flyback]]).
- **Speed follows voltage, torque follows current.** A motor run below its
  rated voltage is slower and weaker. Batteries sag, so check the empty
  voltage ([[battery-cells-and-packs]]).
- **Never drive a motor from a GPIO pin.** Use a driver or a transistor
  with a flyback diode.
- **Wire gauge from stall current** ([[wire-gauge-and-connectors]]).
- Pick the ratio from the output speed the mechanism wants; the gearmotor
  ratio plus any printed stage is the total ([[energy-drive#ratio-budget]]).

## Mechanical integration

- The seat comes from the motor's STEP via `cadmount`. Motor tolerances
  (±1,800 rpm on a 130 motor) show that these are not precision parts.
  Clamp the body; do not rely on a press fit into printed plastic.
- A D-shaft output keys a printed hub one way round
  ([[joints#keyed-joints]]). The TT motor's plastic dual axle is molded, and a
  printed wheel hub must match its flats from the STEP.
- Motor vibration loosens friction fits. Screw brackets, or capture the
  motor with a strap and a screw.
- Leave space and a path for the leads and suppression capacitors at the
  terminal end.

Isolating the motor from the shell, and PWM whine: [[noise-and-vibration]].

## Electrical noise

Brushed motors spark at the commutator and inject noise that resets
microcontrollers and upsets sensors. Pololu's remedies:

- one to three **0.1 µF ceramic capacitors** at the motor: across the
  terminals, and optionally from each terminal to the case, as close to the
  casing as possible;
- keep motor and power leads short and **twist the motor leads**;
- route motor wires away from signal lines;
- bulk electrolytic decoupling of at least several hundred µF near sensitive
  electronics, rated at least twice the supply voltage (non-polarised
  capacitors where a capacitor sees reversing voltage).

Leave room in the CAD for the capacitors on the motor tabs and for the
twisted pair to run away from the signal wiring.
