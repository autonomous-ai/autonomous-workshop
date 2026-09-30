---
title: Motor drivers and flyback protection
tags: [motor-driver, h-bridge, l298n, drv8833, tb6612, uln2003, flyback, diode, inductive-load]
aliases: [h bridge, dual motor driver, back emf, freewheel diode, snubber, darlington driver]
sources:
  - https://www.pololu.com/product/2130
  - https://www.pololu.com/product/2135
  - https://www.pololu.com/product/713
  - https://lastminuteengineers.com/l298n-dc-stepper-driver-arduino-tutorial/
  - https://www.rugged-circuits.com/the-motor-driver-myth
  - https://lastminuteengineers.com/28byj48-stepper-motor-arduino-tutorial/
  - https://en.wikipedia.org/wiki/Flyback_diode
related: [small-dc-motors, stepper-motors, power-path-design, battery-cells-and-packs, logic-level-interfacing, thermal-design-for-enclosures, fluid-fittings-and-pneumatics]
updated: 2026-09-23
---

# Motor drivers and flyback protection

A microcontroller pin supplies milliamps. A motor wants amps and has to be
reversed. A driver sits between them: an H-bridge for direction and speed,
a transistor array for one-way loads. Every inductive load (motor, relay,
solenoid) also needs a path for the current it keeps pushing when switched
off.

## Choosing an H-bridge

| driver | motor supply | current per channel | notes |
|---|---|---|---|
| **DRV8833** (Pololu carrier) | 2.7–10.8 V | 1.2 A continuous, 2 A peak | two channels; 3 V and 5 V logic; reverse-voltage, under-voltage, over-current and over-temperature protection; optional current limiting; 0.7 × 0.4 in, fits a breadboard. Thermal testing held ~1.2–1.3 A before shutdown, below the chip datasheet's 1.5 A |
| **TB6612FNG** (Pololu carrier) | 4.5–13.5 V recommended (runs down to 2.5 V with reduced performance) | 1 A continuous, 3 A peak (channels can be paralleled for 2 A) | logic 2.7–5.5 V; reverse-power protection on the motor supply only (none on Vcc); thermal shutdown; PWM to 100 kHz |
| **L298N** (module) | 5–46 V chip range (module regulator ≤ 12 V) | 2 A per channel | bipolar transistors: about 2 V drop at typical current, and more as current rises (up to ~5 V at 2 A); onboard 78M05 5 V regulator, enabled by jumper, supplies up to 0.5 A only when the input is ≤ 12 V |

**The L298N's drop is the trap.** At 12 V in, the motor sees about 10 V
(lastminuteengineers). A 6 V toy motor on a 4 × AA pack through an L298N gets
about 4 V, and the difference turns into heat on the board: 2 A through
~3.7 V of drop is ~7.4 W (Rugged Circuits). For battery toys prefer a MOSFET
driver (DRV8833, TB6612).

```python
V_MOTOR = V_BATTERY_EMPTY - DRIVER_DROP
assert DRIVER_CONT_A >= MOTOR_RUNNING_A and DRIVER_PEAK_A >= MOTOR_STALL_A, \
    "driver must survive the motor's stall current"
```

Stall currents to check against: 130 motor 0.5 A, TT gearmotor 1.1–1.5 A,
micro metal HP 1.6 A ([[small-dc-motors]]). A TT motor stalling on a DRV8833
is at its peak rating.

Driver dissipation and junction temperature:
[[thermal-design-for-enclosures]].

## One-direction loads: transistor arrays

The ULN2003 (seven Darlington pairs, 500 mA / 50 V each, built-in flyback
diodes) switches one side of a load. It is the usual driver for a 28BYJ-48
stepper, relays, solenoids and lamps ([[stepper-motors]]). It cannot reverse
a DC motor.

## Flyback (freewheel) diodes

When current through an inductor is interrupted, the inductor "resists the
drop in current by developing a very large induced voltage" of the opposite
polarity. That spike destroys the switching transistor or arcs relay
contacts.

- Put a diode **antiparallel** across the coil: reverse-biased in normal
  operation, it conducts when the switch opens and clamps the coil voltage to
  about the diode's forward drop (0.7–1.5 V).
- The cost is slower release: a relay drops out later while the current
  circulates through the diode. A resistor or Zener in series with the diode
  speeds release at the price of a higher spike.
- H-bridge driver ICs and the ULN2003 include the diodes (or body diodes) for
  their outputs. A bare transistor or MOSFET switching a motor, relay or
  solenoid needs an external one.

Pumps and solenoid valves are inductive loads too:
[[fluid-fittings-and-pneumatics]].

## Wiring rules for the enclosure

- Keep motor supply and logic supply separate where possible, with a common
  ground. A motor starting from the same rail as the microcontroller is the
  classic reset ([[power-path-design]]).
- Put the driver close to the motors; keep motor leads twisted and short
  ([[small-dc-motors#electrical-noise]]).
- Drivers get warm near their continuous rating. Give the board air, and do
  not bury it against PLA ([[electronics-enclosure-design]]).
