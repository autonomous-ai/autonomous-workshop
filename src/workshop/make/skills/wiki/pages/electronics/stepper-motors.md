---
title: Stepper motors for small machines
tags: [stepper, 28byj-48, nema-17, uln2003, step-angle, holding-torque, driver]
aliases: [stepper motor, geared stepper, nema17, bipolar stepper, unipolar stepper]
sources:
  - https://www.adafruit.com/product/858
  - https://lastminuteengineers.com/28byj48-stepper-motor-arduino-tutorial/
  - https://www.pololu.com/product/1200
  - https://reprap.org/wiki/NEMA_17_Stepper_motor
  - https://eu.aspina-group.com/en/learning-zone/columns/what-is/034/
related: [motor-drivers-and-flyback, small-dc-motors, energy-drive, shafts-and-bearings, noise-and-vibration]
updated: 2026-09-23
---

# Stepper motors for small machines

A stepper moves in fixed steps without feedback. It is right for positioning
that must repeat (a dial, a turntable index, a slow drive), and wrong where
speed or efficiency matter. It draws current while standing still to hold
position.

## 28BYJ-48 (geared 5 V unipolar)

- 28 mm diameter, 20 mm tall body, excluding a 9 mm long, Ø5 mm shaft with
  two flats (Adafruit). Built-in mounting plate with two holes; 37 g;
  9-inch cable with a 5-pin connector.
- 5 V, about 42 Ω per winding (Adafruit). Lastminuteengineers quotes 240 mA
  typical operating current.
- **Two gear ratios are sold under one name.** The common one is ~64:1
  (2,048 full steps per output turn, stride 5.625°/64). Adafruit's variant
  is ~1/16 (about 512 steps per turn). Count the steps before trusting a
  kinematic formula, and record the ratio as `[measured]`.
- Slow: about 15 rpm with the 64:1 box (lastminuteengineers); Adafruit
  recommends under 6 rpm at 5 V (about 12 rpm overdriven at 9 V). Holding
  torque about 150 gf·cm on Adafruit's variant.
- Usually driven by a ULN2003 board: Darlington pairs rated 500 mA / 50 V
  with built-in flyback diodes, four coil LEDs, and an on/off jumper. Power
  the motor from a separate 5 V, not from the microcontroller board.

## NEMA 17 (bipolar)

"NEMA 17" fixes the mounting face, not the performance (ASPINA, from NEMA
ICS 16-2001):

| dimension | value |
|---|---|
| square flange | 1.7 in, ~42 mm (43.18 mm per RepRap; 42.3 mm for Pololu #1200) |
| mounting holes | 31 mm square pattern, M3 (hole Ø 0.150 ± 0.010 in in the standard) |
| pilot (boss) diameter | 0.8661 in (22 mm) nominal, 0.03–0.09 in deep |
| shaft | 0.1969 in (5 mm) nominal, often with a flat |

Length, torque and winding vary. A typical 3D-printer-class motor is about
1.5–1.8 A per phase with ≥ 44 N·cm holding torque, 1.8° per step (200
steps/turn) or 0.9° (RepRap). A smaller example is Pololu #1200:
42.3 × 48 mm, 1.2 A per coil, 3.3 Ω, 3.2 kg·cm (44 oz·in), 5 mm D-shaft.

Needs a bipolar current-limiting driver (for example A4988/DRV8825/TMC class
boards) set to the motor's rated current. An H-bridge without current
limiting overheats it ([[motor-drivers-and-flyback]]).

## Design notes

- **The pilot locates the motor**, the screws only clamp it. Cut a pilot
  recess (clearance from `cadfits`) and take the bolt pattern from the
  motor's STEP.
- Steppers run warm while holding. Keep PLA mounts away from the motor body
  or allow airflow, and do not press a printed part onto a hot case.
- Losing steps is silent. A mechanism that must know its position needs a
  home switch ([[switches-and-reed-sensors]]).
- Couple the shaft with a set screw on the flat, or a keyed printed hub
  ([[shafts-and-bearings#getting-torque-on-and-off]]).

Stepper dampers and soft mounts: [[noise-and-vibration]].
